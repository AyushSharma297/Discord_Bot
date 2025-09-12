import subprocess
import logging
import time
import re
import ollama
from datetime import datetime
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize the FastAPI app
app = FastAPI(
    title="Ollama API Proxy",
    description="A FastAPI application to interact with Ollama models.",
    version="1.0.0"
)

# Define a router for organizing API endpoints
api_router = APIRouter()

# Pydantic models for request bodies
class TextQueryRequest(BaseModel):
    system_prompt: str = Field(..., description="The system's role or instructions for the model.")
    user_prompt: str = Field(..., description="The user's query for the model.")

class ImageQueryRequest(BaseModel):
    system_prompt: str = Field(..., description="The system's role or instructions for the model.")
    user_prompt: str = Field(..., description="The user's query about the image.")
    image_base64: str = Field(..., description="The image data encoded in base64 format.")

@app.post("/ollama_query/")
async def ollama_query(request: TextQueryRequest):
    model_name = "llama3.1:latest"
    start_time = time.time()

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': request.system_prompt},
                {'role': 'user', 'content': request.user_prompt}
            ]
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        output = response['message']['content'].strip()
        tokens_generated = response.get('total_duration') # Note: The ollama library doesn't return token count directly

        logging.info(f"response: {output}")
        logging.info(f"Elapsed time: {elapsed_time:.3f} seconds")

        response_data = {
            "response": output,
            "elapsed_time_seconds": elapsed_time,
            "tokens_generated": "N/A", # Or you could use 'total_duration' as a proxy
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": model_name
        }

        return response_data

    except ollama.OllamaException as e:
        logging.error(f"Ollama API error: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama API error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")



@app.post("/ollama_img/")
async def ollama_img(request: ImageQueryRequest):
    """
    Processes an image query using the Ollama `llama3.2-vision` model,
    with a fallback to pull the model if it's not present.
    """
    model_name = "gemma3:4b" #"llama3.2-vision:latest"
    
    # This loop will run a maximum of two times (initial attempt + one retry)
    for attempt in range(2):
        start_time = time.time()
        try:
            # Correctly structure the messages for a multi-turn conversation
            messages = [
                {
                    'role': 'system',
                    'content': request.system_prompt
                },
                {
                    'role': 'user',
                    'content': request.user_prompt,
                    'images': [request.image_base64]
                }
            ]
            
            response = ollama.chat(
                model=model_name,
                messages=messages,
            )

            end_time = time.time()
            elapsed_time = end_time - start_time

            if 'message' not in response or 'content' not in response['message']:
                logging.error(f"Unexpected response format from Ollama: {response}")
                raise HTTPException(status_code=500, detail="Unexpected response format from Ollama.")

            output = response['message']['content'].strip()
            # The ollama library doesn't expose token count directly in chat responses
            tokens_generated = response.get('total_duration', 'N/A')

            logging.info(f"Ollama response: {output}")
            logging.info(f"Elapsed time: {elapsed_time:.3f} seconds")

            response_data = {
                "response": output,
                "elapsed_time_seconds": elapsed_time,
                "tokens_generated": tokens_generated,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "full_response_object": response
            }
            return response_data

        except ollama._types.ResponseError as e:
            # Check for a specific error message indicating the model needs to be pulled.
            if "not found" in str(e) or "no longer compatible" in str(e) and attempt == 0:
                logging.info(f"Ollama model '{model_name}' not found.")
    
            else:
                # If it's a different Ollama error or the second attempt, re-raise it
                logging.error(f"Ollama API error: {e}")
                raise HTTPException(status_code=500, detail=f"Ollama API error: {e}")
                
        except Exception as e:
            # Handle any other unexpected exceptions
            logging.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/health/")
async def health_check():
    """
    A simple health check endpoint.
    """
    return {"status": "ok"}

# Include the router in the main FastAPI app
app.include_router(api_router)
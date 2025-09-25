"""
Main FastAPI application for the LLM API Gateway.

This module sets up a FastAPI server to provide a unified interface for interacting
with local Ollama models and the Groq API. It includes endpoints for text generation,
image analysis, and an intelligent agent that can use tools.
"""

# --- Standard Library Imports ---
import logging
import time
import os
import yaml
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, TypedDict, Annotated, List

# --- Third-party Imports ---
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from groq import Groq
import ollama

# --- LangChain and LangGraph Imports ---
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

# --- Local Application Imports ---
from web_search import answer_query
from rag_call import call_local_api


# --- Environment Variable Loading ---
load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
OLLAMA_MODEL_VISION = os.getenv("OLLAMA_MODEL_VISION", "gemma3:4b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# --- Path Configuration ---
try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SYS_PROMPTS_PATH = os.path.join(base_dir, 'utils', 'sys_prompts.yaml')
except NameError:
    # Fallback to a relative path in the current working directory
    SYS_PROMPTS_PATH = 'utils/sys_prompts.yaml'


# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- System Prompts Management ---
@lru_cache(maxsize=1)
def load_system_prompts() -> Dict[str, Any]:
    """
    Loads system prompts from a YAML file.

    The result is cached using LRU cache to avoid repeated file I/O,
    which is efficient as prompts are unlikely to change during runtime.

    Returns:
        A dictionary containing the loaded system prompts.
        Returns an empty dictionary if the file is not found.
    """
    try:
        with open(SYS_PROMPTS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(
            f"System prompts file not found at {SYS_PROMPTS_PATH}. "
            "Proceeding without pre-defined system prompts."
        )
        return {}


def get_prompt_by_id(prompt_id: str) -> str | None:
    """
    Retrieves a specific system prompt by its unique ID from the loaded data.

    Args:
        prompt_id: The ID of the prompt to retrieve.

    Returns:
        The content of the prompt as a string, or None if the ID is not found.
    """
    prompts_data = load_system_prompts()
    for prompt in prompts_data.get("system_prompts", []):
        if prompt.get("id") == prompt_id:
            return prompt.get("content")
    logger.warning(f"System prompt with ID '{prompt_id}' not found.")
    return None


# --- Agent State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tool_used: str
    result: str

# --- Agent Tools ---
@tool
def web_search_tool(query: str) -> str:
    """Search the web for information about the query."""
    try:
        response = answer_query(query)
        return str(response)
    except Exception as e:
        return f"Web search error: {str(e)}"


@tool
def rag_api_tool(query: str) -> str:
    """Query the local RAG API for information."""
    try:
        response = call_local_api(query)
        if response:
            return str(response)
        else:
            return "Error: No response from RAG API"
    except Exception as e:
        return f"RAG API error: {str(e)}"

# --- LLM and Agent Initialization ---
tools = [web_search_tool, rag_api_tool]

def create_intelligent_agent(use_groq: bool = False):
    """
    Dynamically creates an intelligent agent with the specified LLM.

    Args:
        use_groq: If True, the agent uses the Groq API. Otherwise, it uses
                  a local Ollama model.

    Returns:
        A compiled LangGraph agent ready to process requests.
    """
    system_prompt = get_prompt_by_id("Agent_orch_v1")
    if not system_prompt:
        # Fallback prompt if the YAML file or specific ID is not found
        system_prompt = "You are a helpful assistant that can use tools to answer questions."
    logger.debug(f"Using system prompt: {system_prompt}")
    if use_groq:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        llm = ChatGroq(model=GROQ_MODEL, temperature=0)
        logger.info(f"Creating agent with Groq model: {GROQ_MODEL}")
    else:
        llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
        logger.info(f"Creating agent with Ollama model: {OLLAMA_MODEL}")

    # Create the ReAct agent, which can reason and decide which tool to use
    agent_executor = create_react_agent(llm, tools, prompt= system_prompt)
    return agent_executor


# --- FastAPI Application Setup ---
app = FastAPI(
    title="LLM API Gateway",
    description="A unified API for local Ollama models and the Groq API, with an intelligent agent.",
    version="1.1.0"
)

# Use an API router for better project structure and organization
api_router = APIRouter()


# --- Pydantic Models for Request Bodies ---
class UnifiedTextQueryRequest(BaseModel):
    """Request model for the unified text query endpoint."""
    system_prompt: str = Field(
        ...,
        description="The system's role or instructions for the model.",
        examples=["You are a helpful assistant."]
    )
    user_prompt: str = Field(
        ...,
        description="The user's query for the model.",
        examples=["What is the capital of France?"]
    )
    use_groq: bool = Field(
        False,
        description="If true, use the Groq API instead of the local Ollama model."
    )


class ImageQueryRequest(BaseModel):
    """Request model for the image analysis endpoint."""
    system_prompt: str = Field(
        ...,
        description="Instructions for how the model should interpret the image.",
        examples=["Describe this image in detail."]
    )
    user_prompt: str = Field(
        ...,
        description="The user's specific question about the image.",
        examples=["What is the main subject of this picture?"]
    )
    image_base64: str = Field(
        ...,
        description="The image data encoded in base64 format."
    )


class AgentQueryRequest(BaseModel):
    """Request model for the intelligent agent endpoint."""
    query: str = Field(
        ...,
        description="The query to be processed by the agent.",
        examples=["What is the latest news about AI?"]
    )
    use_groq: bool = Field(
        False,
        description="If true, the agent uses Groq for its reasoning process."
    )


# --- API Endpoints ---

@api_router.post("/query/", summary="Unified Text Generation")
async def unified_query(request: UnifiedTextQueryRequest):
    """
    Processes a text generation request using either Ollama or Groq.
    This endpoint is ideal for straightforward prompt-response interactions.
    """
    start_time = time.time()
    try:
        if request.use_groq:
            # Use the Groq API for faster inference
            if not GROQ_API_KEY:
                raise HTTPException(status_code=400, detail="GROQ_API_KEY is not configured.")
            client = Groq(api_key=GROQ_API_KEY)
            chat_completion = client.chat.completions.create(
                messages=[
                    {'role': 'system', 'content': request.system_prompt},
                    {'role': 'user', 'content': request.user_prompt}
                ],
                model=GROQ_MODEL,
            )
            output = chat_completion.choices[0].message.content
            tokens_generated = chat_completion.usage.completion_tokens
            model_name = GROQ_MODEL
        else:
            # Use the local Ollama model
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': request.system_prompt},
                    {'role': 'user', 'content': request.user_prompt}
                ]
            )
            output = response['message']['content'].strip()
            # 'eval_count' is a more accurate token count for Ollama
            tokens_generated = response.get('eval_count', 'N/A')
            model_name = OLLAMA_MODEL

        elapsed_time = time.time() - start_time
        logger.info(
            f"Query processed by {model_name} in {elapsed_time:.3f}s. "
            f"Response: {output[:100]}..."
        )

        return {
            "response": output,
            "model_used": model_name,
            "elapsed_time_seconds": elapsed_time,
            "tokens_generated": tokens_generated,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except ollama.OllamaError as e:
        logger.error(f"Ollama API error: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama API error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in /query/: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/ollama_img/")
async def ollama_img(request: ImageQueryRequest):
    """
    Processes an image query using the Ollama model.
    """
    model_name = OLLAMA_MODEL_VISION
    
    for attempt in range(2):
        start_time = time.time()
        try:
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
            if "not found" in str(e) or "no longer compatible" in str(e) and attempt == 0:
                logging.info(f"Ollama model '{model_name}' not found.")
            else:
                logging.error(f"Ollama API error: {e}")
                raise HTTPException(status_code=500, detail=f"Ollama API error: {e}")
                
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@api_router.post("/agent", summary="Intelligent Agent with Tool Use")
async def agent_endpoint(request: AgentQueryRequest):
    """
    Processes a query using an intelligent agent that can autonomously
    decide to use tools like web search or a RAG API.
    """
    try:
        start_time = time.time()
        # Dynamically create the agent based on the user's choice of LLM
        intelligent_agent = create_intelligent_agent(use_groq=request.use_groq)

        # The input to the agent is a list of messages
        initial_messages = [HumanMessage(content=request.query)]

        # Asynchronously invoke the agent
        result = await intelligent_agent.ainvoke({
            "messages": initial_messages
        })

        # The final response is the last message from the agent
        final_message = result["messages"][-1]

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Log the tool usage for monitoring
        tool_used = "unknown"
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_used = message.tool_calls[0]["name"]
                break

        return {
            "query": request.query,
            "tool_used": tool_used,
            "result": final_message.content,
            "elapsed_time_seconds": elapsed_time,
            "status": "success"
        }

    except ValueError as e:
        # Catch specific configuration errors like missing API keys
        logger.error(f"Configuration error in agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent error for query '{request.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")


@api_router.get("/health/", summary="Health Check")
async def health_check():
    """
    Performs a simple health check of the API.

    It verifies the connection to the Ollama service to ensure the gateway
    is fully operational.
    """
    try:
        # A lightweight check to see if the Ollama service is responsive
        ollama.ps()
        logger.info("Health check successful.")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: Unable to connect to Ollama. Error: {e}")
        # Still return 200 OK but with an unhealthy status,
        # which is common practice for health check endpoints.
        return {"status": "unhealthy", "error": f"Could not connect to Ollama: {e}"}


# Include the router in the main FastAPI app
app.include_router(api_router)


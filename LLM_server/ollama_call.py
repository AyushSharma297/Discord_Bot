from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import logging
import time
import re
from datetime import datetime

app = FastAPI()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class QueryRequest(BaseModel):
    system_prompt: str
    user_prompt: str

@app.post("/ollama_query/")
async def ollama_query(request: QueryRequest):
    model_name = "llama3.1:latest"  # fixed model
    full_query = f"System: {request.system_prompt}\nUser: {request.user_prompt}"
    start_time = time.time()

    try:
        result = subprocess.run(
            ['ollama', 'run', model_name, full_query],
            capture_output=True,
            encoding='utf-8',
            timeout=30
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""

        # Log stdout and stderr
        logging.info(f"Olaama stdout: {stdout}")
        logging.info(f"Olaama stderr: {stderr}")
        logging.info(f"Elapsed time: {elapsed_time:.3f} seconds")

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Olaama CLI error: {stderr}")

        output = stdout
        if not output:
            output = "No response from Olaama model."

        # Combine stdout and stderr to search for tokens info
        combined_output = f"{stdout}\n{stderr}"

        # Look for a pattern like "Tokens generated: 123"
        match = re.search(r'Tokens generated:\s*(\d+)', combined_output)

        # Extract token count or default to "N/A"
        tokens_generated = int(match.group(1)) if match else "N/A"

        response_data = {
            "response": output,
            "elapsed_time_seconds": elapsed_time,
            "tokens_generated": tokens_generated,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        logging.info(f"Response data: {response_data}")

        return response_data

    except subprocess.TimeoutExpired:
        logging.error("Olaama CLI timed out")
        raise HTTPException(status_code=504, detail="Olaama CLI timed out")
    except Exception as e:
        logging.error(f"Olaama CLI failed: {e}")
        raise HTTPException(status_code=500, detail=f"Olaama CLI failed: {e}")

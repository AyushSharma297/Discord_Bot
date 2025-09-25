<h1 align="center">🚀 LLM API Gateway </h1>

<div align="center">

![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green?style=for-the-badge&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLMs-orange?style=for-the-badge&logo=ollama&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-ultrafast-critical?style=for-the-badge&logo=groq&logoColor=white)
![LightRAG](https://img.shields.io/badge/LightRAG-GraphRAG-lightblue?style=for-the-badge&logo=neo4j&logoColor=white)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/status-active-success?style=for-the-badge)
![Version](https://img.shields.io/badge/version-1.1.0-informational?style=for-the-badge)

### 🎯 **High-performance, async API gateway for seamless LLM integration**

*Unified interface for multiple LLM providers with built-in GraphRAG capabilities*

</div>

***

## Overview

**LLM API Gateway** is a versatile, high-performance FastAPI service acting as a central hub for all your language model interactions. It seamlessly switches between local LLMs via Ollama (for privacy) and Groq API (for speed), supports GraphRAG knowledge retrieval, and adds multimodal vision capabilities.

***

## ✨ Features

- **Multi-Provider Support:** Ollama, Groq, and more.
- **Async Performance:** Built on FastAPI for lightning-fast responses.
- **GraphRAG Integration:** Advanced retrieval from LightRAG knowledge graphs.
- **Type Safety:** Full Pydantic model validation.
- **Monitoring Ready:** Integrated logging and metrics.
- **Docker Support:** Container-ready deployment.
- **Dual LLM Routing:** Select Ollama (privacy) or Groq (speed) per task.
- **Intelligent Agent:** LangGraph-powered ReAct agent for web search, private KB RAG, and context-rich answers.
- **Vision Support:** Multimodal endpoint for image captioning and analysis via local Ollama models.
- **Health Check:** `/health/` endpoint for robust monitoring (Kubernetes, Docker Swarm, load balancers).

***

## 📋 Requirements

- Python **3.9+**
- FastAPI
- Ollama (local inference)
- LightRAG (GraphRAG)
- LangGraph
- pip for package management

***

## 🔧 Configuration

Create a `.env` file in your project root:

```env
# --- Ollama ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_VISION="your_model"
OLLAMA_MODEL="your_model"

# --- Groq API Configuration ---
GROQ_API_KEY="your_token"
GROQ_MODEL="your_model"
```

***

## 🏗️ Architecture

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Client Apps  │────│  API Gateway  │────│  LLM Providers│
└───────────────┘    └───────────────┘    └───────────────┘
                          │
                   ┌───────────────┐
                   │   LightRAG    │
                   │ KnowledgeGraph│
                   └───────────────┘
```

***

## 📈 Performance

- **Response Time:** <100ms (excluding LLM inference)
- **Throughput:** 1000+ requests/sec
- **Concurrency:** End-to-end async/await
- **Memory:** Minimized footprint

***

## 📦 Project Setup

### 1. Prerequisites

- Python 3.9+
- pip
- Local Ollama instance running ([Install Ollama](https://ollama.ai/); pull required models, e.g. `ollama pull llama3`)
- Install [Install LightRAG](https://github.com/HKUDS/LightRAG) local RAG API service for private KB queries (version used `lightrag-hku 1.4.8.2`) 

### 2. Install Dependencies

Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # (Linux & macOS)
# venv\Scripts\activate    # (Windows)

pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in your project root:
```env
# --- Ollama Configuration ---
OLLAMA_MODEL="llama3"
OLLAMA_MODEL_VISION="llava"
# --- Groq API Configuration ---
GROQ_API_KEY="YOUR_GROQ_API_KEY"
GROQ_MODEL="llama3-8b-8192"
```

### 4. Start LightRAG Server

Run in project directory:
```bash
lightrag-server
```

### 5. Run the FastAPI Server

```bash
uvicorn ollama_call:app --reload
```
Accessible at:
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

***

## 📡 API Endpoints

### Core LLM Operations

- `POST /query/`: Direct query
- `POST /ollama_img/`: Image analysis

### GraphRAG Operations

- `POST /v1/rag/query`: RAG-enhanced queries
- `POST /v1/rag/ingest`: Document ingestion
- `GET /v1/rag/status`: System status

### Agent Operations

- `POST /agent`: Intelligent LangGraph agent endpoint

### Monitoring

- `GET /health/`: Health check/status

***

## ⚡ Usage Examples

### Query with Groq

```bash
curl -X POST http://127.0.0.1:8000/query/ \
-H "Content-Type: application/json" \
-d '{
  "system_prompt": "You are a financial analyst.",
  "user_prompt": "What are the key benefits of portfolio diversification?",
  "use_groq": true
}'
```

### Use the Intelligent Agent

```bash
curl -X POST http://127.0.0.1:8000/agent \
-H "Content-Type: application/json" \
-d '{
  "query": "What is the latest news about space exploration?",
  "use_groq": true
}'
```

### Analyze an Image

```bash
curl -X POST http://127.0.0.1:8000/ollama_img/ \
-H "Content-Type: application/json" \
-d '{
  "system_prompt": "You are a helpful assistant that describes images in detail.",
  "user_prompt": "What is in this image?",
  "image_base64": "<BASE64_IMAGE_STRING>"
}'
```

*Tip: Convert images to Base64 in Python using `base64.b64encode()`.*

***

## 🐍 Python Client Example

```python
import requests
import base64
import json

BASE_URL = "http://127.0.0.1:8000"

def query_example():
    url = f"{BASE_URL}/query/"
    payload = {
        "system_prompt": "You are a financial analyst.",
        "user_prompt": "What are the key benefits of portfolio diversification?",
        "use_groq": True
    }
    response = requests.post(url, json=payload)
    print(json.dumps(response.json(), indent=2))

def agent_example():
    url = f"{BASE_URL}/agent"
    payload = {
        "query": "What is the latest news about space exploration?", 
        "use_groq": True
    }
    response = requests.post(url, json=payload)
    print(json.dumps(response.json(), indent=2))

def image_analysis_example(image_path="path/to/your/image.jpg"):
    with open(image_path, "rb") as f:
        base64_img = base64.b64encode(f.read()).decode("utf-8")
        url = f"{BASE_URL}/ollama_img/"
        payload = {
            "system_prompt": "You are a helpful assistant that describes images in detail.",
            "user_prompt": "What is in this image?",
            "image_base64": base64_img
        }
        response = requests.post(url, json=payload)
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    query_example()
    agent_example()
    # image_analysis_example("path/to/your/image.jpg")
```

***

## 🛠 Health Check

```bash
curl http://127.0.0.1:8000/health/
```

***

## 📜 License

This project is licensed under the **MIT License**.

***

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [LightRAG](https://github.com/HKUDS/LightRAG) - GraphRAG implementation
- [Groq](https://groq.com/) - Ultra-fast LLM inference
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agentic reasoning engine

***

<div align="center">

**⭐ Star this repo if you find it helpful! ⭐**

Made with ❤️ by the Ayush Sharma

</div>
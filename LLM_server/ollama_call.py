import logging
import time
import ollama
from datetime import datetime
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, TypedDict, Annotated, List
from typing_extensions import TypedDict

# Correct LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# Import your custom modules
from web_search import answer_query
from rag_call import call_local_api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define agent state
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tool_used: str
    result: str

# Define tools using the @tool decorator
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

# Initialize Ollama model
llm = ChatOllama(
    model="llama3.1:latest",
    temperature=0,
    base_url="http://localhost:11434"
)

# Create tools list
tools = [web_search_tool, rag_api_tool]

# Create the agent using prebuilt ReAct agent
def create_intelligent_agent():
    """Create an agent that can decide which tool to use based on the query."""
    
    # Custom prompt that helps the agent decide which tool to use
    system_prompt = """<system_prompt>
<role>
You are an intelligent query router responsible for analyzing incoming user requests and selecting the most appropriate tool for execution within an enterprise agent workflow system.
</role>

<core_objective>
Analyze the nature and requirements of each user query to determine the optimal tool selection strategy, ensuring accurate and efficient query resolution.
</core_objective>

<tool_selection_matrix>
<tool name="web_search_tool">
  <selection_criteria>
    • Real-time or time-sensitive information requests
    • Current events, breaking news, or live data queries
    • Questions requiring the most recent factual updates
    • Temporal queries (current date, time, weather conditions)
    • Executive or organizational changes ("Who is the current CEO?")
    • Market data, stock prices, or financial updates
    • Social media trends or viral content
  </selection_criteria>
  <examples>
    - "What's the latest news about [topic]?"
    - "Current weather in [location]"
    - "Who is the CEO of [company] as of 2025?"
    - "Today's date and time"
    - "Recent developments in [field]"
  </examples>
</tool>

<tool name="rag_api_tool">
  <selection_criteria>
    • Queries requiring specialized domain knowledge from internal documents
    • Information retrieval from proprietary or confidential sources
    • Company policies, procedures, or internal documentation
    • Technical specifications or product documentation
    • Historical data analysis from stored repositories
    • Compliance or regulatory information from internal sources
  </selection_criteria>
  <examples>
    - "Summarize our internal policy on [topic]"
    - "Extract information from project documentation"
    - "Company-specific procedures for [process]"
    - "Technical specifications from our knowledge base"
    - "Historical project data analysis"
  </examples>
</tool>
</tool_selection_matrix>

<routing_logic>
<primary_decision_factors>
1. Information freshness requirements (recent vs. historical)
2. Data source dependency (external vs. internal)
3. Query temporality (time-bound vs. time-independent)
4. Knowledge domain specificity (general vs. specialized)
</primary_decision_factors>

<escalation_rules>
• If query requirements are ambiguous, default to web_search_tool for broader coverage
• For hybrid queries requiring both tools, prioritize based on primary information need
• When internal knowledge is sufficient and current, respond directly without tool invocation
</escalation_rules>
</routing_logic>

<output_format>
<tool_required>
Invoke the selected tool with appropriate parameters based on query analysis.
</tool_required>

<direct_response>
When internal knowledge base contains sufficient and current information, provide direct response without external tool invocation.
</direct_response>
</output_format>

<quality_assurance>
• Ensure tool selection aligns with query intent and information requirements
• Validate that selected approach minimizes latency while maximizing accuracy
• Maintain consistency in routing decisions for similar query patterns
• Prioritize user experience through efficient query resolution
</quality_assurance>
</system_prompt>

"""
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    
    return agent

# Initialize the agent globally
intelligent_agent = create_intelligent_agent()

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

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to be processed by the agent.")

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
        tokens_generated = response.get('total_duration')

        logging.info(f"response: {output}")
        logging.info(f"Elapsed time: {elapsed_time:.3f} seconds")

        response_data = {
            "response": output,
            "elapsed_time_seconds": elapsed_time,
            "tokens_generated": "N/A",
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
    Processes an image query using the Ollama model.
    """
    model_name = "llama3.2-vision:latest"
    
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

@app.post("/agent")
async def agent_endpoint(request: QueryRequest) -> Dict[str, Any]:
    """
    Main agent endpoint that processes queries using LangGraph and Ollama.
    The agent will automatically choose between web search and RAG API based on the query.
    """
    query = request.query
    
    try:
        # Create initial message
        initial_messages = [HumanMessage(content=query)]
        
        # Invoke the agent
        result = await intelligent_agent.ainvoke({
            "messages": initial_messages
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        
        # Determine which tool was used by analyzing the messages
        tool_used = "unknown"
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_used = message.tool_calls[0]["name"]
                break
        
        return {
            "query": query,
            "tool_used": tool_used,
            "result": final_message.content,
            "message_count": len(result["messages"]),
            "status": "success"
        }
        
    except Exception as e:
        logging.error(f"Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

# Alternative simple agent endpoint without tool detection
@app.post("/simple-agent")
async def simple_agent_endpoint(request: QueryRequest) -> Dict[str, Any]:
    """
    Simplified agent endpoint that uses a basic decision logic.
    """
    query = request.query
    
    try:
        # Simple decision logic (like your original DecisionModel)
        if any(keyword in query.lower() for keyword in ["search", "fact", "who", "what", "where", "when", "news", "current"]):
            # Use web search
            result = web_search_tool.invoke(query)
            tool_used = "web_search"
        else:
            # Use RAG API
            result = rag_api_tool.invoke(query)
            tool_used = "rag_api"
        
        return {
            "query": query,
            "tool_used": tool_used,
            "result": result,
            "status": "success"
        }
        
    except Exception as e:
        logging.error(f"Simple agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simple agent error: {str(e)}")

@app.get("/health/")
async def health_check():
    """
    A simple health check endpoint.
    """
    try:
        # Test Ollama connection
        test_response = await llm.ainvoke("Say 'OK'")
        return {
            "status": "healthy",
            "ollama_connection": "active",
            "model": "llama3.1:latest",
            "agent_status": "ready"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }


app.include_router(api_router)



import requests

def call_local_api(query: str, mode: str = "hybrid") -> dict | None:
    url = "http://localhost:9621/query"
    payload = {
        "query": query,
        "mode": mode,
        "only_need_context": True,
        "only_need_prompt": True,
        "response_type": "string",
        "top_k": 40,
        "chunk_top_k": 20,
        "max_entity_tokens": 6000,
        "max_relation_tokens": 8000,
        "max_total_tokens":30000,
        "history_turns": 0,
        "enable_rerank": True
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # raise exception for HTTP errors
        return response.json()  # assuming API returns JSON response
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return None
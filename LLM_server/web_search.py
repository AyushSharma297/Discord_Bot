
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Any
from ddgs import DDGS

def get_search_links(query: str, max_results: int = 5, safe_search: bool = True) -> list[str]:
    """
    Perform a DuckDuckGo search for the given query and return top result URLs.

    Args:
        query       (str):  The search query.
        max_results (int):  Maximum number of URLs to return.
        safe_search (bool): If True, enable safe search filtering.

    Returns:
        list[str]: A list of result URLs.
    """
    links = []
    safesetting = "Moderate" if safe_search else "Off"
    with DDGS() as ddgs:
        for result in ddgs.text(query, safesearch=safesetting, timelimit="y"):
            href = result.get("href")
            if href:
                links.append(href)
            if len(links) >= max_results:
                break
    return links

def fetch_page_text(url: str, timeout: int = 10) -> str:
    """
    Download a webpage and extract visible paragraph text.

    Args:
        url     (str): The page URL to fetch.
        timeout (int): Request timeout in seconds.

    Returns:
        str: Concatenated text of all paragraphs on the page.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text(strip=True) for p in paragraphs)

def summarize_text(text: str, question: str, max_sentences: int = 10) -> list[str]:
    """
    Extract the most relevant sentences from text based on overlap with question words.

    Args:
        text          (str):   The source text to summarize.
        question      (str):   The user’s original question.
        max_sentences (int):   Maximum number of sentences to return.

    Returns:
        list[str]: Top relevant sentences.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    question_words = set(re.findall(r'\w+', question.lower()))
    scored = []
    for s in sentences:
        words = set(re.findall(r'\w+', s.lower()))
        score = len(words & question_words)
        if score > 0 and len(s) > 40:
            scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_sentences]]

def answer_query(query: str) -> dict:
    """
    Orchestrate search, fetch, and summarization to answer a user’s query.
    Returns summaries paired with each URL (one sentence per URL).

    Args:
        query (str): The question or search query.

    Returns:
        dict: {
            "query": str,
            "results": list of dicts [{ "url": str, "summary": str }, ...]
        }
    """
    urls = get_search_links(query, max_results=5, safe_search=True)

    combined_text = ""
    for url in urls:
        combined_text += fetch_page_text(url) + " "
        time.sleep(1)  # polite delay between requests

    summary_sentences = summarize_text(combined_text, query, max_sentences=len(urls))

    # Pair URLs with summary sentences; if fewer summaries, use empty string for remainder
    results = []
    for i, url in enumerate(urls):
        summary = summary_sentences[i] if i < len(summary_sentences) else ""
        results.append({
            "url": url,
            "summary": summary
        })

    return {
        "query": query,
        "results": results
    }

from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient
from typing import Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


load_dotenv()
tavily_client = TavilyClient()

@tool
def search_web(query: str) -> Dict[str, Any] :
    """tool for Search the web for frish information."""
    logging.info(f"search for: {query}")
    print(f"Search the web fro: {query}")
    return tavily_client.search(query)
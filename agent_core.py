"""Shared FastEat AI agent core.

Single source of truth for creating and invoking the LangChain chef agent.
Used by both the CLI (main.py) and the FastAPI backend (backend/main.py).
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from photo_decoder import build_image_message
from prompt import CHEF_PROMPT, SYSTEM_CHEF_PROMPT
from tool import search_web

load_dotenv()

logger = logging.getLogger(__name__)

_agent = None


def create_chef_agent():
    """Create the FastEat AI chef agent using the original configuration."""
    return create_agent(
        model=init_chat_model(
            model="qwen/qwen3.8-27b",
            model_provider="groq",
        ),
        tools=[search_web],
        system_prompt=SYSTEM_CHEF_PROMPT,
    )


def get_agent():
    """Return the shared agent instance, creating it on first use."""
    global _agent
    if _agent is None:
        logger.info("creating our agent...")
        _agent = create_chef_agent()
    return _agent


def generate_recipe(image_path: Path, prompt: str = CHEF_PROMPT) -> str:
    """Run the existing agent against an ingredient photo and return its text."""
    agent = get_agent()
    logger.info("invoking our agent...")
    message = build_image_message(Path(image_path), prompt)
    response = agent.invoke({"messages": [message]})
    return response["messages"][-1].content

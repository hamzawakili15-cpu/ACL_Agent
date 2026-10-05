import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from prompt import SYSTEM_CHEF_PROMPT, CHEF_PROMPT
from tool import search_web
from photo_decoder import choose_image_file, build_image_message
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


load_dotenv()

logging.info("creating our agent...")
agent = create_agent(
    model = init_chat_model(
    model = "qwen/qwen3.8-27b",
    model_provider = "groq",),
    tools = [search_web],
    system_prompt=SYSTEM_CHEF_PROMPT,
)

logging.info("choosing our image...")
path_image = choose_image_file()

logging.info("invoking our agent...")
message = build_image_message(path_image, CHEF_PROMPT)
responce = agent.invoke(
    {
        "messages" : [message],
    }
)

print(responce["messages"][-1].content)



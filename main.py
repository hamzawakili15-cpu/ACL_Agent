import logging

from dotenv import load_dotenv

from agent_core import generate_recipe
from photo_decoder import choose_image_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


load_dotenv()

logging.info("choosing our image...")
path_image = choose_image_file()

response = generate_recipe(path_image)

print(response)

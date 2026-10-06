"""FastEat AI — small FastAPI adapter around the existing LangChain agent."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Union

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load secrets before importing agent modules (tool.py builds its client at import).
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("fasteat.backend")

missing = [key for key in ("GROQ_API_KEY", "TAVILY_API_KEY") if not os.getenv(key)]
if missing:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing)}. "
        "Copy .env_example to .env and fill in your API keys."
    )

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from agent_core import generate_recipe
from backend.recipe_parser import parse_recipe

MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "5"))
MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
DEV_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app = FastAPI(
    title="FastEat AI API",
    description="Turn a photo of your ingredients into a recipe.",
    version="1.0.0",
)

extra_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if "*" in extra_origins:
    allowed_origins = ["*"]
else:
    allowed_origins = list(dict.fromkeys(DEV_ORIGINS + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Ingredient(BaseModel):
    name: str
    amount: str = ""
    unit: str = ""


class RecipeSection(BaseModel):
    heading: str
    body: str


class Recipe(BaseModel):
    title: str = ""
    description: str = ""
    ingredients: List[Ingredient] = []
    instructions: List[str] = []
    prep_time: Union[int, str] = ""
    cook_time: Union[int, str] = ""
    servings: Union[int, str] = ""
    difficulty: str = ""
    tips: List[str] = []
    source_urls: List[str] = []
    sections: List[RecipeSection] = []
    raw_text: str = ""


class GenerateResponse(BaseModel):
    success: bool = True
    recipe: Recipe


def _validate_image(data: bytes, content_type: str, filename: str) -> str:
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Please upload a JPG, PNG or WEBP image.",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image is too large. Maximum size is {MAX_IMAGE_MB} MB.",
        )
    if data.startswith(b"\xff\xd8\xff"):
        sniffed = "image/jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        sniffed = "image/png"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        sniffed = "image/webp"
    else:
        raise HTTPException(
            status_code=415,
            detail="This file does not look like a valid JPG, PNG or WEBP image.",
        )
    if sniffed != content_type:
        raise HTTPException(
            status_code=415,
            detail="The file type does not match the image content.",
        )
    return ALLOWED_TYPES[sniffed]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/recipes/generate", response_model=GenerateResponse)
async def generate(image: UploadFile = File(...)) -> GenerateResponse:
    data = await image.read(MAX_IMAGE_BYTES + 1)
    extension = _validate_image(data, image.content_type or "", image.filename or "")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        logger.info("received image %s (%d bytes)", image.filename, len(data))
        # Run the synchronous agent off the event loop so the API stays responsive.
        raw_text = await run_in_threadpool(generate_recipe, tmp_path)
    except HTTPException:
        raise
    except Exception:
        logger.exception("agent failed while generating a recipe")
        raise HTTPException(
            status_code=500,
            detail="Unable to generate your recipe right now. Please try again.",
        )
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("could not delete temp file %s", tmp_path)

    return GenerateResponse(recipe=Recipe(**parse_recipe(raw_text)))

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("RECIPE_LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("RECIPE_LLM_MODEL", "gpt-4o-mini")
EMBED_PROVIDER = os.getenv("RECIPE_EMBED_PROVIDER", "openai")
EMBED_MODEL = os.getenv("RECIPE_EMBED_MODEL", "text-embedding-3-small")

RECIPES_DIR = Path(os.getenv("RECIPE_RECIPES_DIR", "recipes"))
CHROMA_DIR = Path(os.getenv("RECIPE_CHROMA_DIR", ".chroma"))

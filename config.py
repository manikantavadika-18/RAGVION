import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001"
)

CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    "./storage/chroma"
)

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "genai_knowledge"
)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 5
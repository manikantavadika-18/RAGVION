import os
import chromadb
from config import CHROMA_PATH, COLLECTION_NAME

# Vercel's filesystem is read-only except /tmp, so use /tmp there.
if os.environ.get("VERCEL"):
    CHROMA_PATH = "/tmp/chroma_db"

os.makedirs(CHROMA_PATH, exist_ok=True)

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def get_collection():
    return _collection


def clear_collection():
    global _collection
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
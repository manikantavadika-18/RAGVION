import os
import re
import uuid
from werkzeug.datastructures import FileStorage

from rag.loader import load_file
from rag.chunker import chunk_text
from rag.embeddings import embed_documents
from rag.vector_store import get_collection

def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

def ingest_file(file: FileStorage):
    filename = safe_filename(file.filename)
    file_bytes = file.read()

    pages = load_file(filename, file_bytes)

    documents = []
    metadatas = []
    ids = []

    for page in pages:
        page_text = page["text"].strip()
        if not page_text:
            continue

        chunks = chunk_text(page_text)

        for index, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "filename": filename,
                "page": page.get("page") or 0,
                "chunk": index
            })
            ids.append(str(uuid.uuid4()))

    if not documents:
        raise ValueError(
            "No readable text was found. If this is a scanned PDF, install Tesseract OCR and try again."
        )

    embeddings = embed_documents(documents)

    collection = get_collection()
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return {
        "message": "Document indexed successfully.",
        "filename": filename,
        "pages": len(pages),
        "chunks": len(documents),
        "total_chunks": collection.count()
    }

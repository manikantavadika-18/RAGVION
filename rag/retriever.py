from rag.embeddings import embed_query
from rag.vector_store import get_collection
from config import TOP_K

def retrieve(query, top_k=TOP_K):
    collection = get_collection()

    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    items = []
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    for doc, metadata, distance in zip(documents, metadatas, distances):
        items.append({
            "document": doc,
            "filename": metadata.get("filename", "Unknown"),
            "page": metadata.get("page"),
            "score": max(0.0, 1.0 - float(distance))
        })

    return items

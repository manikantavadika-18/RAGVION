import json
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from rag.vector_store import get_collection

def generate_synthetic_qa(count=5):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("Upload at least one document first.")

    result = collection.get(
        limit=min(30, collection.count()),
        include=["documents"]
    )

    context = "\n\n".join(result.get("documents", []))

    prompt = f"""
Create {count} high-quality synthetic question-answer pairs from the following
knowledge-base text. These are for evaluating a RAG chatbot.

Return ONLY valid JSON in this exact shape:
[
  {{"question": "...", "answer": "..."}}
]

Knowledge base:
{context}
"""

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2000
        )
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)

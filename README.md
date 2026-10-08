# NovaRAG — GenAI Knowledge Assistant

A beginner-friendly end-to-end Generative AI mini project integrating:

- LLM
- RAG
- Embeddings
- ChromaDB
- Synthetic data generation
- PDF/TXT/DOCX ingestion
- OCR fallback for scanned PDFs
- ChatGPT-style frontend

## Architecture

Document -> Loader/OCR -> Chunking -> Embeddings -> ChromaDB
Question -> Embedding -> Retrieval -> Context -> Gemini LLM -> Answer + Sources

## Run

1. Create and activate a Python virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`.
4. Put your Gemini API key in `.env`.
5. Start:
   `python app.py`
6. Open:
   `http://127.0.0.1:5000`

## OCR on Windows

Install Tesseract OCR if you need scanned PDFs. If Tesseract is not on PATH, set the executable path in `rag/loader.py` before calling `image_to_string`.

## Important

Never commit `.env` or expose your API key in frontend JavaScript.

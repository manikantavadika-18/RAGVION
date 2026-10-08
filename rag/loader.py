import io
import os
import fitz
import pytesseract
from PIL import Image
from pypdf import PdfReader
from docx import Document

def load_txt(file_bytes):
    return [{"text": file_bytes.decode("utf-8", errors="ignore"), "page": None}]

def load_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [{"text": text, "page": None}]

def load_pdf(file_bytes):
    pages = []

    reader = PdfReader(io.BytesIO(file_bytes))
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"text": text, "page": number})

    if sum(len(p["text"].strip()) for p in pages) > 100:
        return pages

    # OCR fallback for scanned/image-only PDFs.
    ocr_pages = []
    pdf = fitz.open(stream=file_bytes, filetype="pdf")

    for number, page in enumerate(pdf, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(image)
        ocr_pages.append({"text": text, "page": number})

    return ocr_pages

def load_file(filename, file_bytes):
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return load_pdf(file_bytes)
    if ext == ".txt":
        return load_txt(file_bytes)
    if ext == ".docx":
        return load_docx(file_bytes)

    raise ValueError("Unsupported file type.")

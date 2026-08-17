"""File processor — Extract text from TXT, DOCX, PDF files."""

import logging
import os

logger = logging.getLogger(__name__)

ALLOWED_TRANSCRIPT_EXTENSIONS = {".txt", ".docx", ".pdf"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg"}


def validate_file(filename: str, file_size: int, allowed_extensions: set, max_size_mb: int = 100) -> str:
    """Validate file type and size. Returns the file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise ValueError(
            f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(f"File too large. Maximum size: {max_size_mb}MB")
    if file_size == 0:
        raise ValueError("File is empty")
    return ext


def extract_text_from_file(file_path: str) -> str:
    """Extract text content from a TXT, DOCX, or PDF file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        return _extract_txt(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext == ".pdf":
        return _extract_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type for text extraction: {ext}")


def _extract_txt(file_path: str) -> str:
    """Extract text from a TXT file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
    if not content:
        raise ValueError("TXT file is empty or contains no readable text")
    return content


def _extract_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        content = "\n".join(paragraphs)
        if not content:
            raise ValueError("DOCX file contains no readable text")
        return content
    except Exception as e:
        if "no readable text" in str(e):
            raise
        logger.error(f"Error reading DOCX: {e}")
        raise ValueError(f"Failed to read DOCX file: {e}")


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        content = "\n".join(text_parts).strip()
        if not content:
            raise ValueError("PDF file contains no extractable text")
        return content
    except Exception as e:
        if "no extractable text" in str(e):
            raise
        logger.error(f"Error reading PDF: {e}")
        raise ValueError(f"Failed to read PDF file: {e}")

"""
PDF text extraction utility using PyMuPDF.
"""

import io
from loguru import logger

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not installed. PDF parsing will be unavailable.")


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 50) -> str:
    """
    Extract text content from PDF bytes.

    Args:
        pdf_bytes: Raw PDF file bytes.
        max_pages: Maximum number of pages to extract (default 50).

    Returns:
        Extracted text as a single string.

    Raises:
        RuntimeError: If PyMuPDF is not installed.
        ValueError: If the PDF cannot be parsed.
    """
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF is required for PDF parsing. "
            "Install it with: pip install PyMuPDF"
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Failed to open PDF: {exc}") from exc

    pages_text: list[str] = []

    for page_num in range(min(len(doc), max_pages)):
        try:
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                pages_text.append(text.strip())
        except Exception as exc:
            logger.warning(f"Failed to extract page {page_num}: {exc}")
            continue

    doc.close()

    if not pages_text:
        raise ValueError("No text could be extracted from the PDF.")

    full_text = "\n\n".join(pages_text)

    # Clean up common PDF artifacts
    full_text = _clean_pdf_text(full_text)

    return full_text


def _clean_pdf_text(text: str) -> str:
    """Clean common artifacts from PDF-extracted text."""
    import re

    # Remove excessive whitespace while preserving paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove page headers/footers (common patterns)
    text = re.sub(r"\n\d+\s*\n", "\n", text)  # Standalone page numbers

    # Fix hyphenated line breaks
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    return text.strip()

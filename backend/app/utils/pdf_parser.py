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

    # 1. Remove excessive horizontal whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # 2. Fix fragmented lines (vertical text artifacts)
    # If a line is very short (e.g. 1-3 chars) and followed by a newline and more text, 
    # it's often a line-breaking artifact from two-column layouts.
    # We join lines that don't end with a sentence terminator and are followed by lowercase.
    lines = text.split("\n")
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            cleaned_lines.append("")
            i += 1
            continue
            
        # Join with next line if this line is short or doesn't end with punctuation
        # and the next line exists and doesn't start with a capital letter.
        while i + 1 < len(lines):
            next_line = lines[i+1].strip()
            if not next_line:
                break
            
            # Heuristic for joining: 
            # - Current line is short (< 40 chars)
            # - OR Doesn't end with punctuation (. ? ! :)
            # - AND Next line starts with lowercase or common joining word
            should_join = False
            if len(line) < 40:
                should_join = True
            elif not re.search(r'[.?!:]$', line):
                should_join = True
                
            if should_join and re.match(r'[a-z0-9]', next_line):
                line = line + " " + next_line
                i += 1
            else:
                break
        
        cleaned_lines.append(line)
        i += 1
    
    text = "\n".join(cleaned_lines)

    # 3. Standardize paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 4. Remove standalone page numbers and headers
    text = re.sub(r"\n\d+\s*\n", "\n", text)
    
    # 5. Fix hyphenated line breaks (re-run as catch-all)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    return text.strip()

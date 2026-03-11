"""
Text chunking utilities for the RAG pipeline.
Splits documents into overlapping chunks for embedding.
"""


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    """
    Split text into overlapping chunks using recursive character splitting.

    Args:
        text: The document text to split.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text or len(text.strip()) == 0:
        return []

    if len(text) <= chunk_size:
        return [text.strip()]

    # Separators to try splitting on (in order of preference)
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks = _recursive_split(text, separators, chunk_size, chunk_overlap)

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Recursively split text using the first working separator."""
    if not text:
        return []

    # Find the best separator
    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    # Split by separator
    if separator:
        splits = text.split(separator)
    else:
        splits = list(text)

    # Merge splits into chunks
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for split in splits:
        split_len = len(split) + (len(separator) if current_chunk else 0)

        if current_length + split_len > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = separator.join(current_chunk)
            chunks.append(chunk_text)

            # Keep overlap from end of current chunk
            overlap_text = chunk_text[-chunk_overlap:] if chunk_overlap > 0 else ""
            current_chunk = [overlap_text] if overlap_text else []
            current_length = len(overlap_text)

        current_chunk.append(split)
        current_length += split_len

    # Add remaining text
    if current_chunk:
        chunks.append(separator.join(current_chunk))

    return chunks

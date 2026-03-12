"""
Embedding generation — supports local (sentence-transformers, free) and OpenAI.
"""

import numpy as np
from loguru import logger

from app.config import get_settings

# Global model cache for local embeddings
_local_model = None


def _get_local_model():
    """Lazy-load the sentence-transformers model."""
    global _local_model
    if _local_model is None:
        try:
            import warnings
            # Suppress PyTorch precompile artifact registration warnings
            warnings.filterwarnings("ignore", message=".*already registered.*")
            warnings.filterwarnings("ignore", message=".*mega-cache.*")
            
            from sentence_transformers import SentenceTransformer

            settings = get_settings()
            _local_model = SentenceTransformer(settings.embedding_model)
            logger.info(f"Loaded embedding model: {settings.embedding_model}")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )
    return _local_model


async def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        NumPy array of shape (n_texts, embedding_dim).
    """
    settings = get_settings()

    if settings.embedding_provider == "local":
        return _generate_local_embeddings(texts)
    elif settings.embedding_provider == "openai":
        return await _generate_openai_embeddings(texts)
    else:
        raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def _generate_local_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings using sentence-transformers (free, local)."""
    model = _get_local_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)


async def _generate_openai_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings using OpenAI API."""
    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY required for OpenAI embeddings.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Process in batches of 100
    all_embeddings: list[list[float]] = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model=settings.embedding_model or "text-embedding-3-small",
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings, dtype=np.float32)

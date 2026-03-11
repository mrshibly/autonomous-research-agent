"""
FAISS-based vector store for the RAG pipeline.
"""

import os

import numpy as np
from loguru import logger

try:
    import faiss
except ImportError:
    faiss = None
    logger.warning("FAISS not installed. Vector store will be unavailable.")

from app.rag.embeddings import generate_embeddings


class VectorStore:
    """FAISS vector store for document retrieval."""

    def __init__(self, dimension: int = 384) -> None:
        """
        Initialize the vector store.

        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2).
        """
        if faiss is None:
            raise RuntimeError("faiss-cpu is required. Install with: pip install faiss-cpu")

        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: list[dict] = []
        self._id_counter = 0

    async def add_documents(
        self, texts: list[str], metadata: list[dict] | None = None
    ) -> int:
        """
        Add documents to the vector store.

        Args:
            texts: List of text chunks to add.
            metadata: Optional metadata for each text.

        Returns:
            Number of documents added.
        """
        if not texts:
            return 0

        embeddings = await generate_embeddings(texts)

        # Resize index if dimension doesn't match
        if embeddings.shape[1] != self.dimension:
            self.dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)

        self.index.add(embeddings)

        for i, text in enumerate(texts):
            doc = {
                "id": self._id_counter,
                "text": text,
                "metadata": metadata[i] if metadata and i < len(metadata) else {},
            }
            self.documents.append(doc)
            self._id_counter += 1

        logger.info(f"Added {len(texts)} documents to vector store. Total: {self.index.ntotal}")
        return len(texts)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search for the most relevant documents.

        Args:
            query: The search query.
            top_k: Number of results to return.

        Returns:
            List of matching documents with scores.
        """
        if self.index.ntotal == 0:
            return []

        query_embedding = await generate_embeddings([query])

        # Ensure top_k doesn't exceed total documents
        k = min(top_k, self.index.ntotal)

        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents) and idx >= 0:
                doc = self.documents[idx].copy()
                doc["score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to score
                results.append(doc)

        return results

    def clear(self) -> None:
        """Clear all documents from the store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._id_counter = 0
        logger.info("Vector store cleared.")

    def save(self, directory: str) -> None:
        """Save the index and documents to disk."""
        import json
        os.makedirs(directory, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        
        # Save documents and metadata
        with open(os.path.join(directory, "documents.json"), "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Vector store saved to {directory}")

    def load(self, directory: str) -> None:
        """Load the index and documents from disk."""
        import json
        index_path = os.path.join(directory, "index.faiss")
        docs_path = os.path.join(directory, "documents.json")
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            self.index = faiss.read_index(index_path)
            with open(docs_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            self._id_counter = len(self.documents)
            logger.info(f"Vector store loaded from {directory} ({self.index.ntotal} vectors)")
        else:
            logger.warning(f"Vector store files not found in {directory}")

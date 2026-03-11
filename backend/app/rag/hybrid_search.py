import numpy as np
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from loguru import logger

class HybridSearcher:
    """
    Combines Vector Search (Semantics) with BM25 (Keywords).
    """
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.bm25 = None
        self.chunks = []
        self.metadatas = []

    async def update_index(self, chunks: List[str], metadatas: List[Dict]):
        """Build the BM25 index from chunks."""
        if not chunks:
            return
        
        self.chunks = chunks
        self.metadatas = metadatas
        
        # Tokenize for BM25 (simple space splitting or better)
        tokenized_corpus = [doc.lower().split() for doc in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"Hybrid index updated with {len(chunks)} chunks.")

    async def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        alpha: Weight for vector search (0.0 to 1.0). 1.0 is vector only, 0.0 is BM25 only.
        """
        if not self.chunks or not self.bm25:
            # Fallback to pure vector search if BM25 isn't ready
            return await self.vector_store.search(query, top_k=top_k)

        # 1. Vector Search
        vector_results = await self.vector_store.search(query, top_k=top_k * 2)
        
        # 2. BM25 Search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores to [0, 1] range
        if np.max(bm25_scores) > 0:
            bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores) + 1e-9)
        
        # 3. Combine scores
        combined_results = []
        
        # We need a map of chunk_text -> vector_score
        vector_score_map = {res["content"]: res["score"] for res in vector_results}
        
        for i, chunk in enumerate(self.chunks):
            v_score = vector_score_map.get(chunk, 0.5) # Default to 0.5 if not in vector top results
            b_score = bm25_scores[i]
            
            combined_score = (alpha * v_score) + ((1 - alpha) * b_score)
            
            if combined_score > 0.3: # Threshold
                combined_results.append({
                    "content": chunk,
                    "metadata": self.metadatas[i],
                    "score": float(combined_score),
                    "vector_score": float(v_score),
                    "bm25_score": float(b_score)
                })

        # Sort and return top_k
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        return combined_results[:top_k]

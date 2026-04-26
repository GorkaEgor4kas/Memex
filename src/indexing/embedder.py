'''Embedding process'''
import asyncio
from typing import List
from sentence_transformers import SentenceTransformer


class Embedder:
    """Service for embeddings generation."""

    def __init__(self, model_name: str = 'BAAI/bge-m3'):
        self.model = SentenceTransformer(model_name)

    async def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embedding vectors
        """
        loop = asyncio.get_event_loop()
        
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                normalize_embeddings=False,
                show_progress_bar=False
            ).tolist()
        )
        
        return embeddings
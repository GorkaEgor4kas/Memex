'''Semantic search handling using ChromaDB'''
from typing import List, Tuple

from indexing.vector_store import ChromaStore
from indexing.embedder import Embedder
from core.config import config

class SemanticSearch:
    '''Performs semantic (vector) search'''

    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = ChromaStore()

    def search(
            self, query: str,
            k: int = config.retrieval.semantic_limit
    ) -> List[Tuple[str, float]]:
        '''
        Search for semantically similar chunks

        Args:
            query: user's query string
            k: number of results to return

        Returns:
            (chunk_id, score)
        '''

        #sync embeddig process for query
        query_embedding = self.embedder.model.encode(query).tolist()

        results = self.vector_store.search(query_embedding, k)
        
        return [(r["id"], r["distance"]) for r in results]
    


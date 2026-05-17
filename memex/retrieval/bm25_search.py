'''Index search handling using BM25'''
from typing import List, Tuple

from memex.indexing.bm25_store import BM25Store
from memex.core.config import config

class BM25Searcher:
    '''Performs index search'''

    def __init__(self):
        self.store = BM25Store()
        self.store.load()

    def search(self, query: str,
            k: int = config.retrieval.bm25_limit
    ) -> List[Tuple[str, float]]:
        '''
        Searches for index
        
        Args:
            query: user's query string
            k: number of results to return

        Returns: 
            (chunk_id, score)
        '''

        results = self.store.search(query, k)

        return results

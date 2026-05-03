'''Orchestrator for retrieval process'''

import asyncio
from typing import List, Tuple

from indexing.vector_store import ChromaStore
from retrieval.semantic_search import SemanticSearch
from retrieval.bm25_search import BM25Searcher
from retrieval.rrf import rrf_fusion
from core.config import config

class HybridSearch:
    '''Get final chunks base for each query'''

    def __init__(self):
        self.vector_store = ChromaStore()
        self.semantic_search = SemanticSearch()
        self.bm25_search = BM25Searcher()
        self.final_limit = config.retrieval.final_limit

    async def search(self, query: str) -> List[dict]:
        semantic_results, bm25_results = await asyncio.gather(
            asyncio.to_thread(self.semantic_search.search, query),
            asyncio.to_thread(self.bm25_search.search, query),
    )

        final_ids = rrf_fusion(semantic_results, bm25_results)
        final_ids = final_ids[:self.final_limit]

        chunks = self.vector_store.get_by_ids(final_ids)

        #Parental Retrieval
        unique_chunks = self._resolve_parents(chunks)
        
        return unique_chunks
    
    def _resolve_parents(self, chunks: List[dict]) -> List[dict]:
        seen_parents = set()
        resolved = []

        for chunk in chunks:
            parent_id = chunk["metadata"].get("parent_id")

            if parent_id:
                if parent_id not in seen_parents:
                    parent_chunk = self.vector_store.get_by_ids([parent_id])
                    if parent_chunk:
                        resolved.append(parent_chunk[0])
                        seen_parents.add(parent_id)
            else:
                if chunk["id"] not in seen_parents:
                    resolved.append(chunk)
                    seen_parents.add(chunk["id"])
        
        return resolved




    

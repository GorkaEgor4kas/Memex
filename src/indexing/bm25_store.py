'''BM25 vault logic'''
from core.config import config
from typing import List, Tuple
from indexing.chunker import Chunk
import json
from pathlib import Path

import bm25s

class BM25Store:
    '''Class for BM25 handling'''

    def __init__(self, vault_path: Path = None):
        self.vault_path = vault_path or config.path.bm25_index_path 
        self.chunk_ids = []

    def build_index(self, chunks: List[Chunk]) -> None:
        '''Completely rebuilds the BM25 index from the chunk list.'''
        
        corpus = [chunk.content for chunk in chunks]

        corpus_tokens = bm25s.tokenize(corpus, show_progress=False)
        
        self.retrieval = bm25s.BM25()
        self.retrieval.index(corpus_tokens, show_progress=False)

        self.chunk_ids = [chunk.id for chunk in chunks]

    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        '''
        Searches for index
        
        Returns: (chunk_id, score)
        '''
        #protection before build_index call 
        if not hasattr(self, 'retrieval'):
            return []
        
        query_tokens = bm25s.tokenize([query])
        results, scores = self.retrieval.retrieve(query_tokens, k=k)

        output = []

        for i, doc_idx in enumerate(results[0]):
            chunk_id = self.chunk_ids[doc_idx]
            score = float(scores[0][i])
            output.append((chunk_id, score))

        return output

    def save(self) -> None:
        '''Saves indexes to the vault '''
        if hasattr(self, 'retrieval'):
            self.retrieval.save(self.vault_path, corpus=None)
            #saving chunk_ids near
            ids_path = Path(str(self.vault_path) + ".ids.json")
            with open(ids_path, 'w') as f:
                json.dump(self.chunk_ids, f)

    def load(self) -> None:
        '''Loads indexes from the vault'''
        self.retrieval = bm25s.BM25.load(self.vault_path)
        #loading chunk_ids 
        ids_path = Path(str(self.vault_path) + ".ids.json")
        if ids_path.exists():
            with open(ids_path) as f:
                self.chunk_ids = json.load(f)

    


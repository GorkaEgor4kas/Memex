"""Vector store using FAISS."""
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import faiss

from core.config import config
from indexing.chunker import Chunk


class ChromaStore:
    """Vector storage using FAISS."""

    def __init__(self, vault_path: Path = None):
        self.db_path = vault_path or config.path.chroma_db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.db_path / "faiss.index"
        self.meta_path = self.db_path / "metadata.json"
        self.embeddings_path = self.db_path / "embeddings.npy"
        
        # init before loading
        self.index = None
        self.metadata: Dict[str, dict] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        
        if self.index_path.exists() and self.meta_path.exists():
            self.load()

    def add(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return

        embeddings_np = np.array(embeddings).astype('float32')
        
        if self.index is None:
            self.index = faiss.IndexFlatIP(embeddings_np.shape[1])
        
        start_idx = self.index.ntotal
        self.index.add(embeddings_np)
        
        for i, chunk in enumerate(chunks):
            idx = start_idx + i
            self.embeddings[chunk.id] = embeddings_np[i]
            self.metadata[chunk.id] = {
                "content": chunk.content,
                "source_file": chunk.source_file,
                "h1": chunk.metadata.get("h1", ""),
                "h2": chunk.metadata.get("h2", ""),
                "parent_id": chunk.parent_id or "",
                "parent_text": chunk.parent_text or "",
                "faiss_index": idx
            }


    def search(self, query_embedding: List[float], k: int) -> List[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        
        query_np = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_np)
        
        distances, indices = self.index.search(query_np, k)
        
        results = []
        # Create a mapping from FAISS index to chunk ID for faster lookup
        index_to_id = {meta['faiss_index']: chunk_id for chunk_id, meta in self.metadata.items()}
        
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk_id = index_to_id.get(idx)
                if chunk_id and chunk_id in self.metadata:
                    meta = self.metadata[chunk_id]
                    results.append({
                        "id": chunk_id,
                        "content": meta.get("content", ""),
                        "metadata": meta,
                        "distance": float(distances[0][i]),
                    })
        
        return results

    def get_by_ids(self, ids: List[str]) -> List[dict]:
        if not ids:
            return []
        
        results = []
        for chunk_id in ids:
            if chunk_id in self.metadata:
                meta = self.metadata[chunk_id]
                results.append({
                    "id": chunk_id,
                    "content": meta["content"],
                    "metadata": meta,
                })
        return results

    def delete_by_file(self, source_file: str) -> None:
        ids_to_delete = [
            k for k, v in self.metadata.items()
            if v.get("source_file") == source_file
        ]
        if not ids_to_delete:
            return

        for chunk_id in ids_to_delete:
            del self.metadata[chunk_id]
            del self.embeddings[chunk_id]
        
        self._rebuild_index()

    def count(self) -> int:
        return len(self.metadata)

    def clean(self) -> None:
        self.index = None
        self.metadata = {}
        self.embeddings = {}
        self.index_path.unlink(missing_ok=True)
        self.meta_path.unlink(missing_ok=True)
        self.embeddings_path.unlink(missing_ok=True)

    def save(self) -> None:
        self.db_path.mkdir(parents=True, exist_ok=True)

        if self.index:
            faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # Save embeddings as a dict of numpy arrays
        if self.embeddings:
            np.savez_compressed(str(self.embeddings_path), **self.embeddings)

    def load(self) -> None:
        self.index = faiss.read_index(str(self.index_path))
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        
        # Load embeddings
        loaded_data = np.load(str(self.embeddings_path) + ".npz")
        self.embeddings = {key: loaded_data[key] for key in loaded_data.files}

    def _rebuild_index(self) -> None:
        if not self.metadata:
            self.index = None
            self.save()
            return
        
        # Gather all embeddings in order of chunk IDs
        all_embeddings = [self.embeddings[chunk_id] for chunk_id in self.metadata]
        
        if all_embeddings:
            embeddings_np = np.array(all_embeddings).astype('float32')
            self.index = faiss.IndexFlatIP(embeddings_np.shape[1])
            self.index.add(embeddings_np)
            
            # Update FAISS indices in metadata
            for i, chunk_id in enumerate(self.metadata.keys()):
                self.metadata[chunk_id]['faiss_index'] = i
        else:
            self.index = None
        
        self.save()
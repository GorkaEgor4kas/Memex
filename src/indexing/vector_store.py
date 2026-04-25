'''ChromaDB handling'''

from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings

from core.config import config
from indexing.chunker import Chunk

class ChromaStore:
    '''Class for Vector Storage handling'''
    def __init__(self, vault_path: Path = None):
        self.db_path = vault_path or config.path.chroma_db_path
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path = str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="obsidian_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        """Add chunks with embeddings to the database."""
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]

        metadatas = [
            {
                "source_file": chunk.source_file,
                "h1": chunk.metadata.get("h1", ""),
                "h2": chunk.metadata.get("h2", ""),
                "parent_id": chunk.parent_id or "",
                "parent_text": chunk.parent_text or ""
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(self, query_embedding: List[float], k: int) -> List[dict]:
        """
        Search for similar chunks.
        
        Returns:
            List of dicts with keys: id, content, metadata, distance
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents","metadatas","distances"]
        )

        output = []

        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return output

    def delete_by_file(self, source_file: str) -> None:
        """Delete all chunks belonging to a file."""
        results = self.collection.get(
            where={"source_file": source_file}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def get_by_ids(self, ids: List[str]) -> List[dict]:
        """Retrieve chunks by their IDs."""
        if not ids:
            return []
        
        results = self.collection.get(
            ids = ids,
            include=["documents","metadatas"]
        )

        output = []
        for i, chunk_id in enumerate(results["ids"]):
            output.append({
                "id": chunk_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
            })

        return output    
    
    def count(self) -> int:
        """Return total number of chunks in the collection."""
        return self.collection.count()
    
    def clean(self) -> None:
        """Delete the collection and recreate it."""
        self.client.delete_collection("obsidian_chunks")
        self.collection = self.client.get_or_create_collection(
            name="obsidian_chunks",
            metadata={"hnsw:space": "cosine"}
        )


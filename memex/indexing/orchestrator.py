import asyncio
from pathlib import Path
from typing import List, Set, Dict, Any

from memex.core.config import config
from loguru import logger
from memex.indexing.embedder import Embedder
from memex.indexing.chunker import MarkdownChunker, Chunk
from memex.indexing.vector_store import ChromaStore
from memex.indexing.bm25_store import BM25Store
from memex.indexing.index_state import IndexState
from memex.utils.file_utils import get_all_md_files, get_relative_path



class IndexOrchestrator:
    """Coordinates the entire indexing process."""

    def __init__(
        self,
        force: bool = False,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.force = force
        self.verbose = verbose
        self.dry_run = dry_run
        self.vault_path = config.path.vault_path
        self.chunker = MarkdownChunker()
        self.embedder = Embedder()
        self.vector_store = ChromaStore()
        self.bm25_store = BM25Store()
        self.index_state = IndexState()

    async def run(self) -> Dict[str, Any]:
        """Main orchestration method."""

        all_files = get_all_md_files(self.vault_path)

        if self.dry_run:
            return self._dry_run_report(all_files)

        previous_state = self.index_state.load()

        # TODO: Detect changes (new, modified, deleted)
        to_process, to_delete = self._detect_changes(all_files, previous_state)

        if not to_process and not to_delete:
            if self.verbose:
                logger.info("Nothing to change")
            return {"processed": 0, "deleted": 0, "chunks": 0}

        stats = {"processed": 0, "deleted": 0, "chunks": 0}

        #if file needs to be deleted
        for file_path in to_delete:
            if self.verbose:
                logger.info(f"Deleting: {file_path}")
            self._delete_file(file_path)
            stats["deleted"] += 1
        
        #if file new or needs to be updated
        all_new_chunks = []
        for file_path in to_process:
            if self.verbose:
                logger.info(f"Processing: {file_path}")
            chunks = await self._process_file(file_path)
            stats["processed"] += 1
            stats["chunks"] += len(chunks)
            all_new_chunks.extend(chunks)

        self.vector_store.db_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save()

        #rebuild bm25 index if there any changes
        if to_process or to_delete:
            if self.verbose:
                logger.info("Rebuilding BM25 index...")
            self._rebuild_bm25()
        
        #Save index states (rebuilding completely)
        self.index_state.save(all_files, self.vault_path)

        for file_path in to_process:
            file_chunks  = [c for c in all_new_chunks if c.source_file == str(file_path)]
            self.index_state.update_chunks_count(file_path, self.vault_path, len(file_chunks))

        return stats


    def _detect_changes(
        self, current_files: Set[Path], previous_state: Dict[str, Any]
    ) -> tuple[List[Path], List[Path]]:
        """Determine which files to process and which to delete."""
        to_process = []
        to_delete = []

        previous_files = previous_state.get('files', {})
        previous_paths = set(previous_files.keys())
        current_relative = {get_relative_path(f, self.vault_path) for f in current_files}
        
        # files to delete
        for path_str in previous_paths - current_relative:
            try:
                to_delete.append(Path(path_str))
                Path(path_str).relative_to(self.vault_path)
            except ValueError:
                logger.warning("Skipping file outside vault: {}", path_str)

        for file_path in current_files:
            relative_path = get_relative_path(file_path, self.vault_path)

            if self.force:
                to_process.append(file_path)
            elif relative_path not in previous_files:

                #if file is new
                to_process.append(file_path)
            
            else:
                #file change check
                if self.index_state.is_file_changed(file_path, self.vault_path):
                    to_process.append(file_path)

        return to_process, to_delete

    async def _process_file(self, file_path: Path) -> List[Chunk]:
        """Process a single file: chunking -> embeddings -> ChromaDB."""
        #chunking
        chunks = self.chunker.process(file_path)

        if not chunks:
            return []
        
        #embeddings generation
        texts = [chunk.content for chunk in chunks]
        embedding = await self.embedder.get_embedding(texts)
        
        #save embeddings to DB
        self.vector_store.add(chunks, embedding)

        return chunks

    def _rebuild_bm25(self):
        """Rebuild BM25 index from all chunks in FAISS."""
        all_chunks = []
        
        for chunk_id, meta in self.vector_store.metadata.items():
            chunk = Chunk(
                id=chunk_id,
                content=meta["content"],
                source_file=meta.get("source_file", ""),
                metadata={
                    "h1": meta.get("h1", ""),
                    "h2": meta.get("h2", ""),
                },
                parent_id=meta.get("parent_id") or None,
                parent_text=meta.get("parent_text") or None,
            )
            all_chunks.append(chunk)
        
        if all_chunks:
            self.bm25_store.build_index(all_chunks)
            self.bm25_store.save()

    def _delete_file(self, file_path: Path):
        """Delete file chunks from all stores."""
        #delete data from vector DB
        self.vector_store.delete_by_file(file_path)

        self.index_state.remove_file(file_path, self.vault_path)

    def _dry_run_report(self, all_files: Set[Path]) -> Dict[str, Any]:
        """Generate preview report without making changes."""
        previous_state = self.index_state.load()
        to_process, to_delete = self._detect_changes(all_files, previous_state)

        return {
            "dry_run": True,
            "total_files": len(all_files),
            "to_process": len(to_process),
            "to_delete": len(to_delete),
            "unchanged": len(all_files) - len(to_process),
            "new_files": [
                str(f) for f in to_process if get_relative_path(f, self.vault_path) not in previous_state.get("files", {})
            ],
            "modified_files": [
                str(f) for f in to_process if get_relative_path(f, self.vault_path) in previous_state.get("files", {}   )
            ],
            "deleted_files": [str(f) for f in to_delete]
        }



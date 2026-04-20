import asyncio
from pathlib import Path
from typing import List, Set, Dict, Any

from core.config import config
from indexing.embedder import Embedder
from indexing.chunker import MarkdownChunker
from indexing.vector_store import ChromaStore
from indexing.bm25_store import BM25Store
from indexing.index_state import IndexState



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

        # TODO: Get all .md files from vault
        all_files = self._get_all_files()

        if self.dry_run:
            return self._dry_run_report(all_files)

        # TODO: Load previous state from index_state.json
        previous_state = {}

        # TODO: Detect changes (new, modified, deleted)
        to_process, to_delete = self._detect_changes(all_files, previous_state)

        stats = {"processed": 0, "deleted": 0, "chunks": 0}

        for file_path in to_process:
            if self.verbose:
                print(f"Processing: {file_path}")
            chunks = await self._process_file(file_path)
            stats["processed"] += 1
            stats["chunks"] += len(chunks)

        for file_path in to_delete:
            if self.verbose:
                print(f"Deleting: {file_path}")
            self._delete_file(file_path)
            stats["deleted"] += 1

        # TODO: Save updated state to index_state.json

        return stats

    def _get_all_files(self) -> Set[Path]:
        """Return all .md files from vault."""
        # TODO: Use file_utils.get_all_md_files(self.vault_path)
        return set()

    def _detect_changes(
        self, current_files: Set[Path], previous_state: Dict[str, Any]
    ) -> tuple[List[Path], List[Path]]:
        """Determine which files to process and which to delete."""
        to_process = []
        to_delete = []

        # TODO: Compare current files with previous_state
        # - New files: not in previous_state -> process
        # - Modified files: hash changed -> process
        # - Deleted files: in previous_state but not in current -> delete

        return to_process, to_delete

    async def _process_file(self, file_path: Path) -> List:
        """Process a single file: chunking -> BM25 -> embeddings -> ChromaDB."""
        chunks = []

        # TODO: Read file content
        # content = file_path.read_text(encoding="utf-8")

        # TODO: Chunking
        # chunks = self.chunker.process(content, source_file=str(file_path))

        # TODO: Add to BM25 index
        # self.bm25_store.add(chunks)

        # TODO: Generate embeddings
        # texts = [chunk.content for chunk in chunks]
        # embeddings = await asyncio.to_thread(self.embedder.embed, texts)

        # TODO: Add to ChromaDB
        # self.vector_store.add(chunks, embeddings)

        return chunks

    def _delete_file(self, file_path: Path):
        """Delete file chunks from all stores."""
        # TODO: Remove from ChromaDB
        # self.vector_store.delete_by_file(str(file_path))

        # TODO: Handle BM25 (rebuild index or mark as deleted)
        pass

    def _dry_run_report(self, all_files: Set[Path]) -> Dict[str, Any]:
        """Generate preview report without making changes."""
        # TODO: Load previous state
        previous_state = {}

        # TODO: Detect changes
        to_process, to_delete = self._detect_changes(all_files, previous_state)

        return {
            "dry_run": True,
            "total_files": len(all_files),
            "to_process": len(to_process),
            "to_delete": len(to_delete),
            "unchanged": len(all_files) - len(to_process),
        }


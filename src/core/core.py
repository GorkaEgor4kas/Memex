# memex/core.py
import asyncio
from retrieval.hybrid_search import HybridSearch
from generation.decider import Decider
from generation.llm_client import LLMClient
from generation.prompt import SYSTEM_PROMPT
from indexing.orchestrator import IndexOrchestrator


class MemexCore:
    """Memex as a library — importable by both CLI and external agents (Mnemosys)."""

    def __init__(self):
        self._hybrid_search = None
        self._decider = None
        self._llm_client = None

    # --- Lazy init (не грузит модели, пока не нужны) ---

    @property
    def hybrid_search(self):
        if self._hybrid_search is None:
            self._hybrid_search = HybridSearch()
        return self._hybrid_search

    @property
    def decider(self):
        if self._decider is None:
            self._decider = Decider()
        return self._decider

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    # --- Public API ---

    def search(self, query: str, offline: bool = False) -> dict:
        """Search the vault. Returns structured result dict.

        Returns:
            {
                "status": "empty" | "chunks" | "llm_answer",
                "chunks": list of chunk dicts,
                "answer": str or None,
                "sources": set of source filenames
            }
        """
        chunks = asyncio.run(self.hybrid_search.search(query))

        if not chunks:
            return {
                "status": "empty",
                "chunks": [],
                "answer": None,
                "sources": set()
            }

        decision = self.decider.decide(chunks, offline_flag=offline)

        if decision["action"] == "return_chunks":
            return {
                "status": "chunks",
                "chunks": chunks,
                "answer": decision["data"],
                "sources": self._extract_sources(chunks)
            }
        else:
            response = self.llm_client.generate(
                context=decision["data"],
                query=query,
                system_prompt=SYSTEM_PROMPT,
            )
            return {
                "status": "llm_answer",
                "chunks": chunks,
                "answer": response,
                "sources": self._extract_sources(chunks)
            }

    def index(self, force: bool = False, verbose: bool = False, dry_run: bool = False) -> dict:
        """Index (or reindex) the Obsidian vault.

        Returns:
            dict with keys: processed, deleted, chunks (if not dry_run)
            or: total_files, to_process, to_delete, unchanged, new_files, modified_files, deleted_files (if dry_run)
        """
        orchestrator = IndexOrchestrator(
            force=force,
            verbose=verbose,
            dry_run=dry_run
        )
        return asyncio.run(orchestrator.run())

    # --- Helpers ---

    def _extract_sources(self, chunks: list) -> set:
        sources = set()
        for chunk in chunks:
            source = chunk.get("metadata", {}).get("source_file", "unknown")
            sources.add(source)
        return sources
# memex/core/memex.py
import asyncio
from memex.retrieval.hybrid_search import HybridSearch
from memex.generation.decider import Decider
from memex.generation.llm_client import LLMClient
from memex.generation.prompt import SYSTEM_PROMPT
from memex.indexing.orchestrator import IndexOrchestrator


class MemexCore:
    """Memex as a library — importable by both CLI and external agents (Mnemosys)."""

    def __init__(self):
        self._hybrid_search = None
        self._decider = None
        self._llm_client = None

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

    def search(self, query: str, top_k: int = 5, offline: bool = False, raw: bool = False) -> dict:
        chunks = asyncio.run(self.hybrid_search.search(query))

        if not chunks:
            return {
                "status": "empty",
                "chunks": [],
                "answer": None,
                "sources": set()
            }

        chunks = chunks[:top_k]

        if raw:
            return {
                "status": "chunks",
                "chunks": chunks,
                "answer": self._format_chunks(chunks),
                "sources": self._extract_sources(chunks)
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
        orchestrator = IndexOrchestrator(
            force=force,
            verbose=verbose,
            dry_run=dry_run
        )
        return asyncio.run(orchestrator.run())

    def _extract_sources(self, chunks: list) -> set:
        sources = set()
        for chunk in chunks:
            source = chunk.get("metadata", {}).get("source_file", "unknown")
            sources.add(source)
        return sources
    
    def _format_chunks(self, chunks: list) -> str:
        texts = []
        for i, chunk in enumerate(chunks[:5]):
            source = chunk.get("metadata", {}).get("source_file", "unknown")
            text = chunk.get("text", str(chunk))[:300]
            texts.append(f"[{i+1}] {source}: {text}")
        return "\n\n".join(texts)
'''Decision logic for online/offline mode.'''
from typing import List, Union

from memex.utils.network import is_internet_available
from memex.core.config import config
from pathlib import Path

class Decider:
    """Decides what to do with retrieval results and prepares chunks for proper answer."""

    def __init__(self):
        self.mode = config.mode

    def decide(self, chunks: List[dict], offline_flag: bool = False) -> dict:
        """
        Decides what to do with chunks: send to LLM to generate answer or send raw data back to user

        Args:
            - chunks: list of chunks_dict from hybrid_search
            - offline_flag: --offline flag from CLI

        Returns:
            - dict with keys:
                - action: "return_chunks" | "send_to_llm"
                - data: formatted text for LLM | list of dicts (for user)
        """

        #define work mode 
        is_offline = offline_flag or self.mode == "offline"
        has_internet = not is_offline and is_internet_available()
        has_api_key = bool(config.online.provider)

        #offline mode
        if is_offline or not has_internet or not has_api_key:
            return {
                "action": "return_chunks",
                "data": self._format_chunks_for_user(chunks) 
            }
        
        #online mode
        return {
            "action": "send_to_llm",
            "data": self._format_chunks_for_llm(chunks)
        }
        
    def _format_chunks_for_user(self, chunks: List[dict]) -> str:
        """Format chunks as readable text for user."""
        
        lines = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source_file", "unknown")
            content = chunk["content"]
            lines.append(f"--- Source {i}: {source} ---")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    def _format_chunks_for_llm(self, chunks: List[dict]) -> str:
        """Format chunks as context for LLM prompt."""
        lines = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source_file", "unknown")
            filename = Path(source).name if source != "unknown" else source
            content = chunk["content"]
            lines.append(f"[Document {i}: {filename}]")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)
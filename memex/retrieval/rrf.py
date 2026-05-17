"""Reciprocal Rank Fusion."""
from typing import List, Tuple

from memex.core.config import config

def rrf_fusion(
        semantic_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        k: int = config.retrieval.rrf_k
) -> List[str]:
    '''
    Merge two ranked lists using Reciprocal Rank Fusion.

    Args:
        semantic_results: list of (chunk_id, distance) from semantic search
        bm25_results: list of (chunk_id, score) from BM25
        k: RRF smoothing parameter (default 60)

    Returns:
        List of chunk_id sorted by RRF score (descending)
    '''

    scores = {}

    for rank, (chunk_id, _) in enumerate(semantic_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, (chunk_id, _) in enumerate(bm25_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    return sorted_ids
"""
rrf.py

Implements Reciprocal Rank Fusion (RRF) to merge multiple ranked result lists.
This module is intentionally score-agnostic and operates ONLY on ranks.

RRF formula:
    score(d) = Σ 1 / (k + rank_r(d))

where:
- d is a document (resume)
- r is a ranking system (BM25, semantic, etc.)
- k is a smoothing constant (default = 60)
"""

from typing import List, Dict


def reciprocal_rank_fusion(
    bm25_results: List[Dict],
    semantic_results: List[Dict],
    k: int = 60,
    top_n: int = 10
) -> List[Dict]:
    """
    Perform Reciprocal Rank Fusion (RRF) on two ranked lists.

    Parameters
    ----------
    bm25_results : List[Dict]
        Ranked BM25 results.
        Expected format: [{"resume_id": <id>}, ...] in ranked order

    semantic_results : List[Dict]
        Ranked semantic search results.
        Expected format: [{"resume_id": <id>}, ...] in ranked order

    k : int
        Smoothing constant to prevent dominance of rank-1 documents.
        Standard value in IR literature is 60.

    top_n : int
        Number of fused results to return.

    Returns
    -------
    List[Dict]
        Final fused ranking:
        [{"resume_id": <id>, "rrf_score": <float>}, ...]
    """

    # ----------------------------
    # Defensive checks (fail fast)
    # ----------------------------
    if not bm25_results and not semantic_results:
        return []

    if k <= 0:
        raise ValueError("k must be a positive integer")

    rrf_scores = {}  # resume_id -> cumulative RRF score

    # ----------------------------
    # Process BM25 rankings
    # ----------------------------
    for rank, item in enumerate(bm25_results, start=1):
        resume_id = item.get("resume_id")

        # Skip malformed entries instead of crashing
        if resume_id is None:
            continue

        # Initialize score if first seen
        if resume_id not in rrf_scores:
            rrf_scores[resume_id] = 0.0

        # Add reciprocal rank contribution
        rrf_scores[resume_id] += 1.0 / (k + rank)

    # ----------------------------
    # Process semantic rankings
    # ----------------------------
    for rank, item in enumerate(semantic_results, start=1):
        resume_id = item.get("resume_id")

        if resume_id is None:
            continue

        if resume_id not in rrf_scores:
            rrf_scores[resume_id] = 0.0

        rrf_scores[resume_id] += 1.0 / (k + rank)

    # ----------------------------
    # Sort by fused RRF score
    # ----------------------------
    fused_ranking = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],   # sort by RRF score
        reverse=True          # higher score = better rank
    )

    # ----------------------------
    # Return top N results
    # ----------------------------
    return [
        {
            "resume_id": resume_id,
            "rrf_score": round(score, 6)  # rounded for readability/debugging
        }
        for resume_id, score in fused_ranking[:top_n]
    ]

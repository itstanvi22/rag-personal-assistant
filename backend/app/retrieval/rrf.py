from typing import List, Dict, Any

def reciprocal_rank_fusion(
    semantic_chunks: List[Dict[str, Any]],
    bm25_chunks: List[Dict[str, Any]],
    k: int = 60,
    semantic_weight: float = 0.7,
    bm25_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Combine semantic and BM25 results using Reciprocal Rank Fusion.
    
    RRF score = sum(weight / (k + rank))
    
    k=60 is the standard constant that dampens the impact of high rankings.
    semantic_weight=0.7 means we trust semantic search more than keyword search.
    """
    # Build RRF score map keyed by chunk text (unique identifier)
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, Dict] = {}

    # Score semantic results
    for rank, chunk in enumerate(semantic_chunks):
        key = chunk["text"]
        chunk_map[key] = chunk
        scores[key] = scores.get(key, 0) + semantic_weight / (k + rank + 1)

    # Score BM25 results
    for rank, result in enumerate(bm25_chunks):
        chunk = result["chunk"]
        key = chunk["text"]
        chunk_map[key] = chunk
        scores[key] = scores.get(key, 0) + bm25_weight / (k + rank + 1)

    # Sort by combined RRF score
    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Rebuild chunk list with combined scores
    fused = []
    for key in sorted_keys:
        chunk = chunk_map[key].copy()
        chunk["rrf_score"] = round(scores[key], 6)
        # Keep similarity_score if it exists, else set 0
        chunk.setdefault("similarity_score", 0.0)
        fused.append(chunk)

    return fused
import logging
import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

# In-memory BM25 index per document set
# In production this would be persisted to disk
_bm25_index = None
_indexed_chunks: List[Dict[str, Any]] = []
_bm25_signature: Any = None
_TOKEN_PATTERN = re.compile(r"[^a-z0-9\s]")


def tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenizer."""
    text = text.lower()
    text = _TOKEN_PATTERN.sub(" ", text)
    return [token for token in text.split() if len(token) > 1]


def build_bm25_index(chunks: List[Dict[str, Any]]):
    """Build BM25 index from a list of chunk dicts, reusing it when unchanged."""
    global _bm25_index, _indexed_chunks, _bm25_signature

    if not chunks:
        _indexed_chunks = []
        _bm25_index = None
        _bm25_signature = None
        return

    normalized_chunks = [chunk for chunk in chunks if isinstance(chunk, dict) and chunk.get("text")]
    if not normalized_chunks:
        _indexed_chunks = []
        _bm25_index = None
        _bm25_signature = None
        return

    signature = tuple(
        (chunk.get("text", ""), repr(chunk.get("metadata", {})))
        for chunk in normalized_chunks
    )

    if _bm25_index is not None and _indexed_chunks == normalized_chunks and _bm25_signature == signature:
        logger.info("Reusing existing BM25 index")
        return

    _indexed_chunks = normalized_chunks
    tokenized = [tokenize(chunk["text"]) for chunk in normalized_chunks]
    _bm25_index = BM25Okapi(tokenized)
    _bm25_signature = signature

    logger.info(f"Built BM25 index with {len(normalized_chunks)} chunks")


def bm25_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search BM25 index and return ranked chunks with scores."""
    global _bm25_index, _indexed_chunks

    if _bm25_index is None or not _indexed_chunks:
        logger.warning("BM25 index not built yet — returning empty results")
        return []

    if not query or not str(query).strip():
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    scores = _bm25_index.get_scores(query_tokens)

    # Pair each chunk with its BM25 score
    scored_chunks = [
        {"chunk": _indexed_chunks[i], "bm25_score": float(scores[i])}
        for i in range(len(_indexed_chunks))
    ]

    # Sort by score descending, take top_k
    scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
    top_chunks = scored_chunks[: max(1, int(top_k))]

    # Filter out zero-score results (no keyword match at all)
    top_chunks = [c for c in top_chunks if c["bm25_score"] > 0]

    logger.info(f"BM25 search returned {len(top_chunks)} results for query: '{query[:50]}'")
    return top_chunks
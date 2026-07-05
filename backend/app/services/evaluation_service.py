import logging
from typing import List, Dict, Any
from app.retrieval.retriever import retrieve_relevant_chunks
from app.services.chat_service import process_chat
import asyncio

logger = logging.getLogger(__name__)

def compute_retrieval_precision(
    retrieved_chunks: List[Dict],
    query: str,
    relevance_threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Measure what fraction of retrieved chunks are highly relevant.
    Uses similarity score as a proxy for relevance.
    """
    if not retrieved_chunks:
        return {"precision": 0.0, "relevant_count": 0, "total_count": 0}

    relevant = [
        c for c in retrieved_chunks
        if (c.get("similarity_score") or c.get("rrf_score") or 0) >= relevance_threshold
    ]

    precision = len(relevant) / len(retrieved_chunks)

    return {
        "precision": round(precision, 3),
        "relevant_count": len(relevant),
        "total_count": len(retrieved_chunks),
        "relevance_threshold": relevance_threshold
    }


def compute_context_coverage(
    answer: str,
    retrieved_chunks: List[Dict]
) -> Dict[str, Any]:
    """
    Check how many retrieved chunks contributed to the answer.
    Proxy: count chunks whose key terms appear in the answer.
    """
    if not retrieved_chunks or not answer:
        return {"coverage": 0.0, "contributing_chunks": 0}

    answer_lower = answer.lower()
    contributing = 0

    for chunk in retrieved_chunks:
        # Extract key terms from chunk (words > 4 chars, not stopwords)
        words = chunk["text"].lower().split()
        key_terms = [w for w in words if len(w) > 4][:20]

        # Check if any key terms appear in answer
        matches = sum(1 for term in key_terms if term in answer_lower)
        if matches >= 3:  # at least 3 key terms from chunk appear in answer
            contributing += 1

    coverage = contributing / len(retrieved_chunks)

    return {
        "coverage": round(coverage, 3),
        "contributing_chunks": contributing,
        "total_chunks": len(retrieved_chunks)
    }


def compute_answer_length_quality(answer: str) -> Dict[str, Any]:
    """
    Basic answer quality signals based on length and structure.
    Too short = probably didn't answer. Too long = probably rambling.
    """
    word_count = len(answer.split())
    has_citation_reference = "[Source" in answer
    is_refusal = any(phrase in answer.lower() for phrase in [
        "i don't know",
        "no information",
        "not found",
        "cannot find",
        "no relevant"
    ])

    quality = "good"
    if word_count < 10:
        quality = "too_short"
    elif word_count > 500:
        quality = "too_long"
    elif is_refusal:
        quality = "no_answer_found"

    return {
        "word_count": word_count,
        "has_citation_reference": has_citation_reference,
        "is_refusal": is_refusal,
        "quality_signal": quality
    }


async def evaluate_query(
    query: str,
    document_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Run a full evaluation pipeline for a single query.
    Returns retrieval and answer quality metrics.
    """
    logger.info(f"Evaluating query: '{query[:50]}'")

    # Get retrieved chunks
    chunks = retrieve_relevant_chunks(query, document_ids)

    # Get full answer
    result = await process_chat(query, document_ids)
    answer = result["answer"]

    # Compute metrics
    retrieval_metrics = compute_retrieval_precision(chunks, query, relevance_threshold=0.3)
    coverage_metrics = compute_context_coverage(answer, chunks)
    answer_metrics = compute_answer_length_quality(answer)

    return {
        "query": query,
        "answer": answer,
        "metrics": {
            "retrieval": retrieval_metrics,
            "coverage": coverage_metrics,
            "answer_quality": answer_metrics
        },
        "chunks_retrieved": len(chunks),
        "top_chunk_scores": [
            round(c.get("similarity_score", 0), 3)
            for c in chunks[:3]
        ]
    }


async def run_evaluation_suite(
    test_queries: List[str],
    document_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Run evaluation across multiple queries and aggregate results.
    """
    results = []
    for query in test_queries:
        result = await evaluate_query(query, document_ids)
        results.append(result)

    # Aggregate
    avg_precision = sum(
        r["metrics"]["retrieval"]["precision"] for r in results
    ) / len(results)

    avg_coverage = sum(
        r["metrics"]["coverage"]["coverage"] for r in results
    ) / len(results)

    good_answers = sum(
        1 for r in results
        if r["metrics"]["answer_quality"]["quality_signal"] == "good"
    )

    return {
        "total_queries": len(results),
        "aggregate_metrics": {
            "avg_retrieval_precision": round(avg_precision, 3),
            "avg_context_coverage": round(avg_coverage, 3),
            "good_answer_rate": round(good_answers / len(results), 3)
        },
        "individual_results": results
    }
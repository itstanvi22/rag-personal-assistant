import logging
from typing import List, Dict, Any, Optional
from app.vectordb.chroma_client import search_chunks, get_all_chunks_for_documents
from app.ingestion.embedder import embed_query
from app.retrieval.bm25_retriever import build_bm25_index, bm25_search
from app.retrieval.rrf import reciprocal_rank_fusion
from app.core.config import settings

logger = logging.getLogger(__name__)

def retrieve_relevant_chunks(
    query: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: semantic search + BM25 keyword search + RRF fusion.
    """
    if not query or not str(query).strip():
        logger.info("Empty query received; returning no chunks")
        return []

    top_k = max(1, int(top_k or settings.top_k_results))
    normalized_document_ids = [doc_id for doc_id in (document_ids or []) if doc_id]

    # --- Semantic Search ---
    logger.info("Running semantic search...")
    query_embedding = embed_query(query)
    semantic_results = search_chunks(
        query_embedding=query_embedding,
        document_ids=normalized_document_ids,
        top_k=top_k
    )

    semantic_chunks = []
    if semantic_results and semantic_results.get("documents") and semantic_results["documents"][0]:
        for doc, meta, distance in zip(
            semantic_results["documents"][0],
            semantic_results["metadatas"][0],
            semantic_results["distances"][0]
        ):
            if not doc:
                continue
            similarity = 1 - distance if distance is not None else 0.0
            if similarity > 0.3:
                semantic_chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity_score": round(similarity, 4)
                })

    logger.info(f"Semantic search returned {len(semantic_chunks)} chunks")

    # --- BM25 Keyword Search ---
    logger.info("Running BM25 keyword search...")
    all_chunks = get_all_chunks_for_documents(normalized_document_ids)

    if all_chunks:
        build_bm25_index(all_chunks)
        bm25_results = bm25_search(query, top_k=top_k)
    else:
        bm25_results = []

    logger.info(f"BM25 search returned {len(bm25_results)} chunks")

    # --- Hybrid Fusion ---
    logger.info("Fusing results with RRF...")
    fused_chunks = reciprocal_rank_fusion(
        semantic_chunks=semantic_chunks,
        bm25_chunks=bm25_results,
        semantic_weight=0.7,
        bm25_weight=0.3
    )

    final_chunks = fused_chunks[:top_k]
    logger.info(f"Hybrid retrieval final: {len(final_chunks)} chunks")

    return final_chunks
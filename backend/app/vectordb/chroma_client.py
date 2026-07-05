import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_client = None
_collection = None

def get_chroma_client():
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
        )
        _collection = _client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}  # use cosine similarity
        )
        logger.info(f"ChromaDB initialized at {settings.chroma_db_path}")
    return _client, _collection

def store_chunks(chunks: List[Dict[str, Any]], embeddings: List[List[float]], document_id: str):
    """Store chunk texts, embeddings, and metadata in ChromaDB."""
    _, collection = get_chroma_client()
    
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    logger.info(f"Stored {len(chunks)} chunks for document {document_id}")

def search_chunks(query_embedding: List[float], document_ids: List[str] = None, top_k: int = None) -> Dict:
    """Search for similar chunks. Optionally filter by document_ids."""
    _, collection = get_chroma_client()
    top_k = max(1, int(top_k or settings.top_k_results))

    # Build optional metadata filter
    where = None
    if document_ids:
        where = {"document_id": {"$in": [doc_id for doc_id in document_ids if doc_id]}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    return results

def delete_document(document_id: str):
    """Remove all chunks belonging to a document."""
    _, collection = get_chroma_client()
    collection.delete(where={"document_id": {"$eq": document_id}})
    logger.info(f"Deleted all chunks for document {document_id}")

def get_all_chunks_for_documents(document_ids: List[str] = None) -> List[Dict[str, Any]]:
    """Fetch all stored chunks for BM25 index building."""
    _, collection = get_chroma_client()
    
    where = None
    if document_ids:
        where = {"document_id": {"$in": document_ids}}
    
    results = collection.get(
        where=where,
        include=["documents", "metadatas"]
    )
    
    chunks = []
    if results and results["documents"]:
        for doc, meta in zip(results["documents"], results["metadatas"]):
            chunks.append({
                "text": doc,
                "metadata": meta,
                "similarity_score": 0.0
            })
    
    return chunks    
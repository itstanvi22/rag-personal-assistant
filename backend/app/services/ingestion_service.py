import uuid
import logging
from typing import Dict, Any, Optional
from app.ingestion.parser import parse_document
from app.ingestion.chunker import chunk_document
from app.ingestion.embedder import embed_texts
from app.vectordb.chroma_client import store_chunks

logger = logging.getLogger(__name__)

def process_document(
    file_bytes: bytes,
    filename: str,
    change_metadata: Optional[Dict[str, Any]] = None
) -> dict:
    document_id = str(uuid.uuid4())
    logger.info(f"Starting ingestion for '{filename}' with ID {document_id}")

    # Step 1: Parse
    logger.info("Step 1/4: Parsing document")
    text = parse_document(file_bytes, filename)

    # Step 2: Chunk
    logger.info("Step 2/4: Chunking text")
    chunks = chunk_document(text, filename, document_id)

    # Step 3: Inject change metadata into every chunk
    if change_metadata:
        for chunk in chunks:
            chunk["metadata"].update({
                "change_type": change_metadata.get("change_type", "general"),
                "change_title": change_metadata.get("change_title", filename),
                "affected_departments": ",".join(
                    change_metadata.get("affected_departments", [])
                )
            })

    # Step 4: Embed
    logger.info("Step 3/4: Generating embeddings")
    texts_only = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(texts_only)

    # Step 5: Store
    logger.info("Step 4/4: Storing in ChromaDB")
    store_chunks(chunks, embeddings, document_id)

    logger.info(f"Ingestion complete for '{filename}': {len(chunks)} chunks stored")

    return {
        "document_id": document_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "status": "complete"
    }
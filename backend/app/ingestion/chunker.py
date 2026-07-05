import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def split_text_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into overlapping chunks using paragraph-aware boundaries."""
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be less than chunk_size")

    chunks: List[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        split_at = text.rfind("\n\n", start, end)

        if split_at <= start:
         split_at = text.rfind("\n\n", start, end)
         if split_at > start:
          split_at += 2  # skip past the double newline

        if split_at <= start:
         split_at = text.rfind("\n", start, end)
        if split_at > start:
         split_at += 1  # skip past the newline

        if split_at <= start:
         split_at = text.rfind(". ", start, end)
        if split_at > start:
         split_at += 1  # skip past the period

        if split_at <= start:
         split_at = end

        chunk_text = text[start:split_at].strip()
        if chunk_text:
            chunks.append(chunk_text)

        next_start = split_at - chunk_overlap
        if next_start <= start:
            next_start = split_at
        start = next_start

    return chunks


def chunk_document(text: str, filename: str, document_id: str) -> List[Dict[str, Any]]:
    """
    Split document text into overlapping chunks with metadata.
    Returns list of dicts, each with 'text' and 'metadata'.
    """
    chunks = split_text_into_chunks(
        text=text,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not chunks:
        raise ValueError(f"No chunks produced from document {filename}")

    chunk_dicts = []
    for i, chunk_text in enumerate(chunks):
        chunk_dicts.append({
            "text": chunk_text,
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        })

    logger.info(f"Chunked '{filename}' into {len(chunks)} chunks")
    return chunk_dicts
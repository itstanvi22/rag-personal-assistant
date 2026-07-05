import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

# Load once at module level — not on every request
# This is critical: loading a model takes 2-5 seconds
_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")
    return _model

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convert list of strings to list of vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()

def embed_query(query: str) -> List[float]:
    """Embed a single query string — used at query time."""
    model = get_embedding_model()
    embedding = model.encode([query], show_progress_bar=False)
    return embedding[0].tolist()
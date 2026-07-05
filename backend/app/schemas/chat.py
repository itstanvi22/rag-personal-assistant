from pydantic import BaseModel
from typing import List, Optional

class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_text: str
    chunk_index: int

class ChatRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    conversation_id: str
    model_used: str
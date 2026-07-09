from pydantic import BaseModel
from typing import Optional, List

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: Optional[int] = None
    message: str
    change_type: Optional[str] = None
    change_title: Optional[str] = None
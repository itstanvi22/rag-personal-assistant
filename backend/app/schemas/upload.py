from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: Optional[int] = None
    message: str
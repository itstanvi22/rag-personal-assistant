import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.schemas.upload import UploadResponse
from app.services.ingestion_service import process_document

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

VALID_CHANGE_TYPES = [
    "policy_update",
    "process_change",
    "system_migration",
    "organizational_restructure",
    "compliance_update",
    "general"
]

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    change_type: Optional[str] = Form(default="general"),
    change_title: Optional[str] = Form(default=None),
    affected_departments: Optional[str] = Form(default=None)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 50MB."
        )

    # Parse departments from comma-separated string
    departments = []
    if affected_departments:
        departments = [d.strip() for d in affected_departments.split(",")]

    change_metadata = {
        "change_type": change_type or "general",
        "change_title": change_title or file.filename,
        "affected_departments": departments
    }

    try:
        result = process_document(file_bytes, file.filename, change_metadata)
        return UploadResponse(
            document_id=result["document_id"],
            filename=result["filename"],
            status=result["status"],
            chunk_count=result["chunk_count"],
            message=f"Successfully processed {result['chunk_count']} chunks",
            change_type=change_metadata["change_type"],
            change_title=change_metadata["change_title"]
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Document processing failed")
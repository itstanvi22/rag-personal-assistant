import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.icms_service import generate_faq, analyze_change_impact
from app.vectordb.chroma_client import get_all_chunks_for_documents

logger = logging.getLogger(__name__)
router = APIRouter()

class FAQRequest(BaseModel):
    document_id: str
    num_questions: Optional[int] = 10

class ImpactRequest(BaseModel):
    document_id: str

@router.post("/icms/generate-faq")
async def create_faq(request: FAQRequest):
    try:
        result = await generate_faq(
            document_id=request.document_id,
            num_questions=request.num_questions
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"FAQ generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/icms/analyze-impact")
async def impact_analysis(request: ImpactRequest):
    try:
        result = await analyze_change_impact(request.document_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/icms/changes")
async def list_changes():
    """List all uploaded change documents with their metadata."""
    try:
        all_chunks = get_all_chunks_for_documents()
        
        # Deduplicate by document_id
        seen = {}
        for chunk in all_chunks:
            meta = chunk.get("metadata", {})
            doc_id = meta.get("document_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "document_id": doc_id,
                    "filename": meta.get("filename", ""),
                    "change_type": meta.get("change_type", "general"),
                    "change_title": meta.get("change_title", ""),
                    "affected_departments": meta.get("affected_departments", ""),
                    "total_chunks": meta.get("total_chunks", 0)
                }
        
        return {
            "total_documents": len(seen),
            "documents": list(seen.values())
        }
    except Exception as e:
        logger.error(f"Failed to list changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
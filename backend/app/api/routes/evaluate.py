import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.evaluation_service import evaluate_query, run_evaluation_suite

logger = logging.getLogger(__name__)
router = APIRouter()

class EvaluateRequest(BaseModel):
    queries: List[str]
    document_ids: Optional[List[str]] = None

@router.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    if not request.queries:
        raise HTTPException(status_code=400, detail="Provide at least one query")
    
    try:
        if len(request.queries) == 1:
            result = await evaluate_query(
                request.queries[0],
                request.document_ids
            )
            return result
        else:
            result = await run_evaluation_suite(
                request.queries,
                request.document_ids
            )
            return result
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
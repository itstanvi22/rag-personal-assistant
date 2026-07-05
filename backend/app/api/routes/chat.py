import logging
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.services.chat_service import process_chat
from app.services.memory_service import clear_conversation

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = await process_chat(
            query=request.query,
            document_ids=request.document_ids,
            conversation_id=request.conversation_id
        )

        citations = [
            Citation(
                document_id=c["document_id"],
                filename=c["filename"],
                chunk_text=c["chunk_text"],
                chunk_index=c["chunk_index"]
            )
            for c in result["citations"]
        ]

        return ChatResponse(
            answer=result["answer"],
            citations=citations,
            conversation_id=result["conversation_id"],
            model_used=result["model_used"]
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")  
    
@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    clear_conversation(conversation_id)
    return {"message": f"Conversation {conversation_id} cleared"}    
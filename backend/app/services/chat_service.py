import logging
import httpx
import uuid
from typing import List, Optional, Dict, Any
from app.retrieval.retriever import retrieve_relevant_chunks
from app.retrieval.prompt_builder import build_prompt, extract_citations
from app.services.memory_service import get_history, add_turn
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_answer(prompt: str) -> str:
    """Send prompt to Qwen3 via Ollama and return the response."""
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                }
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]


async def process_chat(
    query: str,
    document_ids: Optional[List[str]] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Full query pipeline with conversational memory:
    question → retrieve → build prompt (with history) → generate → save turn → return
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    logger.info(f"Processing chat [{conversation_id[:8]}]: '{query[:50]}'")

    # Step 1: Get conversation history
    history = get_history(conversation_id)
    logger.info(f"Loaded {len(history)} previous messages from history")

    # Step 2: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(
        query=query,
        document_ids=document_ids
    )
    logger.info(f"Retrieved {len(chunks)} chunks")

    # Step 3: Build prompt with history injected
    prompt = build_prompt(query, chunks, history)

    # Step 4: Generate answer
    answer = await generate_answer(prompt)

    # Step 5: Save this turn to memory
    add_turn(conversation_id, query, answer)

    citations = extract_citations(chunks)

    return {
        "answer": answer,
        "citations": citations,
        "conversation_id": conversation_id,
        "model_used": settings.ollama_model
    }
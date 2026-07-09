import logging
import httpx
from typing import List, Dict, Any, Optional
from app.vectordb.chroma_client import get_all_chunks_for_documents
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

async def generate_faq(
    document_id: str,
    num_questions: int = 10
) -> Dict[str, Any]:
    """
    Generate FAQ from a change document using RAG pipeline.
    Retrieves all chunks for the document and asks LLM to generate Q&A pairs.
    """
    logger.info(f"Generating FAQ for document {document_id}")

    # Get all chunks for this document
    chunks = get_all_chunks_for_documents([document_id])

    if not chunks:
        raise ValueError(f"No chunks found for document {document_id}")

    # Get document metadata from first chunk
    metadata = chunks[0].get("metadata", {})
    change_title = metadata.get("change_title", "this document")
    change_type = metadata.get("change_type", "general")
    affected_departments = metadata.get("affected_departments", "")

    # Build context from all chunks
    context = "\n\n".join([c["text"] for c in chunks])

    # Build FAQ generation prompt
    prompt = f"""You are an expert at analyzing organizational change documents and generating helpful FAQs for employees.

CHANGE DOCUMENT: {change_title}
CHANGE TYPE: {change_type}
AFFECTED DEPARTMENTS: {affected_departments or "All departments"}

DOCUMENT CONTENT:
{context}

---

TASK: Generate exactly {num_questions} frequently asked questions (FAQs) that employees would ask about this change, along with clear, accurate answers based ONLY on the document content above.

FORMAT YOUR RESPONSE AS VALID JSON ONLY. No preamble, no explanation, just JSON:
{{
  "faqs": [
    {{
      "question": "Question here?",
      "answer": "Answer here based on document.",
      "category": "one of: Timeline, Process, Impact, Policy, General"
    }}
  ]
}}

Generate questions that cover:
- What is changing and why
- When the change takes effect
- Who is affected
- What employees need to do differently
- Where to get help or more information"""

    # Call Qwen
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                }
            }
        )
        response.raise_for_status()
        raw_answer = response.json()["response"]

    # Parse JSON response
    try:
        # Clean up response in case model adds extra text
        start = raw_answer.find("{")
        end = raw_answer.rfind("}") + 1
        json_str = raw_answer[start:end]
        faq_data = json.loads(json_str)
        faqs = faq_data.get("faqs", [])
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse FAQ JSON: {e}")
        logger.error(f"Raw response: {raw_answer}")
        # Fallback: return raw text
        faqs = [{"question": "See raw output", "answer": raw_answer, "category": "General"}]

    logger.info(f"Generated {len(faqs)} FAQs for document {document_id}")

    return {
        "document_id": document_id,
        "change_title": change_title,
        "change_type": change_type,
        "affected_departments": affected_departments,
        "total_faqs": len(faqs),
        "faqs": faqs
    }


async def analyze_change_impact(document_id: str) -> Dict[str, Any]:
    """
    Analyze a change document and return structured impact assessment.
    """
    chunks = get_all_chunks_for_documents([document_id])

    if not chunks:
        raise ValueError(f"No chunks found for document {document_id}")

    metadata = chunks[0].get("metadata", {})
    change_title = metadata.get("change_title", "this document")
    context = "\n\n".join([c["text"] for c in chunks])

    prompt = f"""Analyze this change document and provide a structured impact assessment.

DOCUMENT: {change_title}
CONTENT:
{context}

Respond in valid JSON only:
{{
  "summary": "2-3 sentence summary of the change",
  "key_changes": ["change 1", "change 2", "change 3"],
  "who_is_affected": ["group 1", "group 2"],
  "action_required": ["action 1", "action 2"],
  "timeline": "key dates and deadlines mentioned",
  "risk_level": "Low/Medium/High",
  "risk_reason": "why this risk level"
}}"""

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
        )
        response.raise_for_status()
        raw_answer = response.json()["response"]

    try:
        start = raw_answer.find("{")
        end = raw_answer.rfind("}") + 1
        json_str = raw_answer[start:end]
        impact_data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        impact_data = {"summary": raw_answer, "error": "Could not parse structured response"}

    return {
        "document_id": document_id,
        "change_title": change_title,
        "impact_assessment": impact_data
    }
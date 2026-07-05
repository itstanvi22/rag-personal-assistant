from typing import List, Dict, Any

def build_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    history: List[Dict] = None
) -> str:
    """
    Assemble final prompt with context, history, and current question.
    """
    # Build conversation history block
    history_block = ""
    if history:
        history_block = "CONVERSATION HISTORY:\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_block += f"{role}: {msg['content']}\n"
        history_block += "\n"

    # Build context block
    if not chunks:
        return f"""{history_block}You are a helpful assistant with access to a personal knowledge base. No relevant documents were found for this query.

Question: {query}

Let the user know no relevant information was found in their documents, and answer from general knowledge if appropriate."""

    context_parts = []
    for i, chunk in enumerate(chunks):
        filename = chunk["metadata"].get("filename", "Unknown")
        chunk_index = chunk["metadata"].get("chunk_index", i)
        score = chunk["similarity_score"]
        context_parts.append(
            f"[Source {i+1}: {filename}, chunk {chunk_index}, relevance: {score}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""{history_block}You are a precise and helpful assistant that answers questions based on the provided context documents.

CONTEXT DOCUMENTS:
{context}

---

INSTRUCTIONS:
- Answer using ONLY the information in the context documents
- If context doesn't contain enough information, say so explicitly
- Reference conversation history for follow-up questions
- Always cite which [Source N] you used
- Do not hallucinate or add information not present in the context

QUESTION: {query}

ANSWER:"""

    return prompt


def extract_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build citation objects from retrieved chunks."""
    citations = []
    for i, chunk in enumerate(chunks):
        citations.append({
            "source_number": i + 1,
            "document_id": chunk["metadata"].get("document_id", ""),
            "filename": chunk["metadata"].get("filename", ""),
            "chunk_index": chunk["metadata"].get("chunk_index", 0),
            "chunk_text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
            "similarity_score": chunk["similarity_score"]
        })
    return citations
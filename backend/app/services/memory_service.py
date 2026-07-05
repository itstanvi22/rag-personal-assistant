from typing import List, Dict
import time

# In-memory store: conversation_id → list of messages
# In production this would be Redis or a database
_conversations: Dict[str, List[Dict]] = {}

MAX_HISTORY_TURNS = 6  # keep last 6 exchanges (3 user + 3 assistant)
MAX_CONVERSATION_AGE = 3600  # 1 hour in seconds

def get_history(conversation_id: str) -> List[Dict]:
    """Get conversation history for a given conversation_id."""
    conversation = _conversations.get(conversation_id, {})
    if not conversation:
        return []
    
    # Expire old conversations
    if time.time() - conversation.get("created_at", 0) > MAX_CONVERSATION_AGE:
        del _conversations[conversation_id]
        return []
    
    return conversation.get("messages", [])

def add_turn(conversation_id: str, user_message: str, assistant_message: str):
    """Add a user/assistant exchange to conversation history."""
    if conversation_id not in _conversations:
        _conversations[conversation_id] = {
            "created_at": time.time(),
            "messages": []
        }
    
    messages = _conversations[conversation_id]["messages"]
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": assistant_message})
    
    # Keep only the last MAX_HISTORY_TURNS messages
    if len(messages) > MAX_HISTORY_TURNS * 2:
        _conversations[conversation_id]["messages"] = messages[-(MAX_HISTORY_TURNS * 2):]

def clear_conversation(conversation_id: str):
    """Clear history for a conversation."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
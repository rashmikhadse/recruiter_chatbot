from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    # Conversation ID (None means "New Chat")
    conversation_id: Optional[str] = None

    # User's message text
    message: str

class ChatResponse(BaseModel):
    # Assistant's reply text
    reply: str

    # Conversation ID (important for first message)
    conversation_id: str


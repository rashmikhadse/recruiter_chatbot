from pydantic import BaseModel
from datetime import datetime

class ConversationCreate(BaseModel):
    # Identifies the user/browser creating the chat
    user_id: str

class ConversationOut(BaseModel):
    # Unique ID for one conversation (chat thread)
    conversation_id: str

    # Short title shown in sidebar
    title: str

    # When the conversation was created
    created_at: datetime

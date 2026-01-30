from fastapi import APIRouter                            # FastAPI router class
from app.repositories.conversation_repo import ConversationRepository
from app.models.conversation_thread import ConversationCreate

# Create router instance required by FastAPI
router = APIRouter()

# Initialize repository to interact with MongoDB
repo = ConversationRepository()

@router.post("/conversations")
def create_conversation(payload: ConversationCreate):
    # Create a new conversation when user clicks "New Chat"
    return repo.create_conversation(payload.user_id)

@router.get("/conversations")
def list_conversations(user_id: str):
    # Return all conversations for a user (for sidebar)
    return repo.list_conversations(user_id)

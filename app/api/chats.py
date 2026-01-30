from fastapi import APIRouter
from app.services.chat_service import ChatService
from app.repositories.chat_repo import ChatRepository
from app.repositories.conversation_repo import ConversationRepository
from app.models.chat_messages import ChatRequest

# Create router instance
router = APIRouter()




# Initialize service and repositories
service = ChatService()
chat_repo = ChatRepository()
conversation_repo = ConversationRepository()

@router.post("/chat")
def chat(payload: ChatRequest):
    # If conversation_id is missing, this is a "New Chat"
    if payload.conversation_id is None:
        # Create a new conversation explicitly
        conversation = conversation_repo.create_conversation(
            user_id="default_user"  # UI should send real user_id later
        )

        # Extract newly created conversation_id
        conversation_id = conversation["conversation_id"]
    else:
        # Use existing conversation_id
        conversation_id = payload.conversation_id

    # Process message with a guaranteed conversation_id
    reply = service.process_message(
        conversation_id,
        payload.message
    )

    # Return reply AND conversation_id (important for UI)
    return {
        "reply": reply,
        "conversation_id": conversation_id
    }

@router.get("/chat/history/{conversation_id}")
def chat_history(conversation_id: str):
    # Load full message history when user opens an old chat
    return chat_repo.get_history(conversation_id)

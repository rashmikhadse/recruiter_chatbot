from app.repositories.chat_repo import ChatRepository
from app.repositories.conversation_repo import ConversationRepository


class ChatService:
    def __init__(self):
        # Repository responsible for storing and retrieving chat messages
        self.chat_repo = ChatRepository()

        # Repository responsible for conversation metadata (title, timestamps)
        self.conversation_repo = ConversationRepository()

    def _generate_title_from_message(self, message: str) -> str:
        """
        Generate a deterministic conversation title from the first user message.
        No LLM is used here — this is fast, predictable, and safe.
        """

        cleaned = message.strip()

        if not cleaned:
            return "New Chat"

        words = cleaned.split()
        title_words = words[:6]

        return " ".join(title_words).title()

    def process_message(self, conversation_id: str, user_message: str) -> str:
        """
        Process a user message within a conversation.

        GUARANTEES:
        - Conversation document exists (defensive creation)
        - Title is generated exactly once
        - Chats are always linked to a valid conversation
        """

        # --------------------------------------------------
        # 0️⃣ DEFENSIVE CHECK: ensure conversation exists
        # --------------------------------------------------

        conversation = self.conversation_repo.get_by_id(conversation_id)

        if conversation is None:
            # Conversation missing (DB reset, stale client, etc.)
            # Create it defensively
            conversation = self.conversation_repo.create_conversation(
                user_id="default_user"  # later replace with real auth
            )

            conversation_id = conversation["conversation_id"]

        # --------------------------------------------------
        # 1️⃣ Save the user's message
        # --------------------------------------------------

        self.chat_repo.save_message(
            conversation_id=conversation_id,
            role="user",
            message=user_message,
        )

        # --------------------------------------------------
        # 2️⃣ Retrieve message history
        # --------------------------------------------------

        history = self.chat_repo.get_history(conversation_id)

        user_messages = [m for m in history if m["role"] == "user"]
        is_first_message = len(user_messages) == 1

        # --------------------------------------------------
        # 3️⃣ Generate title only on first message
        # --------------------------------------------------

        if is_first_message:
            title = self._generate_title_from_message(user_message)

            self.conversation_repo.update_title(
                conversation_id=conversation_id,
                title=title,
            )

        # --------------------------------------------------
        # 4️⃣ Generate assistant reply
        # --------------------------------------------------

        assistant_reply = f"You said: {user_message}"

        # --------------------------------------------------
        # 5️⃣ Save assistant reply
        # --------------------------------------------------

        self.chat_repo.save_message(
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_reply,
        )

        # --------------------------------------------------
        # 6️⃣ Update last activity timestamp
        # --------------------------------------------------

        self.conversation_repo.update_timestamp(conversation_id)

        # --------------------------------------------------
        # 7️⃣ Return reply
        # --------------------------------------------------

        return assistant_reply

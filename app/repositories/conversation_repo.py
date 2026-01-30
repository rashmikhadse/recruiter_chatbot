import uuid
from datetime import datetime
from app.db.mongodb import conversations_collection


class ConversationRepository:

    def create_conversation(self, user_id: str):
        """
        Create a new conversation document.
        """

        if not user_id:
            raise ValueError("user_id is required to create a conversation")

        conversation_id = str(uuid.uuid4())

        conversation = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "title": "New Chat",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        conversations_collection.insert_one(conversation)

        conversation.pop("_id", None)
        return conversation

    def get_by_id(self, conversation_id: str):
        """
        Retrieve a conversation by its conversation_id.
        Returns None if not found.
        """

        if not conversation_id:
            return None

        return conversations_collection.find_one(
            {"conversation_id": conversation_id},
            {"_id": 0},
        )

    def list_conversations(self, user_id: str):
        """
        Return all conversations for a user, newest first.
        """

        return list(
            conversations_collection.find(
                {"user_id": user_id},
                {"_id": 0},
            ).sort("updated_at", -1)
        )

    def update_timestamp(self, conversation_id: str):
        """
        Update last activity timestamp.
        """

        conversations_collection.update_one(
            {"conversation_id": conversation_id},
            {"$set": {"updated_at": datetime.utcnow()}},
        )

    def update_title(self, conversation_id: str, title: str):
        """
        Update conversation title.
        Called only once after the first user message.
        """

        conversations_collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "title": title,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

from datetime import datetime                            # Timestamp support
from app.db.mongodb import chats_collection

class ChatRepository:

    def save_message(self, conversation_id: str, role: str, message: str):
        # Store a single chat message in MongoDB
        chats_collection.insert_one({
            "conversation_id": conversation_id,
            "role": role,                                 # user / assistant
            "message": message,
            "timestamp": datetime.utcnow()
        })

    def get_history(self, conversation_id: str):
        # Retrieve chat history for a conversation
        return list(
            chats_collection.find(
                {"conversation_id": conversation_id},
                {"_id": 0}                                # Exclude Mongo _id
            ).sort("timestamp", 1)
        )

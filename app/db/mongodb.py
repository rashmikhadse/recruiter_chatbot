import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# ---------------------------------------------------------
# Explicitly locate the project root and .env file
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]   # recruiter_chatbot/
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


# ---------------------------------------------------------
# MongoDB connection
# ---------------------------------------------------------

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGO_DB_NAME")]

conversations_collection = db["conversations"]
chats_collection = db["chats"]
resume_collection = db["resume_normalized"]

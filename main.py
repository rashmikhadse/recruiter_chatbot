# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api import conversations, chats


# Create FastAPI app
app = FastAPI(title="Recruitment Chatbot Backend")


# -------------------------------
# UI SERVING USING /ui
# -------------------------------

# Absolute path to ui folder
UI_DIR = Path(__file__).parent / "ui"


# Serve index.html at root "/"
@app.get("/")
def serve_root():
    return FileResponse(UI_DIR / "index.html")


# Serve entire UI folder at /ui
app.mount(
    "/ui",
    StaticFiles(directory=UI_DIR),
    name="ui"
)


# -------------------------------
# API ROUTES
# -------------------------------

app.include_router(conversations.router)
app.include_router(chats.router)

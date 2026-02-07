# semantic_index.py
# --------------------------------------------------
# Builds the semantic index for resume project vectors
# Compatible with Chroma >= 1.x
# --------------------------------------------------

import os
import chromadb
from chromadb.config import Settings

from app.db.mongodb import resume_collection


# --------------------------------------------------
# 1️⃣ Absolute persist directory (inside semantic_search)
# --------------------------------------------------

# Directory of THIS file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Logical Chroma store directory
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

# Ensure directory exists (Chroma will manage contents)
os.makedirs(CHROMA_DIR, exist_ok=True)


# --------------------------------------------------
# 2️⃣ Initialize Chroma client (1.x behavior)
# --------------------------------------------------

chroma_client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR
    )
)


# --------------------------------------------------
# 3️⃣ Create / load collection
# --------------------------------------------------
# IMPORTANT:
# - Cosine space MUST be specified at collection creation
# - This cannot be changed later without rebuilding the index
# --------------------------------------------------

semantic_collection = chroma_client.get_or_create_collection(
    name="resume_project_vectors",
    metadata={
        "hnsw:space": "cosine"
    }
)


# --------------------------------------------------
# 4️⃣ Build resume project semantic index
# --------------------------------------------------

def build_resume_project_index():
    """
    Index each project/experience vector for every resume.
    Each project is stored as an independent vector.
    """

    ids = []          # Unique vector IDs
    embeddings = []   # Project vectors
    documents = []    # Optional (empty)
    metadatas = []    # Optional metadata (not relied upon)

    # Fetch all resumes
    resumes = resume_collection.find({})

    for resume in resumes:

        # Convert Mongo ObjectId to string
        resume_id = str(resume["_id"])

        # Safely extract project vectors
        project_vectors = (
            resume
            .get("resume", {})
            .get("resume_vectors", {})
        )

        for project_id, vector in project_vectors.items():

            # Skip invalid vectors
            if not vector:
                continue

            # Vector ID encodes resume ownership
            ids.append(f"{resume_id}::{project_id}")

            embeddings.append(vector)
            documents.append("")

            metadatas.append({
                "resume_id": resume_id,
                "project_id": project_id
            })

    # Add vectors if any exist
    if ids:
        semantic_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    # Chroma 1.x persists automatically
    print(f"📦 Chroma vector count: {semantic_collection.count()}")

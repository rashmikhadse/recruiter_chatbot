# ---------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------

import re                         # Text cleanup
from typing import List           # Type hints


# ---------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------

import ollama                     # Embedding generation


# ---------------------------------------------------------
# Internal imports
# ---------------------------------------------------------

from app.job.job_agent import run_job_ingestion_agent
from app.db.mongodb import job_collection


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

EMBED_MODEL = "nomic-embed-text"   # Same space as resumes


# ---------------------------------------------------------
# BM25 stopwords
# ---------------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on",
    "with", "is", "are", "was", "were", "be", "by", "as", "at",
    "this", "that", "it", "from", "role", "responsibilities",
    "requirements", "qualification", "skills"
}


# ---------------------------------------------------------
# BM25 token generator
# ---------------------------------------------------------

def generate_job_bm25_tokens(job_text: str) -> List[str]:
    """
    Converts raw job text into BM25 tokens.
    """

    text = job_text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    tokens = [t for t in tokens if len(t) > 1 and not t.isdigit()]

    return tokens


# ---------------------------------------------------------
# Embedding generator
# ---------------------------------------------------------

def generate_job_embedding(job_semantic: str) -> List[float]:
    """
    Generates vector embedding for job semantic text.
    """

    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=job_semantic
    )

    return response["embedding"]


# ---------------------------------------------------------
# MongoDB storage
# ---------------------------------------------------------

def store_job_in_mongodb(job_document: dict):
    """
    Stores final job document in MongoDB.
    """

    job_collection.insert_one(job_document)


# ---------------------------------------------------------
# PIPELINE ENTRY POINT
# ---------------------------------------------------------

def run_job_ingestion_pipeline(user_message: str) -> None:
    """
    Runs job ingestion pipeline.
    Side-effect only: stores data in MongoDB.
    """

    print("🧠 Job ingestion pipeline started")

    # STEP 1: Semantic normalization (LLM)
    agent_output = run_job_ingestion_agent({
        "job_text": user_message
    })

    job_semantic = agent_output["job_semantic"]

    # STEP 2: BM25 tokens
    job_bm25 = generate_job_bm25_tokens(user_message)

    # STEP 3: Semantic embedding
    job_vectors = generate_job_embedding(job_semantic)

    # STEP 4: Final MongoDB document
    job_document = {
        "job_semantic": job_semantic,
        "job_bm25": job_bm25,
        "job_vectors": job_vectors
    }

    # STEP 5: Store
    store_job_in_mongodb(job_document)

    print("✅ Job stored in MongoDB")

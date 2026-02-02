# ---------------------------------------------
# Standard library imports
# ---------------------------------------------

from pathlib import Path                     # Used for safe file-system path handling
import re                                    # Used for regex-based text cleaning
import unicodedata                           # Used for unicode normalization
from typing import List, Optional            # Type hints for clarity and safety

# ---------------------------------------------
# Third-party imports
# ---------------------------------------------

import pymupdf                               # PDF text extraction (structured blocks)
import ollama                                # Local LLM embeddings

# ---------------------------------------------
# Internal imports
# ---------------------------------------------

from app.db.mongodb import resume_collection
from app.resume.resume_agent import run_resume_normalizer_agent

# ---------------------------------------------
# Constants
# ---------------------------------------------

RESUME_DIR = Path("app/static/resumes")       # Directory containing resume PDFs
EMBED_MODEL = "nomic-embed-text"              # Ollama embedding model

TARGET_RESUME = "VIBHA Resume_cloud.pdf"
# 👆 Change this value to process a different single resume
# Set to None to process ALL resumes

# =========================================================
# 1️⃣ Iterate through resume PDFs (parameterized)
# =========================================================

def iterate_resume_pdfs(target_filename: Optional[str] = None):
    """
    Generator that yields PDF files from RESUME_DIR.

    If target_filename is provided:
        → Only that specific resume is yielded.
    If None:
        → All PDFs are yielded (batch mode).
    """

    for file in RESUME_DIR.iterdir():

        # Skip directories and non-PDF files
        if not file.is_file() or file.suffix.lower() != ".pdf":
            continue

        # If a specific resume is requested, filter here
        if target_filename and file.name != target_filename:
            continue

        yield file

# =========================================================
# 2️⃣ Extract structured text from PDF
# =========================================================

def extract_structured_text_from_pdf(pdf_path: Path):
    structured_blocks = []                   # Will store page-wise text blocks

    doc = pymupdf.open(pdf_path)              # Open PDF document

    for page_number, page in enumerate(doc.pages(), start=1):
        blocks = page.get_text("blocks")      # Extract layout-aware text blocks

        for block_id, block in enumerate(blocks):
            text = block[4].strip()            # Actual text content is at index 4
            if text:
                structured_blocks.append({
                    "page": page_number,
                    "block_id": block_id,
                    "text": text
                })

    return structured_blocks

# =========================================================
# 3️⃣ BM25 preprocessing (MECHANICAL, NOT LLM)
# =========================================================

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on",
    "with", "is", "are", "was", "were", "be", "by", "as", "at",
    "this", "that", "it", "from",
    "skills", "name", "experience", "projects",
    "education", "certification", "cgpa", "gpa", "certifications"
}

def generate_bm25_tokens(structured_blocks: List[dict]) -> List[str]:
    """
    Converts extracted resume text into BM25-ready tokens.
    """

    # Combine all extracted text
    text = " ".join(block["text"] for block in structured_blocks)

    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)

    # Lowercase everything
    text = text.lower()

    # Remove emails, phone numbers, and URLs
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)
    text = re.sub(r"\b\d{10,15}\b", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Remove punctuation and special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Tokenize
    tokens = text.split()

    # Remove stopwords
    tokens = [t for t in tokens if t not in STOPWORDS]

    # Remove single-letter tokens
    tokens = [t for t in tokens if len(t) > 1]

    # Remove numeric-only tokens
    tokens = [t for t in tokens if not t.isdigit()]

    return tokens

# =========================================================
# 4️⃣ Generate embeddings (semantic only)
# =========================================================

def generate_resume_embeddings(resume_semantic: dict):
    """
    Generates embeddings for each resume section.
    Ensures the input to Ollama is always a string.
    """

    vectors = {}

    for section, content in resume_semantic.items():

        if not content:
            continue

        # ✅ Normalize content to string
        if isinstance(content, dict):
            # Flatten nested structures safely
            text = " ".join(
                str(v) for v in content.values() if isinstance(v, str)
            )
        elif isinstance(content, list):
            text = " ".join(str(v) for v in content)
        else:
            text = str(content)

        if not text.strip():
            continue

        response = ollama.embeddings(
            model=EMBED_MODEL,
            prompt=text
        )

        vectors[section] = response["embedding"]

    return vectors


# =========================================================
# 5️⃣ Store in MongoDB
# =========================================================

def store_resume_in_mongodb(resume_document: dict):

    # Defensive validation
    if not resume_document.get("name"):
        raise ValueError("Resume normalization failed: name missing")

    resume_collection.insert_one(resume_document)

# =========================================================
# 6️⃣ Orchestrator
# =========================================================

def run_resume_ingestion_pipeline():
    """
    Production-safe pipeline:
    - Can run in single-resume or batch mode
    - One resume failure does not stop others
    """

    # 🔹 Only one resume will be processed if TARGET_RESUME is set
    pdf_files = list(iterate_resume_pdfs(TARGET_RESUME))

    if not pdf_files:
        print("❌ No matching resume PDFs found.")
        return

    print(f"\n📂 Found {len(pdf_files)} resume(s). Starting ingestion...\n")

    for index, pdf_path in enumerate(pdf_files, start=1):

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📄 [{index}/{len(pdf_files)}] Processing resume:")
        print(pdf_path.name)
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        try:
            # STEP 1: Extract structured PDF text
            structured_blocks = extract_structured_text_from_pdf(pdf_path)
            print("🧾 Structured blocks extracted")

            # STEP 2: Prepare agent input
            agent_input = {
                "document_blocks": structured_blocks
            }

            # STEP 3: Resume normalization via LLM agent
            agent_output = run_resume_normalizer_agent(agent_input)
            print("🤖 Resume semantic normalization completed")

            # STEP 4: Generate BM25 tokens
            resume_bm25 = generate_bm25_tokens(structured_blocks)
            agent_output["resume"]["resume_bm25"] = resume_bm25
            print("🔍 BM25 tokens generated")

            # STEP 5: Generate semantic embeddings
            resume_semantic = agent_output["resume"]["resume_semantic"]
            vectors = generate_resume_embeddings(resume_semantic)
            agent_output["resume"]["resume_vectors"] = vectors
            print("📐 Resume embeddings generated")

            # STEP 6: Store in MongoDB
            store_resume_in_mongodb(agent_output)
            print("✅ Resume stored in MongoDB")

        except Exception as e:
            print("❌ Failed to process resume")
            print(f"Reason: {e}")

    print("\n🎉 Resume ingestion completed.")

# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    run_resume_ingestion_pipeline()

# bm25_search.py

# Import BM25 implementation
from rank_bm25 import BM25Okapi

# Import MongoDB collections
from app.db.mongodb import resume_collection, job_collection


def run_bm25_search(job_id, top_k=10):
    """
    Perform BM25 search between one job document and all resume documents.

    Args:
        job_id (ObjectId | str): MongoDB _id of the job document
        top_k (int): Number of top resumes to return

    Returns:
        list: Ranked BM25 search results
    """

    # --------------------------------------------------
    # 1️⃣ Fetch job document from MongoDB
    # --------------------------------------------------

    job_doc = job_collection.find_one({"_id": job_id})

    # If job not found, exit early
    if not job_doc:
        return []

    # Extract job BM25 tokens
    job_tokens = job_doc.get("job_bm25", [])

    # BM25 requires tokens
    if not job_tokens:
        return []

    # --------------------------------------------------
    # 2️⃣ Fetch all resumes from MongoDB
    # --------------------------------------------------

    resume_docs = list(resume_collection.find({}))

    if not resume_docs:
        return []

    # --------------------------------------------------
    # 3️⃣ Build BM25 corpus from nested resume structure
    # --------------------------------------------------

    corpus = []        # list of resume token lists
    resume_ids = []    # mapping index → resume_id

    for resume_doc in resume_docs:
        # Safely extract nested resume_bm25 tokens
        tokens = (
            resume_doc
            .get("resume", {})
            .get("resume_bm25", [])
        )

        # Skip resumes without BM25 tokens
        if not tokens:
            continue

        corpus.append(tokens)
        resume_ids.append(resume_doc["_id"])

    # If no valid resumes exist
    if not corpus:
        return []

    # --------------------------------------------------
    # 4️⃣ Initialize BM25 model
    # --------------------------------------------------

    bm25 = BM25Okapi(corpus)

    # --------------------------------------------------
    # 5️⃣ Compute BM25 scores (job vs resumes)
    # --------------------------------------------------

    scores = bm25.get_scores(job_tokens)

    # --------------------------------------------------
    # 6️⃣ Attach scores to resume IDs
    # --------------------------------------------------

    scored_resumes = []

    for idx, score in enumerate(scores):
        scored_resumes.append({
            "resume_id": resume_ids[idx],
            "bm25_score": float(score)
        })

    # --------------------------------------------------
    # 7️⃣ Sort by BM25 score (descending)
    # --------------------------------------------------

    scored_resumes.sort(
        key=lambda x: x["bm25_score"],
        reverse=True
    )

    # --------------------------------------------------
    # 8️⃣ Assign ranks and return top-k results
    # --------------------------------------------------

    top_results = []

    for rank, result in enumerate(scored_resumes[:top_k], start=1):
        result["rank"] = rank
        top_results.append(result)

    return top_results

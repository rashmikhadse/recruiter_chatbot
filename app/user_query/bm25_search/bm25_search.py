# bm25_search.py

from rank_bm25 import BM25Okapi
from app.db.mongodb import resume_collection, job_collection


def run_bm25_search(job_id, resume_ids, top_k=10):
    """
    Perform BM25 search between one job document and a FILTERED set of resumes.

    Args:
        job_id (ObjectId | str): MongoDB _id of the job document
        resume_ids (list): Resume IDs filtered by MongoDB agent
        top_k (int): Number of top resumes to return

    Returns:
        list: Ranked BM25 results (RRF-compatible)
    """

    # --------------------------------------------------
    # 1️⃣ Fetch job document
    # --------------------------------------------------
    job_doc = job_collection.find_one({"_id": job_id})
    if not job_doc:
        return []

    job_tokens = job_doc.get("job_bm25", [])
    if not job_tokens:
        return []

    # --------------------------------------------------
    # 2️⃣ Fetch ONLY filtered resumes
    # --------------------------------------------------
    resume_docs = list(
        resume_collection.find({"_id": {"$in": resume_ids}})
    )

    if not resume_docs:
        return []

    # --------------------------------------------------
    # 3️⃣ Build BM25 corpus
    # --------------------------------------------------
    corpus = []
    corpus_resume_ids = []

    for resume_doc in resume_docs:
        tokens = (
            resume_doc
            .get("resume", {})
            .get("resume_bm25", [])
        )

        if not tokens:
            continue

        corpus.append(tokens)
        corpus_resume_ids.append(resume_doc["_id"])

    if not corpus:
        return []

    # --------------------------------------------------
    # 4️⃣ BM25 scoring
    # --------------------------------------------------
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(job_tokens)

    # --------------------------------------------------
    # 5️⃣ Rank resumes
    # --------------------------------------------------
    ranked = sorted(
        zip(corpus_resume_ids, scores),
        key=lambda x: x[1],
        reverse=True
    )

    # --------------------------------------------------
    # 6️⃣ Return RRF-ready output
    # --------------------------------------------------
    results = []
    for rank, (resume_id, score) in enumerate(ranked[:top_k], start=1):
        results.append({
            "resume_id": resume_id,
            "rank": rank
        })

    return results

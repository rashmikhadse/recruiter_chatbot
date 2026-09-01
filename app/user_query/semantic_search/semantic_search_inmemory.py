from collections import defaultdict
import chromadb
from bson import ObjectId

from app.db.mongodb import resume_collection, job_collection


def run_semantic_search(job_id, resume_ids, top_k_resumes=10, top_k_projects=50):
    """
    Semantic search restricted to MongoDB-filtered resumes.
    Returns RRF-compatible ranked resume list.
    """

    # --------------------------------------------------
    # 1️⃣ Create in-memory Chroma client
    # --------------------------------------------------
    chroma_client = chromadb.Client()

    semantic_collection = chroma_client.create_collection(
        name="resume_project_vectors",
        metadata={"hnsw:space": "cosine"}
    )

    # --------------------------------------------------
    # 2️⃣ Load ONLY filtered resume project vectors
    # --------------------------------------------------
    ids = []
    embeddings = []

    resume_docs = resume_collection.find(
        {"_id": {"$in": resume_ids}}
    )

    for resume in resume_docs:
        resume_id = resume["_id"]  # KEEP ObjectId

        project_vectors = (
            resume
            .get("resume", {})
            .get("resume_vectors", {})
        )

        for project_id, vector in project_vectors.items():
            if not vector:
                continue

            ids.append(f"{resume_id}::{project_id}")
            embeddings.append(vector)

    if not ids:
        return []

    semantic_collection.add(
        ids=ids,
        embeddings=embeddings
    )

    # --------------------------------------------------
    # 3️⃣ Fetch job vector
    # --------------------------------------------------
    job_doc = job_collection.find_one({"_id": job_id})
    if not job_doc:
        return []

    job_vector = job_doc.get("job_vectors")
    if not job_vector:
        return []

    # --------------------------------------------------
    # 4️⃣ Query semantic similarity
    # --------------------------------------------------
    results = semantic_collection.query(
        query_embeddings=[job_vector],
        n_results=min(top_k_projects, len(ids))
    )

    # --------------------------------------------------
    # 5️⃣ Aggregate project ranks → resume ranks
    # --------------------------------------------------
    resume_rank_scores = defaultdict(list)

    for rank, vector_id in enumerate(results["ids"][0], start=1):
        resume_id_str = vector_id.split("::")[0]
        resume_id = ObjectId(resume_id_str)

        # Rank-based contribution (RRF-compatible philosophy)
        resume_rank_scores[resume_id].append(1 / rank)

    # --------------------------------------------------
    # 6️⃣ Resume-level MAX pooling
    # --------------------------------------------------
    ranked_resumes = sorted(
        resume_rank_scores.items(),
        key=lambda x: max(x[1]),
        reverse=True
    )

    # --------------------------------------------------
    # 7️⃣ Return RRF-ready output
    # --------------------------------------------------
    return [
        {"resume_id": resume_id}
        for resume_id, _ in ranked_resumes[:top_k_resumes]
    ]

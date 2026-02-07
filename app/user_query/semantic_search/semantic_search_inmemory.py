"""
In-memory semantic search for resume matching.

✔ No persistence
✔ No version issues
✔ No filesystem dependency
✔ Uses cosine similarity via Chroma
✔ Project-level → Resume-level aggregation (MAX pooling)
"""

from collections import defaultdict
import chromadb
from bson import ObjectId

from app.db.mongodb import resume_collection, job_collection


def run_semantic_search(job_id, top_k_resumes=10, top_k_projects=50):
    """
    Perform semantic search between job vector and resume project vectors
    using an in-memory Chroma collection.
    """

    # --------------------------------------------------
    # 1️⃣ Create in-memory Chroma client
    # --------------------------------------------------

    chroma_client = chromadb.Client()

    semantic_collection = chroma_client.create_collection(
        name="resume_project_vectors",
        metadata={"hnsw:space": "cosine"}   #Indexing is happening here, this tells Chroma: "When comparing job vectors against resume project vectors, measure similarity using cosine distance."
    )

    # --------------------------------------------------
    # 2️⃣ Load resume project vectors into Chroma
    # --------------------------------------------------

    ids = []
    embeddings = []

    for resume in resume_collection.find({}):
        resume_id = str(resume["_id"])

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

    # Defensive check
    if not ids:
        print("❌ No resume vectors loaded into semantic search")
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
        print("❌ Job not found")
        return []

    job_vector = job_doc.get("job_vectors")

    if not job_vector:
        print("❌ Job vector missing")
        return []

    # --------------------------------------------------
    # 4️⃣ Query semantic similarity
    # --------------------------------------------------

    results = semantic_collection.query(
        query_embeddings=[job_vector],
        n_results=min(top_k_projects, len(ids))
    )

    # --------------------------------------------------
    # 5️⃣ Aggregate project scores → resume scores
    # --------------------------------------------------

    resume_scores = defaultdict(list)

    # Chroma always returns ids in ranked order
    for rank, vector_id in enumerate(results["ids"][0], start=1):

        # vector_id format: resume_id::project_id
        resume_id = vector_id.split("::")[0]

        # Rank-based similarity (stable, model-agnostic)
        similarity = 1 / rank

        resume_scores[resume_id].append(similarity)

    # --------------------------------------------------
    # 6️⃣ Resume-level aggregation (MAX pooling)
    # --------------------------------------------------

    final_results = []

    for resume_id, scores in resume_scores.items():
        final_results.append({
            "resume_id": resume_id,
            "semantic_score": max(scores),
            "matched_projects": len(scores)
        })

    final_results.sort(
        key=lambda x: x["semantic_score"],
        reverse=True
    )

    return final_results[:top_k_resumes]


# --------------------------------------------------
# 7️⃣ CLI / Manual test runner
# --------------------------------------------------

if __name__ == "__main__":
    """
    Run this file directly to test semantic search.
    """

    # 🔴 REPLACE THIS WITH A REAL JOB _id FROM MongoDB
    job_id = ObjectId("6983390d520e1c647cfd01e7")

    results = run_semantic_search(job_id)

    print("\n=== SEMANTIC SEARCH RESULTS ===")

    if not results:
        print("❌ No semantic results returned")
    else:
        for r in results:
            print(
                f"Resume ID: {r['resume_id']} | "
                f"Score: {round(r['semantic_score'], 4)} | "
                f"Matched Projects: {r['matched_projects']}"
            )

# semantic_search.py
# --------------------------------------------------
# Runs semantic search (online / per query)
# Uses the SAME Chroma index stored in:
# app/user_query/semantic_search/chroma_store
# --------------------------------------------------

from collections import defaultdict

from app.db.mongodb import job_collection
from app.user_query.semantic_search.semantic_index import semantic_collection


def run_semantic_search(job_id, top_k_resumes=10, top_k_projects=50):
    """
    Semantic search using project-level vectors,
    aggregated back to resume-level
    """

    job_doc = job_collection.find_one({"_id": job_id})
    if not job_doc:
        return []

    job_vector = job_doc.get("job_vectors")
    if not job_vector:
        return []

    # Query Chroma (ids always returned)
    results = semantic_collection.query(
        query_embeddings=[job_vector],
        n_results=top_k_projects,
        include=["distances"]
    )

    raw_ids = results.get("ids")
    if not raw_ids or not raw_ids[0]:
        return []

    raw_distances = results.get("distances")
    use_rank_fallback = raw_distances is None

    resume_scores = defaultdict(list)

    for rank, vector_id in enumerate(raw_ids[0], start=1):
        resume_id = vector_id.split("::")[0]

        if use_rank_fallback:
            similarity = 1 / rank
        else:
            distance = raw_distances[0][rank - 1]
            similarity = 1 / (1 + distance)

        resume_scores[resume_id].append(similarity)

    final_results = [
        {
            "resume_id": resume_id,
            "semantic_score": max(scores),
            "matched_projects": len(scores)
        }
        for resume_id, scores in resume_scores.items()
    ]

    final_results.sort(
        key=lambda x: x["semantic_score"],
        reverse=True
    )

    return final_results[:top_k_resumes]

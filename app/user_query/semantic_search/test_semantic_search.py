# Import ObjectId for MongoDB IDs
from bson import ObjectId

# Import semantic search function
from app.user_query.semantic_search.semantic_search import run_semantic_search


def test_semantic_search():
    """
    Run semantic search and print top 10 resumes
    """

    # 🔁 Replace with a REAL job _id from MongoDB
    job_id = ObjectId("6983390d520e1c647cfd01e7")

    # Run semantic search
    results = run_semantic_search(
        job_id=job_id,
        top_k_resumes=10,
        top_k_projects=50
    )

    # If no results returned
    if not results:
        print("❌ No semantic results found")
        return

    # Print results
    print("\n✅ Semantic Search – Top 10 Resumes\n")

    for r in results:
        print(
            f"Resume ID: {r['resume_id']} | "
            f"Semantic Score: {round(r['semantic_score'], 4)} | "
            f"Matched Projects: {r['matched_projects']}"
        )


if __name__ == "__main__":
    test_semantic_search()

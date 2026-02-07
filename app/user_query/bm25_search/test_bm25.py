# app/user_query/bm25_search/test_bm25.py

from bson import ObjectId

# ✅ FULL package import (THIS IS THE FIX)
from app.user_query.bm25_search.bm25_search import run_bm25_search


def test_bm25():
    job_id = ObjectId("6983390d520e1c647cfd01e7")

    results = run_bm25_search(job_id, top_k=10)

    if not results:
        print("❌ No BM25 results")
        return

    print("\n✅ BM25 Top 10 Results\n")

    for r in results:
        print(
            f"Rank: {r['rank']} | "
            f"Resume ID: {r['resume_id']} | "
            f"Score: {round(r['bm25_score'], 4)}"
        )

if __name__ == "__main__":
    test_bm25()

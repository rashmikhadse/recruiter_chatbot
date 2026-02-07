# Import the index builder
from app.user_query.semantic_search.semantic_index import build_resume_project_index

if __name__ == "__main__":
    print("🚀 Building semantic index...")
    build_resume_project_index()
    print("✅ Semantic index built successfully")

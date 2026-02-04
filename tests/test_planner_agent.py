from app.user_query.planner_agent import classify_intent

TEST_CASES = [
    # Metadata filtering
    ("List candidates with Python", "metadata_filtering"),
    ("How many candidates have 3 years experience", "metadata_filtering"),
    ("Show candidates in Pune", "metadata_filtering"),

    # Job description
    ("We need a Python developer with 3 years experience", "job_description"),
    ("Create a JD for data engineer", "job_description"),
]

def test_planner():
    for query, expected_intent in TEST_CASES:
        result = classify_intent(query)

        assert "intent" in result, f"No intent for query: {query}"
        assert result["intent"] == expected_intent, (
            f"Wrong intent for '{query}'. "
            f"Expected {expected_intent}, got {result['intent']}"
        )

        assert 0.0 <= result["confidence_score"] <= 1.0, (
            f"Invalid confidence score for query: {query}"
        )

    print("✅ Planner agent tests passed")

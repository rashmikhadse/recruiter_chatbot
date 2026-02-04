# ---------------------------------------------------------
# Response Agent
# Responsibility:
# - Convert raw MongoDB results into UI-friendly text
# - No database access
# - No LLM calls
# ---------------------------------------------------------

from typing import List, Dict, Any


def format_response(user_query: str, results: List[Dict[str, Any]]) -> str:
    """
    Formats MongoDB results into a human-readable response.

    Parameters:
    - user_query: original user question (for context if needed)
    - results: raw MongoDB output (list of dicts)

    Returns:
    - formatted string for UI
    """

    # -----------------------------------------------------
    # Case 1: No results returned
    # -----------------------------------------------------

    if not results:
        return "No candidates found matching your criteria."

    # -----------------------------------------------------
    # Case 2: Aggregation result (e.g. count)
    # MongoDB aggregation returns something like:
    # [{ "total_candidates": 5 }]
    # -----------------------------------------------------

    if len(results) == 1 and len(results[0]) == 1:
        key = list(results[0].keys())[0]
        value = results[0][key]
        return f"{key.replace('_', ' ').title()}: {value}"

    # -----------------------------------------------------
    # Case 3: Normal candidate list (find query)
    # -----------------------------------------------------

    response_lines = [
        f"I found {len(results)} candidate(s):\n"
    ]

    for idx, candidate in enumerate(results, start=1):
        name = candidate.get("name", "N/A")
        role = candidate.get("role", "N/A")
        location = candidate.get("location", "N/A")
        experience = candidate.get("total_experience", "N/A")

        response_lines.append(
            f"{idx}. {name} | {role} | {experience} years | {location}"
        )

    return "\n".join(response_lines)

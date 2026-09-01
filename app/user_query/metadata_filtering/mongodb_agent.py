# ---------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------

import json                                  # For parsing JSON output from LLM
import time                                  # For timing / debugging
from typing import Dict, Any, List           # For clarity of data structures


# ---------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------

import ollama                                # Native Ollama client (same as resume_agent)
from app.db.mongodb import resume_collection


# ---------------------------------------------------------
# Constants (COPIED from resume_agent.py for consistency)
# ---------------------------------------------------------

OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"  # Same local model
TEMPERATURE = 0.0                            # Deterministic output


# ---------------------------------------------------------
# System Prompt (LOCKED)
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a MongoDB Query Builder Agent.

Your ONLY task is to convert a user query into an executable
MongoDB query using resume metadata.

Available metadata fields:
- name (string)
- role (string)
- location (string)
- primary_skills (array of strings)
- total_experience (number)

Allowed operations:
- filtering
- comparisons (=, >, <, >=, <=)
- aggregation (count, how many, average, min, max)

CRITICAL RULES:
- Use ONLY the metadata fields listed above
- Do NOT invent fields
- Do NOT explain anything
- Do NOT return results
- Return ONLY valid JSON
- Output MUST strictly follow one of the formats defined below

NATURAL LANGUAGE CONVERSION RULES:
- Convert experience expressions into numeric comparisons
  (example: "2 years experience" → total_experience >= 2)
- Convert skill mentions into array membership queries on primary_skills
- Convert role/location mentions into exact or case-insensitive matches

SPECIAL JOB DESCRIPTION RULE (IMPORTANT):
- If the FIRST LINE of the user input contains the phrase
  "Job Description" or "job description":
    - IGNORE all other metadata conditions
    - Extract ONLY total experience requirements (if any)
    - Generate a MongoDB FIND query that filters ONLY on total_experience
    - If no experience is mentioned, return a FIND query with an empty filter {}

AGGREGATION RULES:
- If the query asks for count / total number / how many resumes
  AND does NOT specify filters:
    - Generate a COUNT aggregation on the full collection
- Otherwise:
    - Generate a MongoDB FIND query

OUTPUT FORMATS (STRICT):

For filtering:
{
  "type": "find",
  "query": { ... }
}

For aggregation:
{
  "type": "aggregate",
  "pipeline": [ ... ]
}

"""


# ---------------------------------------------------------
# Helper: Extract JSON safely (same pattern as resume_agent)
# ---------------------------------------------------------

def extract_json_from_text(text: str) -> dict:
    """
    Safely extracts a JSON object from LLM output.
    Protects against accidental extra text or formatting.
    """

    text = text.strip()

    # Remove markdown fences if the model adds them
    if text.startswith("```"):
        text = text.split("```")[1]

    # Locate JSON boundaries
    start = text.find("{")
    end = text.rfind("}") + 1

    # Fail fast if JSON is not found
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in MongoDB agent output:\n{text}")

    return json.loads(text[start:end])


# ---------------------------------------------------------
# MongoDB execution helpers (NO LLM LOGIC HERE)
# ---------------------------------------------------------

def execute_find_query(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Executes a MongoDB find query.
    """

    # Projection to return only UI-relevant fields
    projection = {
        "name": 1,
        "contact": 1,
        "role": 1,
        "location": 1,
        "total_experience": 1,
        "primary_skills": 1,
        "_id": 0
    }

    return list(resume_collection.find(query, projection))


def execute_aggregation_pipeline(pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes a MongoDB aggregation pipeline.
    """

    return list(resume_collection.aggregate(pipeline))


# ---------------------------------------------------------
# Public API: MongoDB metadata query compiler + executor
# ---------------------------------------------------------

def run_mongodb_agent(user_query: str) -> List[Dict[str, Any]]:
    """
    Single-shot MongoDB metadata agent.

    INPUT:
    - user_query (plain text from UI / ChatService)

    OUTPUT:
    - Raw MongoDB results (list of dicts)
    """

    print("🧠 MongoDB Query Builder Agent started")

    # -----------------------------------------------------
    # 1️⃣ Construct final prompt with user query injected
    # -----------------------------------------------------

    prompt = (
        SYSTEM_PROMPT
        + "\n\nUser query:\n"
        + user_query
    )

    start_time = time.time()
    print("📤 Sending prompt to Ollama...")

    # -----------------------------------------------------
    # 2️⃣ Single-shot Ollama call (deterministic)
    # -----------------------------------------------------

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": TEMPERATURE}
    )

    print(f"📥 Ollama responded in {round(time.time() - start_time, 2)}s")

    raw_output = response["message"]["content"]

    # -----------------------------------------------------
    # 3️⃣ Parse generated MongoDB query JSON
    # -----------------------------------------------------

    parsed_output = extract_json_from_text(raw_output)

    # -----------------------------------------------------
    # 4️⃣ Execute based on query type
    # -----------------------------------------------------

    if parsed_output["type"] == "find":
        return execute_find_query(parsed_output["query"])

    if parsed_output["type"] == "aggregate":
        return execute_aggregation_pipeline(parsed_output["pipeline"])

    # Defensive fallback (should never happen)
    raise ValueError(f"Unknown MongoDB query type: {parsed_output['type']}")

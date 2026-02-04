# ---------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------

import json                     # Used to safely parse JSON returned by the LLM


# ---------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------

import ollama                   # Ollama client to call local LLM


# ---------------------------------------------------------
# Model configuration
# ---------------------------------------------------------

OLLAMA_MODEL = "qwen2.5:1.5b"   # Same local model used across your system
TEMPERATURE = 0.0                             # Zero temperature for deterministic routing


# ---------------------------------------------------------
# Planner system prompt TEMPLATE
# NOTE: <user_query> is a placeholder replaced at runtime
# ---------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """
You are a Planner Agent in a recruitment chatbot system.

Your task is to decide whether a user query can be handled
using ONLY resume metadata filtering / aggregation
or whether it represents a job description.

Available metadata fields:
- name
- role
- location
- primary_skills
- total_experience

Allowed metadata operations:
- filtering by value
- comparison (>, <, >=, <=)
- aggregation such as count, how many, number of candidates

Decision rules (apply in this order):

1. Metadata filtering:
- If the user query explicitly asks to list, find, filter, or count candidates
  AND the query uses ONLY the metadata fields above with explicit values
  (for example skills, location, years of experience),
  THEN classify as metadata_filtering.
- Queries containing aggregation words like "how many" or "count"
  are STILL metadata_filtering if they operate only on metadata fields.

2. Job description:
- If the user query describes a job role, hiring requirement,
  responsibilities, required skills
- If the user query contains hiring or role-definition language such as
  "we need", "we are hiring", "looking for", "seeking", "role requires",
  "responsibilities include",
  AND does NOT ask to list, find, or count candidates,
  THEN classify as job_description.
- Even if skills or years of experience are mentioned,
  classify as job_description when no candidate retrieval is requested.

User query:
<user_query>

If metadata filtering applies, return ONLY:
{
  "intent": "metadata_filtering",
  "target_agent": "mongodb_agent",
  "confidence_score": <float between 0 and 1>
}

Otherwise return ONLY:
{
  "intent": "job_description",
  "confidence_score": <float between 0 and 1>
}

Do NOT explain your reasoning.
Do NOT add extra text.
Return ONLY valid JSON.
"""


# ---------------------------------------------------------
# Helper function: safely extract JSON from LLM output
# ---------------------------------------------------------

def _extract_json(text: str) -> dict:
    """
    Extracts a JSON object from LLM output.
    This protects against accidental extra text or formatting.
    """

    # Remove leading/trailing whitespace
    text = text.strip()

    # Find the first opening brace
    start = text.find("{")

    # Find the last closing brace
    end = text.rfind("}") + 1

    # If JSON boundaries are not found, fail fast
    if start == -1 or end == -1:
        raise ValueError(f"No valid JSON found in planner output:\n{text}")

    # Parse and return JSON
    return json.loads(text[start:end])


# ---------------------------------------------------------
# Public API: classify intent for a user query
# ---------------------------------------------------------

def classify_intent(user_query: str) -> dict:
    """
    Classifies the user query into:
    - metadata_filtering
    - job_description

    INPUT:
    - user_query: raw string from UI (ChatService.user_message)

    OUTPUT:
    - routing JSON used by app_controller
    """

    # -----------------------------------------------------
    # 1️⃣ Inject the actual user query into the prompt
    # -----------------------------------------------------

    # Replace <user_query> placeholder with real user text
    final_prompt = SYSTEM_PROMPT_TEMPLATE.replace(
        "<user_query>",
        user_query
    )

    # -----------------------------------------------------
    # 2️⃣ Call the LLM (single-shot, stateless)
    # -----------------------------------------------------

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",        # Entire prompt is sent as user message
                "content": final_prompt
            }
        ],
        options={
            "temperature": TEMPERATURE   # Deterministic output
        }
    )

    # -----------------------------------------------------
    # 3️⃣ Extract raw text returned by the model
    # -----------------------------------------------------

    raw_output = response["message"]["content"]

    # -----------------------------------------------------
    # 4️⃣ Parse JSON safely
    # -----------------------------------------------------

    parsed_output = _extract_json(raw_output)

    # -----------------------------------------------------
    # 5️⃣ Minimal validation (fail fast if broken)
    # -----------------------------------------------------

    if "intent" not in parsed_output:
        raise ValueError("Planner output missing 'intent' field")

    if "confidence_score" not in parsed_output:
        raise ValueError("Planner output missing 'confidence_score' field")

    # -----------------------------------------------------
    # 6️⃣ Return routing decision to controller
    # -----------------------------------------------------

    return parsed_output

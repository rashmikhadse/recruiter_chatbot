# ---------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------

import json                      # JSON parsing
import time                      # Latency measurement


# ---------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------

import ollama                    # Ollama LLM client


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"
TEMPERATURE = 0.0                # Deterministic output


# ---------------------------------------------------------
# System Prompt (VERY STRICT)
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a Job Semantic Normalization Agent.

You receive a RAW job description.

Your ONLY task:
- Identify the RESPONSIBILITIES section
- Convert responsibilities into ONE clean professional paragraph

Rules:
- Merge bullet points
- Do NOT include skills, qualifications, role title, company info
- Do NOT hallucinate
- Neutral third-person tone

OUTPUT FORMAT (STRICT JSON ONLY):

{
  "job_semantic": "string"
}
"""


# ---------------------------------------------------------
# Helper: Safe JSON extraction
# ---------------------------------------------------------

def extract_json_from_text(text: str) -> dict:
    """
    Extracts JSON object from LLM output safely.
    """

    text = text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError(f"No JSON found in LLM output:\n{text}")

    return json.loads(text[start:end])


# ---------------------------------------------------------
# Public function used by job_pipeline.py
# ---------------------------------------------------------

def run_job_ingestion_agent(prepared_input: dict) -> dict:
    """
    Converts job responsibilities into prose.
    """

    print("🧠 Job Semantic Agent started")

    job_text = prepared_input.get("job_text")

    if not job_text or not job_text.strip():
        raise ValueError("job_text missing or empty")

    # Construct prompt
    prompt = SYSTEM_PROMPT + "\n\nJob Description:\n\n" + job_text

    start_time = time.time()
    print("📤 Sending prompt to Ollama...")

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": TEMPERATURE}
    )

    print(f"📥 Ollama responded in {round(time.time() - start_time, 2)}s")

    raw_output = response["message"]["content"]
    parsed_output = extract_json_from_text(raw_output)

    # Minimal validation
    if "job_semantic" not in parsed_output:
        raise ValueError("Missing job_semantic in agent output")

    if not parsed_output["job_semantic"].strip():
        raise ValueError("job_semantic is empty")

    print("✅ Job semantic normalization completed")

    return parsed_output

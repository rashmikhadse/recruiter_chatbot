# ---------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------

import json                                  # For JSON serialization / parsing
import time                                  # For basic timing / debugging


# ---------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------

import ollama                                # Native Ollama client


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"               # Local LLM model
TEMPERATURE = 0.0                            # Deterministic output


# ---------------------------------------------------------
# System Prompt (unchanged logic, but now correctly used)
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a Resume Normalization Agent.

You receive raw resume text extracted from a PDF as structured blocks.

Your task has TWO parts only.

────────────────────────────────
PART 1: METADATA INFERENCE
────────────────────────────────

Infer and return the following fields:
- name
- contact (email and/or phone if present)
- role:
  - If professional work experience exists (job title + company + dates),
    return the MOST RECENT job title.
  - If no professional experience exists, infer a suitable entry-level role
    and return it as "<Role Name> (Fresher)".
  - Future dates count as professional experience.
- total_experience in years (number or null)
- location (string or null)
- education (single readable string)
- certifications (string or empty string)
- primary_skills (list of strings)

Rules for primary_skills:
- Skills may be inferred from repeated tools, platforms, or technologies mentioned across experience and project descriptions.
- If a dedicated skills section exists, prioritize it.
- Otherwise, derive primary_skills from technologies most frequently usedin professional experience.


General rules:
- Do NOT hallucinate missing values.
- If a value cannot be inferred, return null, empty string, or empty list.
- If professional experience exists, DO NOT classify as a Fresher.

────────────────────────────────
PART 2: SEMANTIC PROSE CONVERSION
────────────────────────────────

You MUST convert ONLY:
- Professional Experience entries
- Project entries

For EACH experience or project entry:
- Generate EXACTLY ONE paragraph.
- Convert bullet points and fragmented lines into natural prose.
- Preserve company name, location, dates, responsibilities, and technologies.
- Do NOT invent information.
- Use third-person narrative with pronouns (He/She).
- Use clear professional language.

Store each paragraph as a separate key-value pair using this format:
- experience_1, experience_2, ...
- project_1, project_2, ...

────────────────────────────────
OUTPUT FORMAT (STRICT)
────────────────────────────────

Return ONLY valid JSON.
Do NOT include explanations, markdown, or extra text.

Required schema:

{
  "name": string,
  "contact": string,
  "role": string,
  "total_experience": number | null,
  "location": string | null,
  "education": string,
  "certifications": string,
  "primary_skills": [string],
  "resume": {
    "resume_semantic": {
      "experience_1": string,
      "experience_2": string,
      "project_1": string,
      "project_2": string
    }
  }
}


"""


# ---------------------------------------------------------
# Helper: Extract JSON safely from LLM output
# ---------------------------------------------------------

def extract_json_from_text(text: str) -> dict:
    """
    Extracts a JSON object from LLM output safely.
    Handles accidental extra text or code fences.
    """

    text = text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in LLM output:\n{text}")

    return json.loads(text[start:end])


# ---------------------------------------------------------
# Public function used by resume_pipeline.py
# ---------------------------------------------------------

def run_resume_normalizer_agent(prepared_input: dict) -> dict:
    """
    Single-shot resume normalization using Ollama.
    No conversations. No loops. No hanging.
    """

    print("🧠 Resume Normalizer Agent started")

    # --- SAFETY: limit input size sent to LLM ---
    document_blocks = prepared_input.get("document_blocks", [])[:60]

    llm_input = {
        "document_blocks": document_blocks
    }

    # Construct final prompt
    prompt = (
        SYSTEM_PROMPT
        + "\n\nTransform the following input into the required JSON:\n\n"
        + json.dumps(llm_input, indent=2)
    )

    start_time = time.time()
    print("📤 Sending prompt to Ollama...")

    # Single-shot Ollama call
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": TEMPERATURE}
    )

    print(f"📥 Ollama responded in {round(time.time() - start_time, 2)}s")

    raw_output = response["message"]["content"]

    # Parse JSON safely
    parsed_output = extract_json_from_text(raw_output)

    # Minimal schema validation
    required_fields = [
        "name",
        "contact",
        "role",
        "total_experience",
        "location",
        "education",
        "certifications",
        "primary_skills",
        "resume"
    ]

    for field in required_fields:
        if field not in parsed_output:
            raise ValueError(f"Missing required field: {field}")

    if "resume_semantic" not in parsed_output["resume"]:
        raise ValueError("Missing resume.resume_semantic")

    print("✅ Resume normalization successful")

    return parsed_output

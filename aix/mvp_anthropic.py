import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIG ===
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("Set your ANTHROPIC_API_KEY in the environment first.")
client = Anthropic(api_key=API_KEY)

# File paths
CLAUSE_FILE = "startup_clauses.json"
RULEBOOK_FILE = "qcb_rulebook.json"
OUTPUT_FILE = "compliance_results.json"

# === LOAD DATA ===
with open(CLAUSE_FILE, "r", encoding="utf-8") as f:
    clauses = json.load(f)

with open(RULEBOOK_FILE, "r", encoding="utf-8") as f:
    rulebook = json.load(f)

# === HELPER FUNCTION ===
def map_clause_to_rule(clause_text):
    """
    Uses Claude via Messages API to map a startup clause
    to the most relevant QCB rule.
    """
    system_prompt = (
        "You are an AI assistant that maps startup policy clauses "
        "to the most relevant QCB rule. Respond with a JSON object:\n"
        '{ "mapped_rule": "QCB x.x.x", "compliance": "yes"/"no", '
        '"reason": "brief explanation" }'
    )

    user_message = f"Map the following clause:\n\n{clause_text}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5
        max_tokens=300,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # Extract AI completion from the correct response structure
    completion_text = response.content[0].text.strip()

    # Remove markdown code blocks if present
    if completion_text.startswith("```json"):
        completion_text = completion_text.replace("```json", "", 1)
    if completion_text.startswith("```"):
        completion_text = completion_text.replace("```", "", 1)
    if completion_text.endswith("```"):
        completion_text = completion_text.rsplit("```", 1)[0]
    
    completion_text = completion_text.strip()

    # Attempt to parse JSON from response
    try:
        result = json.loads(completion_text)
    except json.JSONDecodeError as e:
        # If AI doesn't return valid JSON, return fallback
        result = {
            "mapped_rule": "unknown",
            "compliance": "unknown",
            "reason": f"Parse error: {completion_text}"
        }

    return result

# === MAIN PROCESSING ===
results = []

for clause in clauses:
    clause_text = clause.get("clause", "")
    mapped_result = map_clause_to_rule(clause_text)

    # Build final output structure
    results.append({
        "clause": clause_text,
        "source": clause.get("source", ""),
        "mapped_rule": mapped_result.get("mapped_rule"),
        "compliance": mapped_result.get("compliance"),
        "reason": mapped_result.get("reason")
    })

# === SAVE OUTPUT ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"✅ Compliance mapping done! Results saved to {OUTPUT_FILE}")
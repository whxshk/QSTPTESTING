"""
Unified MVP AI Compliance Pipeline — Hackathon Deploy-Ready
"""

import os
import json
import re
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from anthropic import Anthropic
from dotenv import load_dotenv

# === Setup ===
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
assert ANTHROPIC_API_KEY, "Set your ANTHROPIC_API_KEY in the environment first."

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# === Config ===
CLAUSE_FILE = "startup_clauses.json"
RULE_FILE = "qcb_rulebook.json"
RESOURCE_FILE = "resources.json"
CONFIG_FILE = "config.json"
OUTPUT_FILE = "compliance_results.json"

# === Load Data ===
clauses = json.load(open(CLAUSE_FILE, "r", encoding="utf-8"))
rules = json.load(open(RULE_FILE, "r", encoding="utf-8"))
resources = json.load(open(RESOURCE_FILE, "r", encoding="utf-8"))
config = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

# Extract config values
SIM_THRESHOLD = config["pipeline_config"]["similarity_threshold"]
MAX_RECOMMENDATIONS = config["pipeline_config"]["max_recommendations"]
CLAUDE_MODEL = config["pipeline_config"]["claude_model"]
MAX_TOKENS = config["pipeline_config"]["max_tokens"]
DEFAULT_CONFIDENCE = config["pipeline_config"]["default_confidence"]

# === Load SentenceTransformer Model ===
model = SentenceTransformer('all-MiniLM-L6-v2')
rule_texts = [r["description"] for r in rules]
rule_embeddings = model.encode(rule_texts, convert_to_tensor=True)

# === Gap Severity Classification ===
def classify_gap_severity(rule_id, compliance):
    """Classify gap severity based on rule type and compliance status from config"""
    if compliance == "no":
        severity_data = config["severity_mapping"].get(rule_id, {
            "severity": "Regulatory Gap",
            "category": "General",
            "priority": 3,
            "description": "Unclassified regulatory gap"
        })
        return severity_data
    return {
        "severity": "Compliant",
        "category": "N/A",
        "priority": 0,
        "description": "Meets regulatory requirements"
    }

# === Financial Gap Calculator ===
def calculate_financial_gap(clause_text, rule_id):
    """Extract and calculate financial shortfalls for capital requirements"""
    capital_req = config["capital_requirements"].get(rule_id)
    if not capital_req:
        return None
    
    # Extract capital amount from clause
    capital_match = re.search(r'QAR\s*([\d,]+)', clause_text)
    if not capital_match:
        return None
    
    current_capital = int(capital_match.group(1).replace(',', ''))
    required_capital = capital_req["minimum_capital"]
    
    if current_capital < required_capital:
        shortfall = required_capital - current_capital
        return {
            "current": f"QAR {current_capital:,}",
            "required": f"QAR {required_capital:,}",
            "shortfall": f"QAR {shortfall:,}",
            "category": capital_req["category"]
        }
    return None

# === Resource Recommendation Engine ===
def recommend_resources(rule_id, severity_data):
    """Match identified gaps to relevant resources from resources.json"""
    recommendations = []
    
    # Get relevant keywords from config
    relevant_keywords = config["resource_keywords_mapping"].get(rule_id, [])
    
    # Process QDB Programs
    for program in resources.get("qdb_programs", []):
        # Match based on keywords in program name and focus areas
        program_text = " ".join([
            program.get("program_name", ""),
            " ".join(program.get("focus_areas", []))
        ]).lower()
        
        # Check if any keyword matches
        if any(keyword in program_text for keyword in relevant_keywords):
            recommendations.append({
                "resource_id": program.get("program_id", "N/A"),
                "name": program.get("program_name", "Unknown Program"),
                "type": "QDB Program",
                "provider": "Qatar Development Bank",
                "focus_areas": program.get("focus_areas", []),
                "description": f"QDB Program focusing on: {', '.join(program.get('focus_areas', []))}"
            })
    
    # Process Compliance Experts
    for expert in resources.get("compliance_experts", []):
        # Match based on keywords in name and specialization
        expert_text = " ".join([
            expert.get("name", ""),
            expert.get("specialization", "")
        ]).lower()
        
        # Check if any keyword matches
        if any(keyword in expert_text for keyword in relevant_keywords):
            recommendations.append({
                "resource_id": expert.get("expert_id", "N/A"),
                "name": expert.get("name", "Unknown Expert"),
                "type": "Compliance Expert",
                "provider": "QCB Network",
                "specialization": expert.get("specialization", "N/A"),
                "description": expert.get("specialization", "Compliance specialist")
            })
    
    return recommendations[:MAX_RECOMMENDATIONS]

# === Claude API Function ===
def map_with_claude(clause_text, rulebook_context):
    """Use Claude API to map clause to QCB rule with enhanced context"""
    system_prompt = (
        "You are an expert AI compliance assistant for Qatar Central Bank (QCB) fintech regulations. "
        "Analyze the startup clause against QCB rules and respond with valid JSON:\n\n"
        '{\n'
        '  "mapped_rule": "QCB x.x.x",\n'
        '  "compliance": "yes"|"no",\n'
        '  "reason": "detailed explanation of compliance status",\n'
        '  "confidence": 0.85,\n'
        '  "action_required": "specific action if non-compliant or null if compliant"\n'
        '}\n\n'
        "IMPORTANT: Return raw JSON only, no markdown code blocks."
    )
    
    user_message = (
        f"Available QCB Rules:\n{rulebook_context}\n\n"
        f"Analyze this startup clause:\n{clause_text}"
    )

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
        if text.startswith("```"):
            text = text.replace("```", "", 1)
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        
        text = text.strip()
        parsed = json.loads(text)

        # Validate and provide defaults
        if "confidence" not in parsed or not isinstance(parsed["confidence"], (int, float)):
            parsed["confidence"] = DEFAULT_CONFIDENCE
        if parsed.get("compliance") not in ["yes", "no"]:
            parsed["compliance"] = "unknown"
        if "action_required" not in parsed:
            parsed["action_required"] = None

        return parsed

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error for clause: {clause_text[:50]}...")
        print(f"   Raw response: {text[:200] if 'text' in locals() else 'No response'}")
        return {
            "mapped_rule": "unknown",
            "compliance": "unknown",
            "reason": f"JSON parse error: {str(e)}",
            "confidence": 0.0,
            "action_required": None
        }
    except Exception as e:
        print(f"❌ API error for clause: {clause_text[:50]}...")
        print(f"   Error: {str(e)}")
        return {
            "mapped_rule": "unknown",
            "compliance": "unknown",
            "reason": f"API error: {str(e)}",
            "confidence": 0.0,
            "action_required": None
        }

# === Main Processing Loop ===
results = []
total_confidence = 0.0
gaps_detected = 0

# Create rulebook context for Claude
rulebook_context = "\n".join([
    f"• {r['rule_id']}: {r['title']} - {r['description']}" 
    for r in rules
])

print(f"\n{'='*60}")
print(f"Starting AI Compliance Analysis Pipeline")
print(f"{'='*60}\n")

for i, clause in enumerate(clauses, 1):
    clause_text = clause["clause"]
    print(f"[{i}/{len(clauses)}] Processing: {clause_text[:60]}...")
    
    # Encode clause and compute similarity with all rules
    clause_emb = model.encode(clause_text, convert_to_tensor=True)
    cos_scores = util.cos_sim(clause_emb, rule_embeddings)[0].cpu().numpy()

    best_idx = cos_scores.argmax()
    best_score = float(cos_scores[best_idx])
    matched_rule = rules[best_idx]

    # Low confidence fallback → Claude API
    if best_score < SIM_THRESHOLD:
        print(f"   ⚠️ Low similarity ({best_score:.2f}) → Calling Claude API...")
        ai_result = map_with_claude(clause_text, rulebook_context)
        mapped_rule = ai_result["mapped_rule"]
        compliance = ai_result["compliance"]
        reason = ai_result["reason"]
        confidence = ai_result.get("confidence", 0.0)
        action_required = ai_result.get("action_required")
        print(f"   ✅ Claude: {mapped_rule} | {compliance} | confidence={confidence}")
    else:
        mapped_rule = matched_rule["rule_id"]
        compliance = "yes"
        reason = f"Matched with {matched_rule['title']} (cosine similarity={best_score:.2f})"
        confidence = best_score
        action_required = None
        print(f"   ✅ High similarity: {mapped_rule} | confidence={confidence:.2f}")

    # Classify severity
    severity_data = classify_gap_severity(mapped_rule, compliance)
    
    # Calculate financial gap if applicable
    financial_gap = calculate_financial_gap(clause_text, mapped_rule)
    
    # Recommend resources for non-compliant items
    recommendations = []
    if compliance == "no":
        gaps_detected += 1
        recommendations = recommend_resources(mapped_rule, severity_data)
        print(f"   🔴 GAP DETECTED: {severity_data['severity']}")
        if recommendations:
            print(f"   💡 {len(recommendations)} resource(s) recommended")
        if financial_gap:
            print(f"   💰 Financial shortfall: {financial_gap['shortfall']}")

    total_confidence += confidence

    # Build result entry
    result_entry = {
        "clause": clause_text,
        "source": clause.get("source", ""),
        "mapped_rule": mapped_rule,
        "compliance": compliance,
        "severity": severity_data["severity"],
        "severity_category": severity_data["category"],
        "priority": severity_data["priority"],
        "reason": reason,
        "confidence": round(confidence, 2)
    }
    
    if action_required:
        result_entry["action_required"] = action_required
    
    if financial_gap:
        result_entry["financial_gap"] = financial_gap
    
    if recommendations:
        result_entry["recommendations"] = recommendations
    
    results.append(result_entry)

# === Calculate Summary Statistics ===
average_conf = round(total_confidence / len(results), 2) if results else 0.0
compliance_rate = round((len(results) - gaps_detected) / len(results) * 100, 1) if results else 0.0

# === Save Output ===
final_output = {
    "model": CLAUDE_MODEL,
    "timestamp": datetime.utcnow().isoformat(),
    "configuration": {
        "similarity_threshold": SIM_THRESHOLD,
        "max_recommendations": MAX_RECOMMENDATIONS,
        "default_confidence": DEFAULT_CONFIDENCE
    },
    "summary": {
        "total_clauses": len(results),
        "compliant_clauses": len(results) - gaps_detected,
        "gaps_detected": gaps_detected,
        "compliance_rate": f"{compliance_rate}%",
        "average_confidence": average_conf
    },
    "results": results
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

# === Final Report ===
print(f"\n{'='*60}")
print(f"✅ Pipeline Complete!")
print(f"{'='*60}")
print(f"Total clauses analyzed: {len(results)}")
print(f"✅ Compliant: {len(results) - gaps_detected}")
print(f"Gaps detected: {gaps_detected}")
print(f"Compliance rate: {compliance_rate}%")
print(f"Average confidence: {average_conf}")
print(f"Results saved to: {OUTPUT_FILE}")
print(f"{'='*60}\n")
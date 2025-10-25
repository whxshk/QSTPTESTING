import json
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Load rules (regulatory framework)
with open("rules.json", "r", encoding="utf-8") as f:
    rules = json.load(f)

# Load startup clauses
with open("startup_clauses.json", "r", encoding="utf-8") as f:
    clauses = json.load(f)

# Load resource mapping
with open("resources.json", "r", encoding="utf-8") as f:
    resources = json.load(f)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Precompute embeddings for rules
rule_texts = [r['text'] for r in rules]
rule_embeddings = model.encode(rule_texts, convert_to_tensor=True)

# Threshold for semantic similarity
SIM_THRESHOLD = 0.7

results = []

for clause in clauses:
    clause_text = clause['clause']
    clause_embedding = model.encode(clause_text, convert_to_tensor=True)
    
    # Compute cosine similarity
    cosine_scores = util.cos_sim(clause_embedding, rule_embeddings)[0].cpu().numpy()
    
    # Find best matching rule
    best_idx = np.argmax(cosine_scores)
    best_score = cosine_scores[best_idx]
    
    matched_rule = rules[best_idx]
    compliance = "yes" if best_score >= SIM_THRESHOLD else "no"
    
    # Map to programs/experts if not compliant
    rec_programs = []
    rec_experts = []
    if compliance == "no":
        # Example: check focus areas and recommend relevant resources
        for program in resources["qdb_programs"]:
            for area in program.get("focus_areas", []):
                if area.lower() in matched_rule['title'].lower():
                    rec_programs.append(program["program_name"])
        for expert in resources["compliance_experts"]:
            if matched_rule['ref'] in expert.get("specialization", ""):
                rec_experts.append(expert["name"])
    
    results.append({
        "clause": clause_text,
        "source": clause.get("source"),
        "mapped_rule": matched_rule['ref'],
        "rule_title": matched_rule['title'],
        "compliance": compliance,
        "recommendations": {
            "programs": rec_programs,
            "experts": rec_experts
        }
    })

# Save results
with open("compliance_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Compliance analysis complete. Results saved to compliance_results.json")

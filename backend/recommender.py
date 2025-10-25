"""
Recommendation engine module.
Matches regulatory gaps to QDB programs and compliance experts.
"""

import json
import pathlib
import logging
from typing import List, Dict
from rapidfuzz import fuzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for loaded resources
_resources_cache = None


def load_resources() -> Dict:
    """
    Load QDB programs and compliance experts from JSON file.

    Returns:
        Dictionary with 'qdb_programs' and 'compliance_experts' lists

    Raises:
        FileNotFoundError: If resources.json doesn't exist
        json.JSONDecodeError: If resources.json is invalid
    """
    global _resources_cache

    if _resources_cache is not None:
        return _resources_cache

    resources_path = pathlib.Path(__file__).parent / "data" / "resources.json"

    if not resources_path.exists():
        logger.error(f"Resources file not found at {resources_path}")
        raise FileNotFoundError(f"Resources file not found: {resources_path}")

    try:
        with open(resources_path, "r", encoding="utf-8") as f:
            _resources_cache = json.load(f)

        logger.info(
            f"Loaded {len(_resources_cache.get('qdb_programs', []))} programs "
            f"and {len(_resources_cache.get('compliance_experts', []))} experts"
        )
        return _resources_cache

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in resources file: {e}")
        raise


def recommend(gaps: List[Dict]) -> List[Dict]:
    """
    Generate recommendations based on identified gaps.

    Matching logic:
    - Data residency gaps -> Data residency expert
    - AML/CFT gaps -> AML workshop + AML expert
    - Compliance officer gaps -> Governance program + expert
    - Cybersecurity gaps -> Cybersecurity program + expert
    - Capital gaps -> Capital advisory program + expert
    - General governance gaps -> Corporate governance program

    Args:
        gaps: List of gap dictionaries with 'title', 'rule_ref', 'severity'

    Returns:
        List of recommendation dictionaries
    """
    resources = load_resources()
    programs = resources.get("qdb_programs", [])
    experts = resources.get("compliance_experts", [])

    recommendations = []
    matched_programs = set()
    matched_experts = set()

    for gap in gaps:
        title_lower = gap.get("title", "").lower()
        rule_ref = gap.get("rule_ref", "")
        severity = gap.get("severity", "low")

        gap_recommendations = {
            "gap_title": gap.get("title"),
            "gap_ref": rule_ref,
            "severity": severity,
            "programs": [],
            "experts": []
        }

        # Data residency matching
        if any(keyword in title_lower for keyword in ["data residency", "data storage", "data hosting", "cloud"]):
            expert = find_expert_by_specialization(experts, "Data Residency")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # AML/CFT matching
        if any(keyword in title_lower for keyword in ["aml", "anti-money laundering", "cft", "financing of terrorism"]):
            program = find_program_by_name(programs, "AML Compliance Workshop")
            if program and program["program_id"] not in matched_programs:
                gap_recommendations["programs"].append(program)
                matched_programs.add(program["program_id"])

            expert = find_expert_by_specialization(experts, "AML/CFT")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # Compliance officer / governance matching
        if any(keyword in title_lower for keyword in ["compliance officer", "governance", "board", "corporate structure"]):
            program = find_program_by_focus(programs, "Corporate Structure")
            if program and program["program_id"] not in matched_programs:
                gap_recommendations["programs"].append(program)
                matched_programs.add(program["program_id"])

            expert = find_expert_by_specialization(experts, "Corporate Governance")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # Cybersecurity matching
        if any(keyword in title_lower for keyword in ["cybersecurity", "security", "iso 27001", "penetration", "cyber"]):
            program = find_program_by_name(programs, "Cybersecurity Excellence")
            if program and program["program_id"] not in matched_programs:
                gap_recommendations["programs"].append(program)
                matched_programs.add(program["program_id"])

            expert = find_expert_by_specialization(experts, "Cybersecurity")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # Capital requirements matching
        if any(keyword in title_lower for keyword in ["capital", "financial", "funding", "paid-up"]):
            program = find_program_by_name(programs, "Capital Readiness")
            if program and program["program_id"] not in matched_programs:
                gap_recommendations["programs"].append(program)
                matched_programs.add(program["program_id"])

            expert = find_expert_by_specialization(experts, "Financial")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # Customer due diligence
        if any(keyword in title_lower for keyword in ["due diligence", "cdd", "customer verification", "kyc"]):
            expert = find_expert_by_specialization(experts, "AML/CFT")
            if expert and expert["expert_id"] not in matched_experts:
                gap_recommendations["experts"].append(expert)
                matched_experts.add(expert["expert_id"])

        # Add general regulatory accelerator for high severity gaps without specific matches
        if severity == "high" and not gap_recommendations["programs"] and not gap_recommendations["experts"]:
            program = find_program_by_name(programs, "Regulatory Accelerator")
            if program and program["program_id"] not in matched_programs:
                gap_recommendations["programs"].append(program)
                matched_programs.add(program["program_id"])

        # Only add if we found recommendations
        if gap_recommendations["programs"] or gap_recommendations["experts"]:
            recommendations.append(gap_recommendations)

    logger.info(f"Generated {len(recommendations)} recommendations for {len(gaps)} gaps")
    return recommendations


def find_program_by_name(programs: List[Dict], name_substring: str) -> Dict:
    """Find a program by partial name match."""
    for program in programs:
        if name_substring.lower() in program["program_name"].lower():
            return program
    return None


def find_program_by_focus(programs: List[Dict], focus_area: str) -> Dict:
    """Find a program by focus area."""
    for program in programs:
        for area in program.get("focus_areas", []):
            if focus_area.lower() in area.lower():
                return program
    return None


def find_expert_by_specialization(experts: List[Dict], specialization_substring: str) -> Dict:
    """Find an expert by partial specialization match."""
    for expert in experts:
        if specialization_substring.lower() in expert["specialization"].lower():
            return expert
    return None


def get_all_programs() -> List[Dict]:
    """Get all available QDB programs."""
    resources = load_resources()
    return resources.get("qdb_programs", [])


def get_all_experts() -> List[Dict]:
    """Get all available compliance experts."""
    resources = load_resources()
    return resources.get("compliance_experts", [])


def search_resources(query: str, threshold: int = 60) -> Dict:
    """
    Search programs and experts using fuzzy matching.

    Args:
        query: Search query
        threshold: Minimum similarity score (0-100)

    Returns:
        Dictionary with matching programs and experts
    """
    resources = load_resources()
    programs = resources.get("qdb_programs", [])
    experts = resources.get("compliance_experts", [])

    matching_programs = []
    matching_experts = []

    # Search programs
    for program in programs:
        score = max(
            fuzz.partial_ratio(query.lower(), program["program_name"].lower()),
            max([fuzz.partial_ratio(query.lower(), area.lower())
                 for area in program.get("focus_areas", [])] or [0])
        )
        if score >= threshold:
            matching_programs.append({**program, "match_score": score})

    # Search experts
    for expert in experts:
        score = max(
            fuzz.partial_ratio(query.lower(), expert["name"].lower()),
            fuzz.partial_ratio(query.lower(), expert["specialization"].lower())
        )
        if score >= threshold:
            matching_experts.append({**expert, "match_score": score})

    # Sort by match score
    matching_programs.sort(key=lambda x: x["match_score"], reverse=True)
    matching_experts.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "programs": matching_programs,
        "experts": matching_experts
    }

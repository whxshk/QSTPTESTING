"""
Compliance scoring module.
Calculates readiness scores based on STRENGTHS (reward points) and gaps (deduct points).
"""

from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strength quality points (ADDITIVE - rewards for what they have)
STRENGTH_POINTS = {
    "excellent": 15,  # Comprehensive, exceeds requirements
    "good": 12,       # Well-documented, meets requirements
    "adequate": 10    # Documented, meets minimum
}

# Gap severity points (DEDUCTIVE - but less harsh than before)
GAP_PENALTIES = {
    "high": 15,    # Critical missing (was 35)
    "medium": 10,  # Important needs work (was 20)
    "low": 5       # Minor improvement (was 10)
}


def compute_score(strengths: List[Dict], gaps: List[Dict]) -> int:
    """
    Calculate compliance readiness score based on STRENGTHS and gaps.

    NEW SCORING ALGORITHM:
    - Start at 0 points
    - ADD points for each strength based on quality
    - SUBTRACT points for each gap based on severity
    - Cap at 0-100

    This rewards startups for what they DO have, not just punishing for what's missing.

    Args:
        strengths: List of strength dictionaries with 'quality' field
        gaps: List of gap dictionaries with 'severity' field

    Returns:
        Score between 0 and 100
    """
    score = 0

    # ADD points for strengths
    strength_counts = {"excellent": 0, "good": 0, "adequate": 0}
    for strength in strengths:
        quality = strength.get("quality", "adequate").lower()

        if quality in STRENGTH_POINTS:
            points = STRENGTH_POINTS[quality]
            score += points
            strength_counts[quality] += 1
        else:
            logger.warning(f"Unknown strength quality: {quality}, treating as adequate")
            score += STRENGTH_POINTS["adequate"]
            strength_counts["adequate"] += 1

    # SUBTRACT points for gaps
    gap_counts = {"high": 0, "medium": 0, "low": 0}
    for gap in gaps:
        severity = gap.get("severity", "low").lower()

        if severity in GAP_PENALTIES:
            penalty = GAP_PENALTIES[severity]
            score -= penalty
            gap_counts[severity] += 1
        else:
            logger.warning(f"Unknown gap severity: {severity}, treating as low")
            score -= GAP_PENALTIES["low"]
            gap_counts["low"] += 1

    # Cap score at 0-100
    final_score = max(0, min(100, score))

    logger.info(
        f"Computed score: {final_score} | "
        f"Strengths: {len(strengths)} (Exc:{strength_counts['excellent']}, "
        f"Good:{strength_counts['good']}, Adeq:{strength_counts['adequate']}) | "
        f"Gaps: {len(gaps)} (High:{gap_counts['high']}, "
        f"Med:{gap_counts['medium']}, Low:{gap_counts['low']})"
    )

    return final_score


def get_score_grade(score: int) -> str:
    """
    Convert numerical score to letter grade.

    Args:
        score: Score between 0 and 100

    Returns:
        Letter grade (A, B, C, D, F)
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def get_score_category(score: int) -> str:
    """
    Get descriptive category for score.

    Args:
        score: Score between 0 and 100

    Returns:
        Category description
    """
    if score >= 85:
        return "Excellent Readiness"
    elif score >= 70:
        return "Good Readiness"
    elif score >= 55:
        return "Moderate Readiness"
    elif score >= 40:
        return "Limited Readiness"
    else:
        return "Insufficient Readiness"


def get_score_color(score: int) -> str:
    """
    Get color code for score visualization.

    Args:
        score: Score between 0 and 100

    Returns:
        Color name (green, yellow, orange, red)
    """
    if score >= 80:
        return "green"
    elif score >= 60:
        return "yellow"
    elif score >= 40:
        return "orange"
    else:
        return "red"


def needs_expert_review(score: int, gaps: List[Dict]) -> bool:
    """
    Determine if expert review is recommended.

    Expert review is recommended if:
    - Score is below 60, OR
    - There are any HIGH severity gaps

    Args:
        score: Compliance score
        gaps: List of identified gaps

    Returns:
        True if expert review is recommended
    """
    if score < 60:
        return True

    for gap in gaps:
        if gap.get("severity", "").lower() == "high":
            return True

    return False


def get_detailed_score_breakdown(strengths: List[Dict], gaps: List[Dict]) -> Dict:
    """
    Get detailed breakdown of score calculation.

    Args:
        strengths: List of identified strengths
        gaps: List of identified gaps

    Returns:
        Dictionary with detailed scoring breakdown
    """
    score = compute_score(strengths, gaps)

    breakdown = {
        "final_score": score,
        "strength_count": len(strengths),
        "gap_count": len(gaps),
        "strength_breakdown": {
            "excellent": {"count": 0, "points_per_item": STRENGTH_POINTS["excellent"], "total_points": 0},
            "good": {"count": 0, "points_per_item": STRENGTH_POINTS["good"], "total_points": 0},
            "adequate": {"count": 0, "points_per_item": STRENGTH_POINTS["adequate"], "total_points": 0}
        },
        "severity_breakdown": {
            "high": {"count": 0, "deduction_per_gap": GAP_PENALTIES["high"], "total_deduction": 0},
            "medium": {"count": 0, "deduction_per_gap": GAP_PENALTIES["medium"], "total_deduction": 0},
            "low": {"count": 0, "deduction_per_gap": GAP_PENALTIES["low"], "total_deduction": 0}
        },
        "grade": get_score_grade(score),
        "category": get_score_category(score),
        "color": get_score_color(score),
        "needs_expert_review": needs_expert_review(score, gaps)
    }

    # Calculate strength breakdown
    total_strength_points = 0
    for strength in strengths:
        quality = strength.get("quality", "adequate").lower()
        if quality in breakdown["strength_breakdown"]:
            breakdown["strength_breakdown"][quality]["count"] += 1
            points = STRENGTH_POINTS[quality]
            breakdown["strength_breakdown"][quality]["total_points"] += points
            total_strength_points += points

    # Calculate gap breakdown
    total_deductions = 0
    for gap in gaps:
        severity = gap.get("severity", "low").lower()
        if severity in breakdown["severity_breakdown"]:
            breakdown["severity_breakdown"][severity]["count"] += 1
            penalty = GAP_PENALTIES[severity]
            breakdown["severity_breakdown"][severity]["total_deduction"] += penalty
            total_deductions += penalty

    breakdown["total_strength_points"] = total_strength_points
    breakdown["total_deductions"] = total_deductions

    return breakdown

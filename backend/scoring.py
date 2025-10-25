"""
Compliance scoring module.
Calculates readiness scores based on identified regulatory gaps.
"""

from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scoring weights for different severity levels
SEVERITY_WEIGHTS = {
    "high": 35,
    "medium": 20,
    "low": 10
}

# Base score
BASE_SCORE = 100


def compute_score(gaps: List[Dict]) -> int:
    """
    Calculate compliance readiness score based on gaps.

    Scoring algorithm:
    - Start with 100 points
    - Deduct 35 points for each HIGH severity gap
    - Deduct 20 points for each MEDIUM severity gap
    - Deduct 10 points for each LOW severity gap
    - Minimum score is 0

    Args:
        gaps: List of gap dictionaries with 'severity' field

    Returns:
        Score between 0 and 100
    """
    score = BASE_SCORE

    severity_counts = {"high": 0, "medium": 0, "low": 0}

    for gap in gaps:
        severity = gap.get("severity", "low").lower()

        if severity in SEVERITY_WEIGHTS:
            deduction = SEVERITY_WEIGHTS[severity]
            score -= deduction
            severity_counts[severity] += 1
        else:
            logger.warning(f"Unknown severity level: {severity}, treating as low")
            score -= SEVERITY_WEIGHTS["low"]
            severity_counts["low"] += 1

    # Ensure score doesn't go below 0
    final_score = max(0, score)

    logger.info(
        f"Computed score: {final_score} "
        f"(High: {severity_counts['high']}, "
        f"Medium: {severity_counts['medium']}, "
        f"Low: {severity_counts['low']})"
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


def get_detailed_score_breakdown(gaps: List[Dict]) -> Dict:
    """
    Get detailed breakdown of score calculation.

    Args:
        gaps: List of identified gaps

    Returns:
        Dictionary with detailed scoring breakdown
    """
    score = compute_score(gaps)

    breakdown = {
        "base_score": BASE_SCORE,
        "final_score": score,
        "total_deductions": BASE_SCORE - score,
        "gap_count": len(gaps),
        "severity_breakdown": {
            "high": {"count": 0, "deduction_per_gap": SEVERITY_WEIGHTS["high"], "total_deduction": 0},
            "medium": {"count": 0, "deduction_per_gap": SEVERITY_WEIGHTS["medium"], "total_deduction": 0},
            "low": {"count": 0, "deduction_per_gap": SEVERITY_WEIGHTS["low"], "total_deduction": 0}
        },
        "grade": get_score_grade(score),
        "category": get_score_category(score),
        "color": get_score_color(score),
        "needs_expert_review": needs_expert_review(score, gaps)
    }

    # Calculate severity breakdown
    for gap in gaps:
        severity = gap.get("severity", "low").lower()
        if severity in breakdown["severity_breakdown"]:
            breakdown["severity_breakdown"][severity]["count"] += 1
            breakdown["severity_breakdown"][severity]["total_deduction"] += SEVERITY_WEIGHTS[severity]

    return breakdown

"""
Regulatory rules management module.
Loads and provides access to QCB regulatory requirements.
"""

import json
import pathlib
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for loaded rules
_rules_cache = None


def load_rules() -> List[Dict]:
    """
    Load QCB regulatory rules from JSON file.

    Returns:
        List of rule dictionaries

    Raises:
        FileNotFoundError: If rules.json doesn't exist
        json.JSONDecodeError: If rules.json is invalid
    """
    global _rules_cache

    if _rules_cache is not None:
        return _rules_cache

    rules_path = pathlib.Path(__file__).parent / "data" / "rules.json"

    if not rules_path.exists():
        logger.error(f"Rules file not found at {rules_path}")
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            _rules_cache = json.load(f)

        logger.info(f"Loaded {len(_rules_cache)} regulatory rules")
        return _rules_cache

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rules file: {e}")
        raise


def get_rules_text() -> str:
    """
    Get formatted text representation of all rules for LLM prompts.

    Returns:
        Formatted string with all rules
    """
    rules = load_rules()

    formatted = []
    for rule in rules:
        formatted.append(
            f"{rule['ref']}: {rule['title']}\n{rule['text']}"
        )

    return "\n\n".join(formatted)


def get_rule_by_ref(ref: str) -> Dict:
    """
    Get a specific rule by its reference code.

    Args:
        ref: Rule reference code (e.g., "QCB 2.1.1")

    Returns:
        Rule dictionary or None if not found
    """
    rules = load_rules()

    for rule in rules:
        if rule["ref"] == ref:
            return rule

    return None


def search_rules(keyword: str) -> List[Dict]:
    """
    Search rules by keyword in title or text.

    Args:
        keyword: Search term

    Returns:
        List of matching rules
    """
    rules = load_rules()
    keyword_lower = keyword.lower()

    matches = []
    for rule in rules:
        if (keyword_lower in rule["title"].lower() or
            keyword_lower in rule["text"].lower()):
            matches.append(rule)

    return matches


def get_rules_summary() -> dict:
    """
    Get summary statistics about loaded rules.

    Returns:
        Dictionary with rule statistics
    """
    rules = load_rules()

    # Extract categories from rule references
    categories = set()
    for rule in rules:
        # Extract category from ref like "QCB 2.1.1" -> "2"
        parts = rule["ref"].split()
        if len(parts) > 1:
            cat = parts[1].split(".")[0]
            categories.add(cat)

    return {
        "total_rules": len(rules),
        "categories": sorted(list(categories)),
        "refs": [r["ref"] for r in rules]
    }

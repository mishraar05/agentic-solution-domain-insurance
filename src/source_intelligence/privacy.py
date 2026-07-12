"""Privacy classification rules."""
from .naming import detect_personal_data


def classify_privacy(column_name: str) -> tuple:
    """Classify column privacy based on name patterns.
    Returns (privacy_class, rationale).
    """
    if detect_personal_data(column_name):
        return "PERSONAL_DATA", "Column name matches personal-data rule; privacy review required"
    return "INTERNAL", "Technical or business metadata; no direct PII detected by MVP rule"

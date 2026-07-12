"""Classify privacy from transparent column-name indicators.

The Source Intelligence workflow uses structural names rather than personal values to identify
privacy-relevant attributes. The public classifier returns both a governed
privacy class and a human-readable rationale. A personal-data classification
causes the workflow to skip value-level profiling and route the recommendation
to the Privacy Steward.
"""
from .naming import detect_personal_data


def classify_privacy(column_name: str) -> tuple:
    """Classify column privacy based on name patterns.
    Returns (privacy_class, rationale).
    """
    if detect_personal_data(column_name):
        return "PERSONAL_DATA", "Column name matches personal-data rule; privacy review required"
    return "INTERNAL", "Technical or business metadata; no direct PII detected by MVP rule"

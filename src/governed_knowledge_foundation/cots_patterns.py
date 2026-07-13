"""Represent authorized deterministic COTS-pattern evidence.

The current deterministic workflow contains no licensed product documentation
or semantic retrieval. The
public function therefore returns an explicit unavailable assessment unless a
small, authorized, versioned structured pattern is later configured. Keeping
the component unavailable is intentional: the confidence calculation records
the missing evidence instead of inventing a product match from model memory.
"""

def match_cots_pattern(table_name: str, column_name: str, value_hint=None) -> dict:
    """Match against authorized COTS patterns.
    Returns dict with match_strength, product, module, version, or NOT_AVAILABLE.
    """
    return {
        "match_strength": None,
        "availability": "NOT_AVAILABLE",
        "product": None,
        "module": None,
        "version": None,
        "reason": "COTS pattern matching deferred to Governed Knowledge Foundation; no knowledge packs loaded"
    }

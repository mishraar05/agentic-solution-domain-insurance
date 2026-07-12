"""Authorized structured COTS pattern matching (Phase 2 deterministic only)."""

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
        "reason": "COTS pattern matching deferred to Phase 3; no knowledge packs loaded"
    }

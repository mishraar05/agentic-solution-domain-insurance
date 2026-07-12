"""Portable loader and structural validator for expanded synthetic fixtures."""

import json
from pathlib import Path

from tests.schema_validator import validate_instance

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPOSITORY_ROOT / "data" / "synthetic" / "expanded_fixtures_v1.json"
SCHEMA_PATH = REPOSITORY_ROOT / "contracts" / "expanded_synthetic_fixtures.schema.json"
CATEGORIES = {
    "null_empty", "duplicate_identifiers", "missing_pk", "orphan_fk",
    "incompatible_types", "conflicting_signals", "unknown_column",
    "ambiguous_mapping", "personal_data", "prohibited_evidence",
    "date_boundary", "amount_boundary", "idempotency", "changed_input",
    "failure_retry",
}


def load_json(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"UTF-8 BOM is not permitted: {path}")
    return json.loads(raw.decode("utf-8"))


def validate_fixture_set(data):
    """Validate required structure without adding a runtime dependency."""
    assert data["schema_version"] == "1.0.0"
    assert data["set_name"] == "expanded_synthetic_fixtures_v1"
    fixtures = data["fixtures"]
    assert len(fixtures) >= 15
    ids = [fixture["fixture_id"] for fixture in fixtures]
    assert len(ids) == len(set(ids))
    assert {fixture["category"] for fixture in fixtures} == CATEGORIES
    for fixture in fixtures:
        assert set(fixture) == {"fixture_id", "category", "description", "target", "input", "expected"}
        assert fixture["input"]["tables"]
        assert fixture["expected"]["processing_action"] in {"ANALYZE", "REJECT"}
        assert fixture["expected"]["approval_state"] == "PROPOSED"
        table_names = {table["name"] for table in fixture["input"]["tables"]}
        assert fixture["target"]["table"] in table_names
    return data


def load_fixtures():
    schema = load_json(SCHEMA_PATH)
    data = load_json(FIXTURE_PATH)
    validate_instance(data, schema)
    return validate_fixture_set(data)["fixtures"]


def fixtures_by_id():
    return {fixture["fixture_id"]: fixture for fixture in load_fixtures()}

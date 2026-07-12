"""Unit checks for executable expanded synthetic fixtures."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from source_intelligence.naming import classify_naming
from source_intelligence.privacy import classify_privacy
from source_intelligence.quality import (
    column_values,
    get_column,
    get_table,
    has_duplicates,
    has_null_or_empty,
    orphan_values,
    relationship_columns,
    review_for_issues,
)
from source_intelligence.types import check_type_compatibility
from tests.fixture_loader import FIXTURE_PATH, SCHEMA_PATH, fixtures_by_id, load_fixtures, load_json
from tests.schema_validator import validate_instance


@pytest.fixture(scope="module")
def cases():
    return fixtures_by_id()


def test_fixture_and_schema_are_utf8_without_bom():
    assert not FIXTURE_PATH.read_bytes().startswith(b"\xef\xbb\xbf")
    assert not SCHEMA_PATH.read_bytes().startswith(b"\xef\xbb\xbf")
    assert load_json(FIXTURE_PATH)["schema_version"] == "1.0.0"
    assert load_json(SCHEMA_PATH)["$schema"].endswith("2020-12/schema")


def test_all_required_fixture_categories_load():
    fixtures = load_fixtures()
    assert len(fixtures) == 15
    assert len({fixture["category"] for fixture in fixtures}) == 15


def test_schema_rejects_incomplete_fixture_set():
    schema = load_json(SCHEMA_PATH)
    invalid = load_json(FIXTURE_PATH)
    invalid["fixtures"][0].pop("expected")
    with pytest.raises(AssertionError, match="missing required"):
        validate_instance(invalid, schema)


def test_null_and_empty_values_are_executable(cases):
    fixture = cases["F001"]
    table = get_table(fixture["input"]["tables"], fixture["target"]["table"])
    assert has_null_or_empty(column_values(table, fixture["target"]["column"]))


def test_duplicate_identifier_is_observed_from_rows(cases):
    fixture = cases["F002"]
    table = get_table(fixture["input"]["tables"], fixture["target"]["table"])
    assert has_duplicates(column_values(table, fixture["target"]["column"]))


def test_missing_primary_key_is_nullable_and_empty(cases):
    fixture = cases["F003"]
    table = get_table(fixture["input"]["tables"], fixture["target"]["table"])
    column = get_column(table, fixture["target"]["column"])
    assert column["nullable"] is True
    assert all(value is None for value in column_values(table, column["name"]))


def test_orphan_foreign_key_is_computed(cases):
    child, child_column, parent, parent_column = relationship_columns(cases["F004"])
    assert orphan_values(
        column_values(child, child_column["name"]),
        column_values(parent, parent_column["name"]),
    ) == ["SYN-MISSING"]


def test_relationship_type_mismatch_is_computed(cases):
    _, child_column, _, parent_column = relationship_columns(cases["F005"])
    assert child_column["physical_type"] != parent_column["physical_type"]


def test_name_type_contradiction_reduces_strength(cases):
    fixture = cases["F006"]
    table = get_table(fixture["input"]["tables"], fixture["target"]["table"])
    column = get_column(table, fixture["target"]["column"])
    strength = check_type_compatibility(column["physical_type"], column["name"])
    assert strength <= fixture["expected"]["type_strength_max"]


@pytest.mark.parametrize("fixture_id", ["F007", "F008"])
def test_unknown_and_ambiguous_patterns_remain_unresolved(cases, fixture_id):
    fixture = cases[fixture_id]
    _, concept, _, strength, _ = classify_naming(
        fixture["target"]["table"], fixture["target"]["column"]
    )
    assert concept is None
    assert strength < 0.75


def test_personal_data_fixture_routes_to_privacy(cases):
    fixture = cases["F009"]
    privacy_class, _ = classify_privacy(fixture["target"]["column"])
    reviewer, reason = review_for_issues(["PERSONAL_DATA_INDICATOR"], privacy_class)
    assert privacy_class == fixture["expected"]["privacy_class"]
    assert reviewer == fixture["expected"]["reviewer_role"]
    assert fixture["expected"]["review_reason_contains"] in reason


@pytest.mark.parametrize(
    "fixture_id,issues",
    [
        ("F001", ["NULL_OR_EMPTY_VALUE"]),
        ("F002", ["DUPLICATE_IDENTIFIER"]),
        ("F003", ["MISSING_PRIMARY_KEY"]),
        ("F004", ["ORPHAN_FOREIGN_KEY"]),
        ("F005", ["RELATIONSHIP_TYPE_MISMATCH"]),
        ("F006", ["NAME_TYPE_CONTRADICTION"]),
        ("F007", ["UNKNOWN_SEMANTIC_PATTERN"]),
        ("F008", ["AMBIGUOUS_SEMANTIC_PATTERN"]),
    ],
)
def test_machine_readable_expected_review_routing(cases, fixture_id, issues):
    expected = cases[fixture_id]["expected"]
    reviewer, reason = review_for_issues(issues)
    assert reviewer == expected["reviewer_role"]
    assert expected["review_reason_contains"] in reason

"""End-to-end validation of multi-record and policy edge-case fixtures."""

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from source_intelligence.policy import is_prohibited_evidence, reject_prohibited_evidence
from source_intelligence.quality import canonical_input_key, column_values, get_table
from tests.fixture_loader import fixtures_by_id


def test_boundary_values_are_real_and_parseable():
    cases = fixtures_by_id()
    dates = column_values(get_table(cases["F011"]["input"]["tables"], "policy_source"), "effective_date")
    amounts = column_values(get_table(cases["F012"]["input"]["tables"], "claim_source"), "claimed_amount")
    assert [date.fromisoformat(value) for value in dates] == [date(1900, 1, 1), date(9999, 12, 31)]
    assert [Decimal(value) for value in amounts] == [Decimal("0.00"), Decimal("9999999999.99")]


def test_same_input_has_same_idempotency_key():
    fixture = fixtures_by_id()["F013"]
    assert canonical_input_key(fixture["input"]["tables"]) == canonical_input_key(fixture["input"]["comparison_tables"])
    assert fixture["expected"]["idempotency"] == "SAME_INPUT_SAME_KEY"


def test_changed_input_has_new_key():
    fixture = fixtures_by_id()["F014"]
    assert canonical_input_key(fixture["input"]["tables"]) != canonical_input_key(fixture["input"]["comparison_tables"])
    assert fixture["expected"]["idempotency"] == "CHANGED_INPUT_NEW_KEY"


def test_retry_reuses_input_key_independent_of_attempt_status():
    fixture = fixtures_by_id()["F015"]
    first = canonical_input_key(fixture["input"]["tables"])
    second = canonical_input_key(fixture["input"]["tables"])
    assert first == second
    assert [attempt["status"] for attempt in fixture["input"]["run_attempts"]] == ["FAILED", "SUCCEEDED"]
    assert fixture["expected"]["idempotency"] == "RETRY_SAME_KEY"


def test_prohibited_value_is_rejected_and_never_leaks_to_output_or_logs():
    fixture = fixtures_by_id()["F010"]
    table = get_table(fixture["input"]["tables"], fixture["target"]["table"])
    values = column_values(table, fixture["target"]["column"])
    sentinel = values[0]
    captured_logs = []

    assert is_prohibited_evidence(fixture["target"]["column"], values)
    event = reject_prohibited_evidence(
        fixture["target"]["table"], fixture["target"]["column"], captured_logs.append
    )

    persisted_output = json.dumps(event, sort_keys=True)
    log_output = "\n".join(captured_logs)
    assert sentinel not in persisted_output
    assert sentinel not in log_output
    assert event["violation_type"] == "PROHIBITED_EVIDENCE"
    assert event["action_taken"] == "REJECTED_BEFORE_PROFILE"
    assert event["routed_to"] == "PRIVACY_STEWARD"
    assert event["sanitized_description"]

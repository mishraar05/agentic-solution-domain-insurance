"""Tests for the Lakehouse Monitoring profile-evidence adapter."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.lakehouse_monitoring_adapter import adapt_metric_row

CONTEXT = {"schema_version": "1.0.0", "run_id": "si_job_42", "artifact_version": "0.3.0",
           "engagement_id": "e", "source_system": "s", "source_table": "bronze_policy"}
NOW = "2026-07-13T00:00:00+00:00"


def _row(**overrides):
    row = {"column_name": "policy_status", "count": 1000, "num_nulls": 10,
           "distinct_count": 4, "min": "ACT", "max": "LAP",
           "frequent_items": [{"item": "ACT", "count": 700}, {"item": "CAN", "count": 150},
                              {"item": "EXP", "count": 100}, {"item": "LAP", "count": 40}]}
    row.update(overrides)
    return row


class TestAdapter:
    def test_internal_column_gets_all_evidence_types(self):
        records = adapt_metric_row(_row(), CONTEXT, "INTERNAL", NOW)
        types = {r["profile_type"] for r in records}
        assert types == {"NULL_RATE", "DISTINCT_COUNT", "MIN_MAX", "CONTROLLED_VALUES"}
        assert all("LAKEHOUSE_MONITORING" in r["minimization_rule"] for r in records)

    def test_personal_column_gets_counts_only(self):
        records = adapt_metric_row(_row(column_name="display_name"), CONTEXT,
                                   "PERSONAL_DATA", NOW)
        types = {r["profile_type"] for r in records}
        assert types == {"NULL_RATE", "DISTINCT_COUNT"}

    def test_k_anonymity_blocks_rare_values(self):
        row = _row(frequent_items=[{"item": "ACT", "count": 900},
                                   {"item": "RARE_VAL", "count": 2}])
        records = adapt_metric_row(row, CONTEXT, "INTERNAL", NOW, min_value_count=5)
        assert "CONTROLLED_VALUES" not in {r["profile_type"] for r in records}

    def test_high_cardinality_blocks_value_summary(self):
        records = adapt_metric_row(_row(distinct_count=5000), CONTEXT, "INTERNAL", NOW)
        assert "CONTROLLED_VALUES" not in {r["profile_type"] for r in records}

    def test_records_are_contract_valid_and_proposed(self):
        for record in adapt_metric_row(_row(), CONTEXT, "INTERNAL", NOW):
            assert record["approval_state"] == "PROPOSED"
            assert record["is_minimized"] is True
            assert record["observed_or_inferred"] == "OBSERVED"

    def test_key_map_override(self):
        row = {"col": "policy_status", "n": 100, "nulls": 0, "ndv": 3,
               "lo": "A", "hi": "C", "top": []}
        records = adapt_metric_row(row, CONTEXT, "INTERNAL", NOW, key_map={
            "column_name": "col", "row_count": "n", "null_count": "nulls",
            "distinct_count": "ndv", "min": "lo", "max": "hi", "frequent_items": "top"})
        assert {r["profile_type"] for r in records} == {"NULL_RATE", "DISTINCT_COUNT", "MIN_MAX"}

"""Unit tests for the data-dictionary Excel export builder."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.dictionary_export import build_workbook


def _record(table, column, pos, state="APPROVED"):
    return {
        "source_table": table, "source_column": column, "ordinal_position": pos,
        "physical_type": "StringType()", "nullable": True, "key_role": "NON_KEY",
        "proposed_business_name": column.title(), "ontology_concept_id": None,
        "domain": "Policy", "observed_or_inferred": "INFERRED",
        "privacy_class": "INTERNAL", "confidence_score": 0.9,
        "approval_state": state, "relationship_evidence": None,
        "assumptions": None, "open_question": None,
    }


class TestDictionaryExport:
    def test_approved_only_filters(self):
        records = [_record("bronze_policy", "a", 1), _record("bronze_policy", "b", 2, "PROPOSED")]
        wb, count = build_workbook(records, "src", "si_job_1", "0.3.0", approved_only=True)
        assert count == 1
        assert "bronze_policy" in wb.sheetnames

    def test_draft_mode_includes_all_with_watermark(self):
        records = [_record("bronze_policy", "a", 1, "PROPOSED")]
        wb, count = build_workbook(records, "src", "si_job_1", "0.3.0", approved_only=False)
        assert count == 1
        overview = wb["Overview"]
        statuses = [overview.cell(row=r, column=2).value for r in range(1, 9)]
        assert any(v and "DRAFT" in str(v) for v in statuses)

    def test_one_sheet_per_table_with_headers(self):
        records = [_record("bronze_policy", "a", 1), _record("bronze_claim", "b", 1)]
        wb, _ = build_workbook(records, "src", "si_job_1", "0.3.0")
        assert set(wb.sheetnames) == {"Overview", "bronze_policy", "bronze_claim"}
        assert wb["bronze_policy"].cell(row=1, column=1).value == "Column"
        assert wb["bronze_policy"].cell(row=2, column=1).value == "a"

    def test_traceability_metadata_present(self):
        wb, _ = build_workbook([_record("t", "a", 1)], "guidewire_pc", "si_job_9", "0.3.0")
        values = [wb["Overview"].cell(row=r, column=2).value for r in range(1, 9)]
        assert "guidewire_pc" in values and "si_job_9" in values

    def test_empty_approved_set_produces_overview_only(self):
        wb, count = build_workbook([_record("t", "a", 1, "PROPOSED")], "s", "si_job_1", "0.3.0")
        assert count == 0 and wb.sheetnames == ["Overview"]

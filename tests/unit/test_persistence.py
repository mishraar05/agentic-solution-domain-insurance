"""Tests for safe compatibility-table schema alignment planning."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.persistence import (
    LEGACY_CONFIDENCE_FIELDS,
    SchemaCompatibilityError,
    plan_existing_schema_alignment,
)


def test_phase2_extra_columns_are_excluded_from_legacy_order():
    incoming = {
        "run_id": "string",
        "source_table": "string",
        "confidence_score": "double",
        "evidence_coverage": "double",
        "naming_strength": "double",
        "type_strength": "double",
        "relationship_strength": "double",
    }
    existing = {
        "source_table": "string",
        "run_id": "string",
        "confidence_score": "double",
        "naming_strength": "double",
        "type_strength": "double",
        "relationship_strength": "double",
    }
    assert plan_existing_schema_alignment(incoming, existing) == [
        "source_table",
        "run_id",
        "confidence_score",
        "naming_strength",
        "type_strength",
        "relationship_strength",
    ]


def test_legacy_confidence_fields_match_phase1_contract():
    assert LEGACY_CONFIDENCE_FIELDS == (
        "naming_strength",
        "type_strength",
        "relationship_strength",
    )


def test_missing_existing_column_fails_before_write():
    with pytest.raises(SchemaCompatibilityError, match="missing"):
        plan_existing_schema_alignment(
            {"run_id": "string"},
            {"run_id": "string", "source_table": "string"},
        )


def test_type_mismatch_fails_before_write():
    with pytest.raises(SchemaCompatibilityError, match="types differ"):
        plan_existing_schema_alignment(
            {"confidence_score": "string"},
            {"confidence_score": "double"},
        )

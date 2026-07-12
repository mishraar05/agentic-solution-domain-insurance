"""Contract-validator coverage for schema features used by Phase 2."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.contract_validation import (
    ContractValidationError,
    validate_instance,
)


def test_min_items_is_enforced():
    with pytest.raises(ContractValidationError, match="at least 1"):
        validate_instance([], {"type": "array", "minItems": 1, "items": {"type": "string"}})


def test_typed_additional_properties_are_enforced():
    schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": {"type": "string"},
    }
    validate_instance({"pack": "1.0.0"}, schema)
    with pytest.raises(ContractValidationError, match="expected type"):
        validate_instance({"pack": 1}, schema)

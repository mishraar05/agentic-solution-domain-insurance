"""Reject prohibited evidence before inspection, profiling, or retention.

The policy helpers identify prohibited narrative, credential, connection, and
test-sentinel evidence. Rejection returns a contract-shaped sanitized audit
event containing only structural context and the action taken; raw values never
enter the event or log message. The event routes the exception to the Privacy
Steward without pretending that prohibited content was safely profiled.
"""

from datetime import datetime, timezone

PROHIBITED_COLUMNS = {"loss_narrative", "claim_narrative", "credentials", "connection_string"}


def is_prohibited_evidence(column_name, values):
    """Identify prohibited evidence without returning or logging raw values."""
    if column_name.lower() in PROHIBITED_COLUMNS:
        return True
    return any(isinstance(value, str) and value.startswith("FORBIDDEN_TEST_") for value in values)


def reject_prohibited_evidence(source_table, source_column, logger=None,
                               run_id="si_00000000T000000Z",
                               source_system="synthetic_fixture_source"):
    """Return a contract-shaped sanitized event; never accept raw values."""
    event = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "artifact_version": "1.0.0",
        "source_system": source_system,
        "source_table": source_table,
        "source_column": source_column,
        "evidence_class_attempted": "PROHIBITED_NARRATIVE",
        "violation_type": "PROHIBITED_EVIDENCE",
        "action_taken": "REJECTED_BEFORE_PROFILE",
        "sanitized_description": "Prohibited evidence rejected before inspection or retention.",
        "routed_to": "PRIVACY_STEWARD",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if logger is not None:
        logger("Policy violation recorded: prohibited evidence rejected before profile.")
    return event

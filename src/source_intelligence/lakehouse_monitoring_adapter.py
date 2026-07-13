"""Adapt Databricks Lakehouse Monitoring profile metrics into governed evidence.

Lakehouse Monitoring computes column profiles platform-natively and writes them
to Delta metric tables. Because monitoring profiles whole tables BEFORE any
privacy decision, this adapter applies the evidence policy on the way in:

- Counts (null rate, distinct count) pass for every column — they expose no values.
- MIN/MAX passes only for privacy-class INTERNAL columns.
- Frequent-item value summaries pass only for INTERNAL columns AND only when the
  k-anonymity rule holds: cardinality <= max_distinct and every emitted value
  occurs >= min_value_count times.

Every record is contract-validated (`profile_evidence.json`) before return and
carries a LAKEHOUSE_MONITORING producer tag in its minimization rule. Metric
column names vary by monitor version, so the caller may override KEY_MAP after
inspecting the actual metric table.
"""

from common.contract_validation import validate_records

PRODUCER_TAG = "LAKEHOUSE_MONITORING"

# Default mapping from adapter fields to monitor metric-table columns.
# Confirm against the deployed monitor's profile-metric table at runtime.
KEY_MAP = {
    "column_name": "column_name",
    "row_count": "count",
    "null_count": "num_nulls",
    "distinct_count": "distinct_count",
    "min": "min",
    "max": "max",
    "frequent_items": "frequent_items",
}


def _base(context, column_name, created_at):
    return {
        "schema_version": context["schema_version"],
        "run_id": context["run_id"],
        "artifact_version": context["artifact_version"],
        "engagement_id": context["engagement_id"],
        "source_system": context["source_system"],
        "source_table": context["source_table"],
        "source_column": column_name,
        "observed_or_inferred": "OBSERVED",
        "approval_state": "PROPOSED",
        "created_at": created_at,
    }


def adapt_metric_row(metric_row, context, privacy_class, created_at,
                     key_map=None, max_distinct=20, min_value_count=5):
    """Convert one monitor profile-metric row into governed evidence records."""
    keys = {**KEY_MAP, **(key_map or {})}
    column = metric_row[keys["column_name"]]
    row_count = metric_row.get(keys["row_count"])
    records = []

    null_count = metric_row.get(keys["null_count"])
    if null_count is not None and row_count:
        records.append({
            **_base(context, column, created_at),
            "profile_type": "NULL_RATE",
            "profile_value": f"{null_count / row_count:.4f}",
            "evidence_class": "AGGREGATE_PROFILE",
            "is_minimized": True,
            "minimization_rule": f"{PRODUCER_TAG}: count aggregate; no value content",
            "privacy_class": privacy_class,
        })

    distinct = metric_row.get(keys["distinct_count"])
    if distinct is not None:
        records.append({
            **_base(context, column, created_at),
            "profile_type": "DISTINCT_COUNT",
            "profile_value": str(int(distinct)),
            "evidence_class": "AGGREGATE_PROFILE",
            "is_minimized": True,
            "minimization_rule": f"{PRODUCER_TAG}: count aggregate; no value content",
            "privacy_class": privacy_class,
        })

    # Value-bearing metrics are gated by the privacy classification.
    if privacy_class == "INTERNAL":
        minimum, maximum = metric_row.get(keys["min"]), metric_row.get(keys["max"])
        if minimum is not None and maximum is not None:
            records.append({
                **_base(context, column, created_at),
                "profile_type": "MIN_MAX",
                "profile_value": f"{minimum}..{maximum}",
                "evidence_class": "AGGREGATE_PROFILE",
                "is_minimized": True,
                "minimization_rule": (
                    f"{PRODUCER_TAG}: range endpoints only; INTERNAL columns only"
                ),
                "privacy_class": privacy_class,
            })

        frequent = metric_row.get(keys["frequent_items"]) or []
        if frequent and distinct is not None and distinct <= max_distinct:
            eligible = [
                item for item in frequent
                if item.get("count", 0) >= min_value_count
            ]
            if eligible and len(eligible) == len(frequent):
                values = sorted(str(item["item"]) for item in eligible)
                records.append({
                    **_base(context, column, created_at),
                    "profile_type": "CONTROLLED_VALUES",
                    "profile_value": ",".join(values),
                    "evidence_class": "CONTROLLED_VALUE_SUMMARY",
                    "is_minimized": True,
                    "minimization_rule": (
                        f"{PRODUCER_TAG}: k-anonymity rule — cardinality <= "
                        f"{max_distinct} and every value count >= {min_value_count}"
                    ),
                    "privacy_class": privacy_class,
                })

    validate_records(records, "profile_evidence.json")
    return records

# Databricks notebook source
"""Build the complete deterministic Source Intelligence observation layer.

This producer reads physical schemas and governance-permitted aggregate
profiles from configured external source tables. Reusable rules from
``src/source_intelligence`` propose business names, ontology concepts, domains,
key roles, relationships, privacy classes, and transparent confidence scores.

Logical records are validated against their JSON contracts before any output
write. Observed physical metadata and inferred semantics remain explicitly
distinguishable, and every attribute retains an evidence reference. Personal-
data columns are classified from their names and are skipped before value-level
profiling; only permitted aggregate profiles for internal columns are retained.

Outputs are solution-owned recommendation records:
``source_observation_dictionary`` for Phase 1 compatibility,
``source_attribute_observation``, ``source_object_observation``,
``profile_evidence``, and ``relationship_candidate``. Writes are append-only,
scoped by ``run_id``, and retry-idempotent. Every recommendation remains
``PROPOSED`` and therefore non-authoritative until a human decision exists.

Run after ``01_validate_source_scope.py`` and before review routing.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 02 — Generate source-observation dictionary
# MAGIC
# MAGIC Deterministic Source Intelligence v1. All classification, confidence, and
# MAGIC privacy logic comes from the tested `source_intelligence` core — no embedded
# MAGIC rules. Records are validated against `contracts/source_attribute_observation.json`
# MAGIC before persistence and appended (never overwritten) scoped by `run_id`.
# MAGIC Retry-idempotent: existing rows for this run_id skip the write.

# COMMAND ----------

import json
from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType, BooleanType, DoubleType, IntegerType, StringType, StructField,
    StructType, TimestampType,
)

from source_intelligence.confidence import compute_confidence
from source_intelligence.contract_validation import validate_records
from source_intelligence.cots_patterns import match_cots_pattern
from source_intelligence.naming import classify_naming
from source_intelligence.privacy import classify_privacy
from source_intelligence.persistence import (
    LEGACY_CONFIDENCE_FIELDS,
    plan_existing_schema_alignment,
)
from source_intelligence.relationships import (
    KNOWN_RELATIONSHIPS, compute_relationship_strength, infer_key_role,
    infer_relationship,
)
from source_intelligence.types import check_type_compatibility

# COMMAND ----------

created_at = datetime.now(timezone.utc)
contract_records = []

for table_name in SOURCE_TABLES:
    source_schema = spark.table(fq_source_table(table_name)).schema
    for ordinal_position, field in enumerate(source_schema.fields, start=1):
        proposed_name, ontology_concept, domain, naming_strength, naming_reason = (
            classify_naming(table_name, field.name)
        )
        type_strength = check_type_compatibility(str(field.dataType), field.name)
        relation = infer_relationship(table_name, field.name)
        relationship_strength = compute_relationship_strength(
            table_name, field.name, relation is not None
        )
        cots = match_cots_pattern(table_name, field.name)
        privacy_class, privacy_rationale = classify_privacy(field.name)

        confidence = compute_confidence(
            naming_strength=naming_strength,
            type_strength=type_strength,
            relationship_strength=relationship_strength,
            cots_match_strength=cots["match_strength"],
            standard_consistency=None,  # standards knowledge pack deferred to Phase 3
        )

        assumptions = (
            None if ontology_concept
            else "Business meaning inferred from naming pattern; steward validation required."
        )
        contract_records.append({
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "artifact_version": ARTIFACT_VERSION,
            "engagement_id": ENGAGEMENT_ID,
            "source_system": SOURCE_SYSTEM,
            "source_table": table_name,
            "source_column": field.name,
            "ordinal_position": ordinal_position,
            "physical_type": str(field.dataType),
            "nullable": field.nullable,
            "key_role": infer_key_role(table_name, field.name),
            "relationship_evidence": relation,
            "proposed_business_name": proposed_name,
            "ontology_concept_id": ontology_concept,
            "domain": domain,
            "observed_or_inferred": "INFERRED",
            "evidence_references": [
                f"catalog_metadata:{SOURCE_CATALOG}.{SOURCE_SCHEMA}."
                f"{table_name}.{field.name}"
            ],
            "confidence_score": confidence.score,
            "confidence_components": confidence.components,
            "evidence_coverage": confidence.evidence_coverage,
            "confidence_reason": f"{naming_reason}; {confidence.confidence_reason}",
            "formula_version": confidence.formula_version,
            "assumptions": assumptions,
            "contradictions": None,
            "open_question": (
                None if confidence.score >= LOW_CONFIDENCE_THRESHOLD
                else "Confirm semantic meaning with data steward."
            ),
            "privacy_class": privacy_class,
            "privacy_rationale": privacy_rationale,
            "approval_state": "PROPOSED",
            "reviewer_role": None,
            "review_rationale": None,
            "created_at": created_at.isoformat(),
        })

# Contract enforcement BEFORE persistence — any violation aborts the write.
validated = validate_records(contract_records, "source_attribute_observation.json")
print(f"Contract validation passed for {validated} records")

# COMMAND ----------

# Physical serialization of the validated records: identical fields; nested
# confidence components -> JSON string, ISO timestamp -> native TIMESTAMP.
dictionary_schema = StructType([
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_table", StringType(), False),
    StructField("source_column", StringType(), False),
    StructField("ordinal_position", IntegerType(), False),
    StructField("physical_type", StringType(), False),
    StructField("nullable", BooleanType(), False),
    StructField("key_role", StringType(), False),
    StructField("relationship_evidence", StringType(), True),
    StructField("proposed_business_name", StringType(), False),
    StructField("ontology_concept_id", StringType(), True),
    StructField("domain", StringType(), False),
    StructField("observed_or_inferred", StringType(), False),
    StructField("evidence_references", ArrayType(StringType()), False),
    StructField("confidence_score", DoubleType(), False),
    StructField("confidence_components", StringType(), False),
    StructField("evidence_coverage", DoubleType(), False),
    StructField("confidence_reason", StringType(), False),
    StructField("formula_version", StringType(), False),
    StructField("assumptions", StringType(), True),
    StructField("contradictions", StringType(), True),
    StructField("open_question", StringType(), True),
    StructField("privacy_class", StringType(), False),
    StructField("privacy_rationale", StringType(), False),
    StructField("approval_state", StringType(), False),
    StructField("reviewer_role", StringType(), True),
    StructField("review_rationale", StringType(), True),
    StructField("created_at", TimestampType(), False),
])

field_order = [f.name for f in dictionary_schema.fields]
rows = [
    Row(**{name: (
        json.dumps(record["confidence_components"]) if name == "confidence_components"
        else created_at if name == "created_at"
        else record[name]
    ) for name in field_order})
    for record in contract_records
]

phase2_attributes_df = spark.createDataFrame(rows, schema=dictionary_schema)
dictionary_df = phase2_attributes_df.drop("evidence_references")
for legacy_field in LEGACY_CONFIDENCE_FIELDS:
    dictionary_df = dictionary_df.withColumn(
        legacy_field,
        F.get_json_object(
            F.col("confidence_components"),
            f"$.{legacy_field}.value",
        ).cast("double"),
    )


def _align_legacy_dictionary(frame, table_name):
    """Fit Phase 2 data to an existing Phase 1 dictionary without evolution."""
    if not spark.catalog.tableExists(table_name):
        return frame
    existing_schema = spark.table(table_name).schema
    incoming_types = {
        field.name: field.dataType.simpleString()
        for field in frame.schema.fields
    }
    existing_types = {
        field.name: field.dataType.simpleString()
        for field in existing_schema.fields
    }
    column_order = plan_existing_schema_alignment(
        incoming_types, existing_types
    )
    dropped = [
        name for name in incoming_types
        if name not in existing_types
    ]
    if dropped:
        print(
            "Phase 1 compatibility write excludes Phase 2-only columns: "
            f"{dropped}"
        )
    return frame.select(*column_order)

# Versioned persistence: append run-scoped records; history is never destroyed.
# Idempotency guard: a retry with the same run_id must not append duplicates.
_dict_table = fq_table("source_observation_dictionary")
_dict_exists = spark.catalog.tableExists(_dict_table)
_already_written = (
    _dict_exists
    and spark.table(_dict_table).filter(F.col("run_id") == RUN_ID).count() > 0
)
if _already_written:
    print(f"Idempotent skip: dictionary rows for run {RUN_ID} already exist.")
else:
    legacy_dictionary_df = _align_legacy_dictionary(
        dictionary_df, _dict_table
    )
    if _dict_exists:
        legacy_dictionary_df.write.mode("append").insertInto(_dict_table)
    else:
        (legacy_dictionary_df.write.format("delta").mode("append")
         .option("mergeSchema", "false")
         .saveAsTable(_dict_table))

_attribute_table = fq_table("source_attribute_observation")
_attributes_written = (
    spark.catalog.tableExists(_attribute_table)
    and spark.table(_attribute_table).filter(F.col("run_id") == RUN_ID).count() > 0
)
if _attributes_written:
    print(f"Idempotent skip: Phase 2 attributes for run {RUN_ID} already exist.")
else:
    (phase2_attributes_df.write.format("delta").mode("append")
     .option("mergeSchema", "false")
     .saveAsTable(_attribute_table))

# COMMAND ----------

# Object observations keep observed metadata references separate from the
# inferred domain and privacy roll-up.
object_records = []
for table_name in SOURCE_TABLES:
    attributes = [
        record for record in contract_records
        if record["source_table"] == table_name
    ]
    domain_counts = {}
    for attribute in attributes:
        domain = attribute["domain"]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    proposed_domain = sorted(
        domain_counts, key=lambda domain: (-domain_counts[domain], domain)
    )[0]
    privacy_class = (
        "PERSONAL_DATA"
        if any(a["privacy_class"] != "INTERNAL" for a in attributes)
        else "INTERNAL"
    )
    object_records.append({
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "artifact_version": ARTIFACT_VERSION,
        "engagement_id": ENGAGEMENT_ID,
        "source_system": SOURCE_SYSTEM,
        "source_table": table_name,
        "object_type": "TABLE",
        "column_count": len(attributes),
        "proposed_domain": proposed_domain,
        "proposed_domain_confidence": round(
            sum(a["confidence_score"] for a in attributes) / len(attributes), 4
        ),
        "cots_match_assessment": None,
        "profile_summary": None,
        "observed_or_inferred": "INFERRED",
        "evidence_references": [
            reference
            for attribute in attributes
            for reference in attribute["evidence_references"]
        ],
        "assumptions": "Object domain is inferred from deterministic attribute classifications.",
        "contradictions": None,
        "open_questions": None,
        "privacy_class": privacy_class,
        "privacy_rationale": (
            "Object contains at least one personal-data attribute name."
            if privacy_class != "INTERNAL"
            else "No personal-data attribute names detected."
        ),
        "approval_state": "PROPOSED",
        "reviewer_role": (
            "PRIVACY_STEWARD" if privacy_class != "INTERNAL" else None
        ),
        "review_rationale": None,
        "created_at": created_at.isoformat(),
    })
validate_records(object_records, "source_object_observation.json")

object_schema = StructType([
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_table", StringType(), False),
    StructField("object_type", StringType(), False),
    StructField("column_count", IntegerType(), False),
    StructField("row_count_estimate", IntegerType(), True),
    StructField("proposed_domain", StringType(), False),
    StructField("proposed_domain_confidence", DoubleType(), False),
    StructField("cots_match_assessment", StringType(), True),
    StructField("profile_summary", StringType(), True),
    StructField("observed_or_inferred", StringType(), False),
    StructField("evidence_references", ArrayType(StringType()), False),
    StructField("assumptions", StringType(), True),
    StructField("contradictions", StringType(), True),
    StructField("open_questions", StringType(), True),
    StructField("privacy_class", StringType(), False),
    StructField("privacy_rationale", StringType(), False),
    StructField("approval_state", StringType(), False),
    StructField("reviewer_role", StringType(), True),
    StructField("review_rationale", StringType(), True),
    StructField("created_at", TimestampType(), False),
])
object_fields = [field.name for field in object_schema.fields]
object_rows = [
    Row(**{
        name: created_at if name == "created_at" else record.get(name)
        for name in object_fields
    })
    for record in object_records
]
object_df = spark.createDataFrame(object_rows, object_schema)

# Relationship candidates use naming and physical-type compatibility only;
# value overlap stays unavailable until explicitly governed.
attribute_index = {
    (record["source_table"], record["source_column"]): record
    for record in contract_records
}
relationship_records = []
for (from_table, from_column), (to_table, to_column) in KNOWN_RELATIONSHIPS.items():
    source = attribute_index[(from_table, from_column)]
    target = attribute_index[(to_table, to_column)]
    compatible = source["physical_type"] == target["physical_type"]
    relationship_records.append({
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "artifact_version": ARTIFACT_VERSION,
        "engagement_id": ENGAGEMENT_ID,
        "source_system": SOURCE_SYSTEM,
        "from_table": from_table,
        "from_column": from_column,
        "to_table": to_table,
        "to_column": to_column,
        "relationship_type": "FOREIGN_KEY",
        "evidence_description": (
            "Deterministic identifier naming overlap and compatible physical types."
        ),
        "naming_overlap": True,
        "type_compatible": compatible,
        "overlap_ratio": None,
        "confidence_score": 0.9 if compatible else 0.6,
        "confidence_reason": (
            "Known naming relationship with compatible physical types."
            if compatible
            else "Known naming relationship with conflicting physical types."
        ),
        "observed_or_inferred": "INFERRED",
        "assumptions": "Referential integrity was not asserted from source values.",
        "contradictions": None if compatible else "Physical types are incompatible.",
        "approval_state": "PROPOSED",
        "reviewer_role": "DATA_ARCHITECT",
        "review_rationale": None,
        "created_at": created_at.isoformat(),
    })
validate_records(relationship_records, "relationship_candidate.json")

relationship_schema = StructType([
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("from_table", StringType(), False),
    StructField("from_column", StringType(), False),
    StructField("to_table", StringType(), False),
    StructField("to_column", StringType(), False),
    StructField("relationship_type", StringType(), False),
    StructField("evidence_description", StringType(), False),
    StructField("naming_overlap", BooleanType(), False),
    StructField("type_compatible", BooleanType(), False),
    StructField("overlap_ratio", DoubleType(), True),
    StructField("confidence_score", DoubleType(), False),
    StructField("confidence_reason", StringType(), False),
    StructField("observed_or_inferred", StringType(), False),
    StructField("assumptions", StringType(), True),
    StructField("contradictions", StringType(), True),
    StructField("approval_state", StringType(), False),
    StructField("reviewer_role", StringType(), True),
    StructField("review_rationale", StringType(), True),
    StructField("created_at", TimestampType(), False),
])
relationship_fields = [field.name for field in relationship_schema.fields]
relationship_rows = [
    Row(**{
        name: created_at if name == "created_at" else record.get(name)
        for name in relationship_fields
    })
    for record in relationship_records
]
relationship_df = spark.createDataFrame(relationship_rows, relationship_schema)

# Approved aggregate evidence only. Personal-data columns are never read.
profile_records = []
for record in contract_records:
    if record["privacy_class"] != "INTERNAL":
        continue
    source_df = spark.table(fq_source_table(record["source_table"]))
    column = F.col(f"`{record['source_column']}`")
    profile = source_df.agg(
        F.avg(column.isNull().cast("double")).alias("null_rate"),
        F.approx_count_distinct(column).alias("distinct_count"),
    ).first()
    for profile_type, profile_value in (
        (
            "NULL_RATE",
            "NOT_AVAILABLE"
            if profile.null_rate is None
            else str(round(profile.null_rate, 6)),
        ),
        ("DISTINCT_COUNT", str(profile.distinct_count)),
    ):
        profile_records.append({
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "artifact_version": ARTIFACT_VERSION,
            "engagement_id": ENGAGEMENT_ID,
            "source_system": SOURCE_SYSTEM,
            "source_table": record["source_table"],
            "source_column": record["source_column"],
            "profile_type": profile_type,
            "profile_value": profile_value,
            "evidence_class": "AGGREGATE_PROFILE",
            "is_minimized": True,
            "minimization_rule": "Aggregate only; no source values retained.",
            "observed_or_inferred": "OBSERVED",
            "privacy_class": "INTERNAL",
            "approval_state": "PROPOSED",
            "created_at": created_at.isoformat(),
        })
validate_records(profile_records, "profile_evidence.json")

profile_schema = StructType([
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_table", StringType(), False),
    StructField("source_column", StringType(), False),
    StructField("profile_type", StringType(), False),
    StructField("profile_value", StringType(), False),
    StructField("evidence_class", StringType(), False),
    StructField("is_minimized", BooleanType(), False),
    StructField("minimization_rule", StringType(), False),
    StructField("observed_or_inferred", StringType(), False),
    StructField("privacy_class", StringType(), False),
    StructField("approval_state", StringType(), False),
    StructField("created_at", TimestampType(), False),
])
profile_fields = [field.name for field in profile_schema.fields]
profile_rows = [
    Row(**{
        name: created_at if name == "created_at" else record.get(name)
        for name in profile_fields
    })
    for record in profile_records
]
profile_df = spark.createDataFrame(profile_rows, profile_schema)


def _append_once(frame, table_name):
    target = fq_table(table_name)
    already_written = (
        spark.catalog.tableExists(target)
        and spark.table(target).filter(F.col("run_id") == RUN_ID).count() > 0
    )
    if already_written:
        print(f"Idempotent skip: {table_name} for run {RUN_ID} already exists.")
    else:
        frame.write.format("delta").mode("append").saveAsTable(target)


_append_once(object_df, "source_object_observation")
_append_once(relationship_df, "relationship_candidate")
_append_once(profile_df, "profile_evidence")

display(
    dictionary_df.filter(F.col("run_id") == RUN_ID)
    .orderBy("source_table", "ordinal_position")
)

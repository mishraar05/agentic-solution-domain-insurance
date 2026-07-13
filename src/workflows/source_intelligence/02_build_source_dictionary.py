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
``source_observation_dictionary`` as a consumer-facing dictionary projection,
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
from source_intelligence.knowledge_classifier import (
    check_type_compatibility_kb,
    classify_naming_kb,
    classify_privacy_kb,
    provenance_references,
)
from source_intelligence.persistence import (
    DICTIONARY_PROJECTION_CONFIDENCE_FIELDS,
    plan_existing_schema_alignment,
)
from source_intelligence.relationships import (
    compute_relationship_strength,
    discover_relationship_candidates,
    infer_key_roles,
    relationship_evidence_by_attribute,
)

# COMMAND ----------

created_at = datetime.now(timezone.utc)
source_attributes = []

for table_name in SOURCE_TABLES:
    source_schema = spark.table(fq_source_table(table_name)).schema
    column_metadata = [
        {
            "name": field.name,
            "nullable": field.nullable,
            "ordinal_position": ordinal_position,
        }
        for ordinal_position, field in enumerate(source_schema.fields, start=1)
    ]
    key_roles = infer_key_roles(table_name, column_metadata)
    for ordinal_position, field in enumerate(source_schema.fields, start=1):
        source_attributes.append({
            "source_table": table_name,
            "source_column": field.name,
            "ordinal_position": ordinal_position,
            "physical_type": str(field.dataType),
            "nullable": field.nullable,
            "key_role": key_roles[field.name],
        })

relationship_candidates = discover_relationship_candidates(source_attributes)
relationship_evidence = relationship_evidence_by_attribute(
    relationship_candidates
)
candidates_by_attribute = {}
for candidate in relationship_candidates:
    key = (candidate["from_table"], candidate["from_column"])
    candidates_by_attribute.setdefault(key, []).append(candidate)

contract_records = []
for attribute in source_attributes:
    table_name = attribute["source_table"]
    column_name = attribute["source_column"]
    naming = classify_naming_kb(
        table_name,
        column_name,
        source_system=SOURCE_SYSTEM,
        naming_convention=NAMING_CONVENTION,
        effective_date=RULE_EFFECTIVE_DATE,
    )
    proposed_name = naming["proposed_business_name"]
    ontology_concept = naming["ontology_concept_id"]
    domain = naming["domain"]
    naming_strength = naming["naming_strength"]
    naming_reason = naming["reason"]
    type_strength, type_provenance = check_type_compatibility_kb(
        attribute["physical_type"],
        naming["ontology_concept_type"],
        source_system=SOURCE_SYSTEM,
        naming_convention=NAMING_CONVENTION,
        effective_date=RULE_EFFECTIVE_DATE,
    )
    attribute_candidates = candidates_by_attribute.get(
        (table_name, column_name), []
    )
    relation = relationship_evidence.get((table_name, column_name))
    relationship_strength = (
        max(candidate["confidence_score"] for candidate in attribute_candidates)
        if attribute_candidates
        else compute_relationship_strength(table_name, column_name, False)
    )
    relationship_contradictions = "; ".join(sorted({
        candidate["contradictions"]
        for candidate in attribute_candidates
        if candidate["contradictions"]
    })) or None
    cots = match_cots_pattern(table_name, column_name)
    privacy_class, privacy_rationale, privacy_provenance = (
        classify_privacy_kb(
            column_name,
            source_system=SOURCE_SYSTEM,
            naming_convention=NAMING_CONVENTION,
            effective_date=RULE_EFFECTIVE_DATE,
        )
    )
    contradictions = "; ".join(filter(None, [
        naming["contradictions"], relationship_contradictions,
    ])) or None
    rule_references = provenance_references(
        naming["provenance"] + type_provenance + privacy_provenance
    )

    confidence = compute_confidence(
        naming_strength=naming_strength,
        type_strength=type_strength,
        relationship_strength=relationship_strength,
        cots_match_strength=cots["match_strength"],
        standard_consistency=None,  # governed standards evidence unavailable
        naming_contradicted=naming["naming_contradicted"],
        relationship_contradicted=relationship_contradictions is not None,
    )

    assumptions = (
        None if ontology_concept else (
            "Deterministic semantics unresolved; closed-candidate semantic "
            "mapping or steward validation required."
        )
    )
    contract_records.append({
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "artifact_version": ARTIFACT_VERSION,
        "engagement_id": ENGAGEMENT_ID,
        "source_system": SOURCE_SYSTEM,
        "source_table": table_name,
        "source_column": column_name,
        "ordinal_position": attribute["ordinal_position"],
        "physical_type": attribute["physical_type"],
        "nullable": attribute["nullable"],
        "key_role": attribute["key_role"],
        "relationship_evidence": relation,
        "proposed_business_name": proposed_name,
        "ontology_concept_id": ontology_concept,
        "domain": domain,
        "observed_or_inferred": "INFERRED",
        "evidence_references": [
            f"catalog_metadata:{SOURCE_CATALOG}.{SOURCE_SCHEMA}."
            f"{table_name}.{column_name}",
            *rule_references,
        ],
        "confidence_score": confidence.score,
        "confidence_components": confidence.components,
        "evidence_coverage": confidence.evidence_coverage,
        "confidence_reason": f"{naming_reason}; {confidence.confidence_reason}",
        "formula_version": confidence.formula_version,
        "assumptions": assumptions,
        "contradictions": contradictions,
        "open_question": (
            "Resolve naming ambiguity using only the recorded ontology "
            "candidate set, or leave unresolved."
            if naming["naming_contradicted"] else (
                None if confidence.score >= LOW_CONFIDENCE_THRESHOLD
                else "Confirm semantic meaning with data steward."
            )
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

attribute_observations_df = spark.createDataFrame(rows, schema=dictionary_schema)
dictionary_df = attribute_observations_df.drop("evidence_references")
for projection_field in DICTIONARY_PROJECTION_CONFIDENCE_FIELDS:
    dictionary_df = dictionary_df.withColumn(
        projection_field,
        F.get_json_object(
            F.col("confidence_components"),
            f"$.{projection_field}.value",
        ).cast("double"),
    )


def _align_dictionary_projection(frame, table_name):
    """Fit canonical observations to the dictionary projection schema."""
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
            "Dictionary projection excludes canonical-only columns: "
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
    dictionary_projection_df = _align_dictionary_projection(
        dictionary_df, _dict_table
    )
    if _dict_exists:
        dictionary_projection_df.write.mode("append").insertInto(_dict_table)
    else:
        (dictionary_projection_df.write.format("delta").mode("append")
         .option("mergeSchema", "false")
         .saveAsTable(_dict_table))

_attribute_table = fq_table("source_attribute_observation")
_attributes_written = (
    spark.catalog.tableExists(_attribute_table)
    and spark.table(_attribute_table).filter(F.col("run_id") == RUN_ID).count() > 0
)
if _attributes_written:
    print(f"Idempotent skip: canonical attributes for run {RUN_ID} already exist.")
else:
    (attribute_observations_df.write.format("delta").mode("append")
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

# Relationship candidates use only current-run metadata; value overlap stays
# unavailable until explicitly governed.
relationship_records = []
for candidate in relationship_candidates:
    relationship_records.append({
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "artifact_version": ARTIFACT_VERSION,
        "engagement_id": ENGAGEMENT_ID,
        "source_system": SOURCE_SYSTEM,
        "from_table": candidate["from_table"],
        "from_column": candidate["from_column"],
        "to_table": candidate["to_table"],
        "to_column": candidate["to_column"],
        "relationship_type": "FOREIGN_KEY",
        "evidence_description": candidate["evidence_description"],
        "naming_overlap": candidate["naming_overlap"],
        "type_compatible": candidate["type_compatible"],
        "overlap_ratio": None,
        "confidence_score": candidate["confidence_score"],
        "confidence_reason": candidate["confidence_reason"],
        "observed_or_inferred": "INFERRED",
        "assumptions": "Referential integrity was not asserted from source values.",
        "contradictions": candidate["contradictions"],
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

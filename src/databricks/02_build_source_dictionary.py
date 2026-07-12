# Databricks notebook source
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
    BooleanType, DoubleType, IntegerType, StringType, StructField, StructType,
    TimestampType,
)

from source_intelligence.confidence import compute_confidence
from source_intelligence.contract_validation import validate_records
from source_intelligence.cots_patterns import match_cots_pattern
from source_intelligence.naming import classify_naming
from source_intelligence.privacy import classify_privacy
from source_intelligence.relationships import (
    compute_relationship_strength, infer_key_role, infer_relationship,
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

dictionary_df = spark.createDataFrame(rows, schema=dictionary_schema)

# Versioned persistence: append run-scoped records; history is never destroyed.
# Idempotency guard: a retry with the same run_id must not append duplicates.
_dict_table = fq_table("source_observation_dictionary")
_already_written = (
    spark.catalog.tableExists(_dict_table)
    and spark.table(_dict_table).filter(F.col("run_id") == RUN_ID).count() > 0
)
if _already_written:
    print(f"Idempotent skip: dictionary rows for run {RUN_ID} already exist.")
else:
    (dictionary_df.write.format("delta").mode("append")
     .option("mergeSchema", "false")
     .saveAsTable(_dict_table))

display(
    dictionary_df.filter(F.col("run_id") == RUN_ID)
    .orderBy("source_table", "ordinal_position")
)

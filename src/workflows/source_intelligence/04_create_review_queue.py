# Databricks notebook source
"""Route governed recommendations into the human review queue.

This workflow reads the current run's source-attribute and source-documentation
recommendations and applies deterministic routing policy.
Privacy findings, key and relationship candidates, contradictions, unmapped
concepts, insufficient evidence coverage, and low-confidence proposals are
assigned atomically to the appropriate reviewer role with a reason and
priority.

Each queue item is validated against ``contracts/review_queue_item.json``
before persistence. Queue items start as ``OPEN`` and never approve the source
recommendation. The stable ``queue_item_id`` links a later human decision to
exactly one recommendation. Re-running the same ``run_id`` does not append
duplicates.

Every LLM-assisted documentation recommendation is routed to a Domain Steward;
the model is never allowed to approve its output.

Run after ``03_generate_source_documentation.py`` and before workflow validation.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 04 — Create reviewer work queue
# MAGIC
# MAGIC Atomic routing via `source_intelligence.routing`; every queue item is validated
# MAGIC against `contracts/review_queue_item.json` before persistence. Writes are
# MAGIC retry-idempotent: if queue rows for this run already exist, the write is skipped.

# COMMAND ----------

import json
from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, StructField, StructType, TimestampType,
)

from source_intelligence.contract_validation import validate_records
from source_intelligence.persistence import plan_existing_schema_alignment
from source_intelligence.routing import route_review

# COMMAND ----------

# Idempotency guard: a retry with the same run_id must not append duplicates.
queue_table = fq_table("source_intelligence_review_queue")
already_written = (
    spark.catalog.tableExists(queue_table)
    and spark.table(queue_table).filter(F.col("run_id") == RUN_ID).count() > 0
)

# COMMAND ----------

if already_written:
    print(f"Idempotent skip: review_queue rows for run {RUN_ID} already exist.")
    review_queue = spark.table(queue_table).filter(F.col("run_id") == RUN_ID)
else:
    attribute_rows = (
        spark.table(fq_table("source_attribute_observation"))
        .filter(F.col("run_id") == RUN_ID)
        .collect()
    )
    assert attribute_rows, (
        f"No canonical attribute observations found for run {RUN_ID}."
    )
    documentation_rows = (
        spark.table(fq_table("source_documentation_recommendation"))
        .filter(F.col("run_id") == RUN_ID)
        .collect()
    )
    assert len(documentation_rows) == len(attribute_rows), (
        "Every canonical attribute must have one source-documentation "
        "recommendation before review routing."
    )
    attributes_by_key = {
        (row.source_table, row.source_column): row
        for row in attribute_rows
    }

    queued_at = datetime.now(timezone.utc)
    contract_items = []
    for row in attribute_rows:
        decision = route_review(
            confidence_score=row.confidence_score,
            evidence_coverage=row.evidence_coverage,
            privacy_class=row.privacy_class,
            relationship_evidence=row.relationship_evidence,
            ontology_concept_id=row.ontology_concept_id,
            key_role=row.key_role,
            contradictions=row.contradictions,
            evidence_coverage_floor=EVIDENCE_COVERAGE_FLOOR,
            low_confidence_threshold=LOW_CONFIDENCE_THRESHOLD,
        )
        if decision["review_reason"] is None:
            continue
        contract_items.append({
            "schema_version": SCHEMA_VERSION,
            "queue_item_id": f"{RUN_ID}:{row.source_table}:{row.source_column}",
            "run_id": row.run_id,
            "artifact_version": row.artifact_version,
            "engagement_id": row.engagement_id,
            "source_table": row.source_table,
            "source_column": row.source_column,
            "proposed_business_name": row.proposed_business_name,
            "domain": row.domain,
            "ontology_concept_id": row.ontology_concept_id,
            "key_role": row.key_role,
            "confidence_score": row.confidence_score,
            "evidence_coverage": row.evidence_coverage,
            "privacy_class": row.privacy_class,
            "review_trigger": decision["review_trigger"],
            "review_reason": decision["review_reason"],
            "review_priority": decision["review_priority"],
            "recommended_reviewer_role": decision["recommended_reviewer_role"],
            "queue_status": "OPEN",
            "assumptions": row.assumptions,
            "open_question": row.open_question,
            "queued_at": queued_at.isoformat(),
        })

    for documentation in documentation_rows:
        key = (documentation.source_table, documentation.source_column)
        attribute = attributes_by_key[key]
        material_documentation = json.dumps({
            "generation_status": documentation.generation_status,
            "column_description": documentation.proposed_column_description,
            "glossary_term": documentation.proposed_glossary_term,
            "glossary_definition": documentation.proposed_glossary_definition,
            "glossary_concept_id": (
                documentation.proposed_glossary_concept_id
            ),
            "context_fingerprint": documentation.context_fingerprint,
        }, sort_keys=True)
        contract_items.append({
            "schema_version": SCHEMA_VERSION,
            "queue_item_id": (
                f"{RUN_ID}:{documentation.source_table}:"
                f"{documentation.source_column}:source_documentation"
            ),
            "run_id": documentation.run_id,
            "artifact_version": documentation.artifact_version,
            "engagement_id": documentation.engagement_id,
            "source_table": documentation.source_table,
            "source_column": documentation.source_column,
            "proposed_business_name": (
                documentation.proposed_glossary_term
                or attribute.proposed_business_name
            ),
            "domain": attribute.domain,
            "ontology_concept_id": (
                documentation.proposed_glossary_concept_id
            ),
            "key_role": attribute.key_role,
            "confidence_score": attribute.confidence_score,
            "evidence_coverage": attribute.evidence_coverage,
            "privacy_class": attribute.privacy_class,
            "review_trigger": "SOURCE_DOCUMENTATION",
            "review_reason": (
                "LLM-assisted column description and business-glossary "
                "proposal requires Domain Steward review."
            ),
            "review_priority": (
                "HIGH" if documentation.generation_status == "UNRESOLVED"
                else "MEDIUM"
            ),
            "recommended_reviewer_role": "DOMAIN_STEWARD",
            "queue_status": "OPEN",
            "assumptions": material_documentation,
            "open_question": documentation.resolution_reason,
            "queued_at": queued_at.isoformat(),
        })

    # Contract enforcement BEFORE persistence.
    validated = validate_records(contract_items, "review_queue_item.json")
    print(f"Queue-item contract validation passed for {validated} records")

    queue_schema = StructType([
        StructField("schema_version", StringType(), False),
        StructField("queue_item_id", StringType(), False),
        StructField("run_id", StringType(), False),
        StructField("artifact_version", StringType(), False),
        StructField("engagement_id", StringType(), False),
        StructField("source_table", StringType(), False),
        StructField("source_column", StringType(), False),
        StructField("proposed_business_name", StringType(), False),
        StructField("domain", StringType(), False),
        StructField("ontology_concept_id", StringType(), True),
        StructField("key_role", StringType(), False),
        StructField("confidence_score", DoubleType(), False),
        StructField("evidence_coverage", DoubleType(), False),
        StructField("privacy_class", StringType(), False),
        StructField("review_trigger", StringType(), False),
        StructField("review_reason", StringType(), False),
        StructField("review_priority", StringType(), False),
        StructField("recommended_reviewer_role", StringType(), False),
        StructField("queue_status", StringType(), False),
        StructField("assumptions", StringType(), True),
        StructField("open_question", StringType(), True),
        StructField("queued_at", TimestampType(), False),
    ])
    # Physical serialization of the validated logical record: identical fields;
    # ISO timestamp string -> native TIMESTAMP.
    rows = [Row(**{**item, "queued_at": queued_at}) for item in contract_items]
    review_queue = spark.createDataFrame(rows, schema=queue_schema)
    review_queue.write.format("delta").mode("append").saveAsTable(queue_table)

# Preserve the consumer-facing queue projection without evolving its physical
# schema. Governed review consumers use source_intelligence_review_queue.
queue_projection_table = fq_table("review_queue")
queue_projection_exists = spark.catalog.tableExists(queue_projection_table)
queue_projection_written = (
    queue_projection_exists
    and spark.table(queue_projection_table)
    .filter(F.col("run_id") == RUN_ID)
    .count() > 0
)
if not queue_projection_written:
    queue_projection_df = review_queue
    if queue_projection_exists:
        incoming_types = {
            field.name: field.dataType.simpleString()
            for field in queue_projection_df.schema.fields
        }
        existing_types = {
            field.name: field.dataType.simpleString()
            for field in spark.table(queue_projection_table).schema.fields
        }
        column_order = plan_existing_schema_alignment(
            incoming_types, existing_types
        )
        queue_projection_df = queue_projection_df.select(*column_order)
        queue_projection_df.write.mode("append").insertInto(queue_projection_table)
    else:
        queue_projection_df.write.format("delta").mode("append").saveAsTable(
            queue_projection_table
        )

display(review_queue.orderBy("review_priority", "recommended_reviewer_role", "source_table"))

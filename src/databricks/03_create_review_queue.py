# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 03 — Create reviewer work queue
# MAGIC
# MAGIC Atomic routing via `source_intelligence.routing`; every queue item is validated
# MAGIC against `contracts/review_queue_item.json` before persistence. Writes are
# MAGIC retry-idempotent: if queue rows for this run already exist, the write is skipped.

# COMMAND ----------

from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, StructField, StructType, TimestampType,
)

from source_intelligence.contract_validation import validate_records
from source_intelligence.routing import route_review

# COMMAND ----------

# Idempotency guard: a retry with the same run_id must not append duplicates.
queue_table = fq_table("review_queue")
already_written = (
    spark.catalog.tableExists(queue_table)
    and spark.table(queue_table).filter(F.col("run_id") == RUN_ID).count() > 0
)

# COMMAND ----------

if already_written:
    print(f"Idempotent skip: review_queue rows for run {RUN_ID} already exist.")
    review_queue = spark.table(queue_table).filter(F.col("run_id") == RUN_ID)
else:
    dictionary_rows = (
        spark.table(fq_table("source_observation_dictionary"))
        .filter(F.col("run_id") == RUN_ID)
        .collect()
    )
    assert dictionary_rows, f"No dictionary records found for run {RUN_ID}."

    queued_at = datetime.now(timezone.utc)
    contract_items = []
    for row in dictionary_rows:
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

display(review_queue.orderBy("review_priority", "recommended_reviewer_role", "source_table"))

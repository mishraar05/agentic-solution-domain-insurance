# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 03 — Create reviewer work queue
# MAGIC
# MAGIC Atomic routing via the tested `source_intelligence.routing` core: one decision
# MAGIC per record carrying trigger, reason, reviewer, and priority (no reason/reviewer
# MAGIC disagreement). Key candidates always reach the Data Architect. Queue rows are
# MAGIC appended run-scoped with a stable `queue_item_id` so review decisions can link
# MAGIC back to exactly one item.

# COMMAND ----------

import json
from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, StructField, StructType, TimestampType,
)

from source_intelligence.routing import route_review

# COMMAND ----------

dictionary_rows = (
    spark.table(fq_table("source_observation_dictionary"))
    .filter(F.col("run_id") == RUN_ID)
    .collect()
)
assert dictionary_rows, f"No dictionary records found for run {RUN_ID}."

queued_at = datetime.now(timezone.utc)
queue_rows = []
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
    queue_rows.append(Row(
        queue_item_id=f"{RUN_ID}:{row.source_table}:{row.source_column}",
        engagement_id=row.engagement_id,
        source_table=row.source_table,
        source_column=row.source_column,
        proposed_business_name=row.proposed_business_name,
        domain=row.domain,
        ontology_concept_id=row.ontology_concept_id,
        key_role=row.key_role,
        confidence_score=row.confidence_score,
        evidence_coverage=row.evidence_coverage,
        privacy_class=row.privacy_class,
        review_trigger=decision["review_trigger"],
        review_reason=decision["review_reason"],
        review_priority=decision["review_priority"],
        recommended_reviewer_role=decision["recommended_reviewer_role"],
        queue_status="OPEN",
        assumptions=row.assumptions,
        open_question=row.open_question,
        run_id=row.run_id,
        artifact_version=row.artifact_version,
        queued_at=queued_at,
    ))

queue_schema = StructType([
    StructField("queue_item_id", StringType(), False),
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
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("queued_at", TimestampType(), False),
])

review_queue = spark.createDataFrame(queue_rows, schema=queue_schema)
# Versioned persistence: append run-scoped queue; prior queues are retained.
review_queue.write.format("delta").mode("append").saveAsTable(fq_table("review_queue"))

display(review_queue.orderBy("review_priority", "recommended_reviewer_role", "source_table"))

# Databricks notebook source
"""Record one explicit human decision for an open review-queue item.

This optional workbench entry point runs after the core Source Intelligence job
has created ``review_queue`` records. A human reviewer supplies a queue item,
their governed role, a decision, and mandatory rationale through Databricks
widgets. The deterministic lifecycle service verifies role authorization,
requires targeted invalidation for modifications, fingerprints the material
recommendation, and creates a contract-valid decision linked to exactly one
queue item.

The notebook never chooses a decision or rationale for the reviewer and is not
part of the automated core job. It persists an append-only decision event and
does not rewrite source data, recommendation history, or the original queue
record. Repeating the same logical decision is idempotent.

Required widgets
----------------
``queue_item_id``, ``reviewer_role``, ``reviewer_decision``, and
``reviewer_rationale``. ``invalidation_impact`` is required when the decision is
``MODIFIED`` and otherwise optional.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType, TimestampType

from common.contract_validation import validate_records
from source_intelligence.review_lifecycle import create_review_decision

# COMMAND ----------

dbutils.widgets.text("queue_item_id", "")
dbutils.widgets.dropdown(
    "reviewer_role",
    "DOMAIN_STEWARD",
    ["DATA_ARCHITECT", "DOMAIN_STEWARD", "PRIVACY_STEWARD"],
)
dbutils.widgets.dropdown(
    "reviewer_decision",
    "DEFERRED",
    ["APPROVED", "MODIFIED", "REJECTED", "DEFERRED"],
)
dbutils.widgets.text("reviewer_rationale", "")
dbutils.widgets.text("invalidation_impact", "")

queue_item_id = dbutils.widgets.get("queue_item_id").strip()
reviewer_role = dbutils.widgets.get("reviewer_role").strip()
reviewer_decision = dbutils.widgets.get("reviewer_decision").strip()
reviewer_rationale = dbutils.widgets.get("reviewer_rationale").strip()
invalidation_impact = dbutils.widgets.get("invalidation_impact").strip() or None

assert queue_item_id, "queue_item_id is required."
assert reviewer_rationale, "reviewer_rationale is required."

# COMMAND ----------

queue_table = fq_output_table("source_intelligence_review_queue")
matches = (
    spark.table(queue_table)
    .filter(F.col("queue_item_id") == queue_item_id)
    .collect()
)
assert len(matches) == 1, (
    f"Expected exactly one review_queue row for {queue_item_id!r}; "
    f"found {len(matches)}."
)

queue_item = matches[0].asDict(recursive=True)
queued_at = queue_item["queued_at"]
queue_item["queued_at"] = (
    queued_at.astimezone(timezone.utc).isoformat()
    if queued_at.tzinfo
    else queued_at.replace(tzinfo=timezone.utc).isoformat()
)

decided_at = datetime.now(timezone.utc)
decision = create_review_decision(
    queue_item=queue_item,
    reviewer_role=reviewer_role,
    reviewer_decision=reviewer_decision,
    reviewer_rationale=reviewer_rationale,
    decided_at=decided_at.isoformat(),
    invalidation_impact=invalidation_impact,
)
validate_records([decision], "review_decision.json")

# COMMAND ----------

decision_schema = StructType([
    StructField("decision_id", StringType(), False),
    StructField("queue_item_id", StringType(), False),
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("source_table", StringType(), False),
    StructField("source_column", StringType(), False),
    StructField("recommendation_type", StringType(), False),
    StructField("review_reason", StringType(), False),
    StructField("recommended_reviewer_role", StringType(), False),
    StructField("reviewer_role", StringType(), False),
    StructField("reviewer_decision", StringType(), False),
    StructField("reviewer_rationale", StringType(), False),
    StructField("prior_recommendation_version", StringType(), False),
    StructField("recommendation_fingerprint", StringType(), False),
    StructField("invalidation_impact", StringType(), True),
    StructField("queue_status", StringType(), False),
    StructField("decided_at", TimestampType(), False),
    StructField("queued_at", TimestampType(), False),
])
field_names = [field.name for field in decision_schema.fields]
physical_values = {
    **decision,
    "decided_at": decided_at,
    "queued_at": queued_at,
}
decision_row = Row(**{
    name: physical_values.get(name)
    for name in field_names
})
decision_df = spark.createDataFrame([decision_row], decision_schema)

decision_table = fq_output_table("review_decision")
already_written = (
    spark.catalog.tableExists(decision_table)
    and spark.table(decision_table)
    .filter(F.col("decision_id") == decision["decision_id"])
    .count() > 0
)
if already_written:
    print(f"Idempotent skip: decision {decision['decision_id']} already exists.")
else:
    decision_df.write.format("delta").mode("append").saveAsTable(decision_table)
    print(f"Recorded human decision {decision['decision_id']}.")

display(decision_df)

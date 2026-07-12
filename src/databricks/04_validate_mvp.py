# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 04 — Validate Source Intelligence outputs
# MAGIC
# MAGIC Configured source tables are external read-only prerequisites. Only the
# MAGIC dictionary and review queue are solution-owned outputs.

# COMMAND ----------

from pyspark.sql import functions as F

existing_source_tables = {
    row.tableName
    for row in spark.sql(
        f"SHOW TABLES IN `{SOURCE_CATALOG}`.`{SOURCE_SCHEMA}`"
    ).collect()
    if not row.isTemporary
}
missing_inputs = set(SOURCE_TABLES) - existing_source_tables
assert not missing_inputs, f"Missing configured source inputs: {sorted(missing_inputs)}"

required_outputs = {"source_observation_dictionary", "review_queue"}
existing_outputs = {
    row.tableName
    for row in spark.sql(
        f"SHOW TABLES IN `{OUTPUT_CATALOG}`.`{OUTPUT_SCHEMA}`"
    ).collect()
    if not row.isTemporary
}
missing_outputs = required_outputs - existing_outputs
assert not missing_outputs, f"Missing recommendation outputs: {sorted(missing_outputs)}"

dictionary = spark.table(fq_output_table("source_observation_dictionary"))
queue = spark.table(fq_output_table("review_queue"))

assert dictionary.count() > 0, "Source observation dictionary is empty."
assert dictionary.filter(F.col("confidence_score").isNull()).count() == 0, "Every record needs a confidence score."
assert dictionary.filter(F.col("approval_state") != "PROPOSED").count() == 0, "The solution must not auto-approve recommendations."
assert queue.filter(F.col("queue_status") != "OPEN").count() == 0, "The review queue should contain open work only."

summary = {
    "run_id": RUN_ID,
    "configured_source_tables": len(SOURCE_TABLES),
    "dictionary_rows": dictionary.count(),
    "review_queue_rows": queue.count(),
    "low_confidence_rows": dictionary.filter(F.col("confidence_score") < LOW_CONFIDENCE_THRESHOLD).count(),
    "personal_data_rows": dictionary.filter(F.col("privacy_class") != "INTERNAL").count(),
}

print("Source Intelligence validation passed")
for key, value in summary.items():
    print(f"{key}: {value}")

display(
    dictionary.groupBy("domain", "approval_state")
    .count()
    .orderBy("domain", "approval_state")
)

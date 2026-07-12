# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 04 — Validate MVP outputs

# COMMAND ----------

from pyspark.sql import functions as F

required_tables = {
    "bronze_policy",
    "bronze_policyholder",
    "bronze_claim",
    "source_observation_dictionary",
    "review_queue",
}

existing_tables = {
    row.tableName
    for row in spark.sql(f"SHOW TABLES IN `{CATALOG}`.`{SCHEMA}`").collect()
    if not row.isTemporary
}
missing = required_tables - existing_tables
assert not missing, f"Missing required tables: {sorted(missing)}"

dictionary = spark.table(fq_table("source_observation_dictionary"))
queue = spark.table(fq_table("review_queue"))

assert dictionary.count() > 0, "Source observation dictionary is empty."
assert dictionary.filter(F.col("confidence_score").isNull()).count() == 0, "Every record needs a confidence score."
assert dictionary.filter(F.col("approval_state") != "PROPOSED").count() == 0, "MVP should not auto-approve recommendations."
assert queue.filter(F.col("queue_status") != "OPEN").count() == 0, "MVP review queue should contain open work only."

summary = {
    "run_id": RUN_ID,
    "dictionary_rows": dictionary.count(),
    "review_queue_rows": queue.count(),
    "low_confidence_rows": dictionary.filter(F.col("confidence_score") < LOW_CONFIDENCE_THRESHOLD).count(),
    "personal_data_rows": dictionary.filter(F.col("privacy_class") != "INTERNAL").count(),
}

print("MVP validation passed")
for key, value in summary.items():
    print(f"{key}: {value}")

display(
    dictionary.groupBy("domain", "approval_state")
    .count()
    .orderBy("domain", "approval_state")
)

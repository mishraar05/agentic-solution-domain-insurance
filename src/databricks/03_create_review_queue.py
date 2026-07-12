# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 03 — Create reviewer work queue
# MAGIC
# MAGIC The queue makes uncertainty visible. It does not approve or change any recommendation automatically.

# COMMAND ----------

from datetime import datetime, timezone
from pyspark.sql import functions as F

dictionary = spark.table(fq_table("source_observation_dictionary"))

review_queue = (
    dictionary
    .withColumn(
        "review_reason",
        F.when(F.col("privacy_class") != "INTERNAL", F.lit("Privacy classification requires review"))
         .when(F.col("confidence_score") < F.lit(LOW_CONFIDENCE_THRESHOLD), F.lit("Confidence below configured threshold"))
         .when(F.col("ontology_concept_id").isNull(), F.lit("No approved ontology concept mapped"))
         .when(F.col("relationship_evidence").isNotNull(), F.lit("Inferred relationship requires confirmation"))
    )
    .filter(F.col("review_reason").isNotNull())
    .withColumn(
        "recommended_reviewer_role",
        F.when(F.col("privacy_class") != "INTERNAL", F.lit("PRIVACY_STEWARD"))
         .when(F.col("relationship_evidence").isNotNull(), F.lit("DATA_ARCHITECT"))
         .otherwise(F.lit("DOMAIN_STEWARD"))
    )
    .withColumn("queue_status", F.lit("OPEN"))
    .withColumn("queued_at", F.lit(datetime.now(timezone.utc)))
    .select(
        "source_table", "source_column", "proposed_business_name", "domain",
        "ontology_concept_id", "confidence_score", "privacy_class",
        "review_reason", "recommended_reviewer_role", "queue_status",
        "assumptions", "open_question", "run_id", "queued_at",
    )
)

review_queue.write.format("delta").mode("overwrite").saveAsTable(fq_table("review_queue"))

display(review_queue.orderBy("recommended_reviewer_role", "source_table", "source_column"))

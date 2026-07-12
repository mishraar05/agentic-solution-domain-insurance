# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — MVP configuration
# MAGIC
# MAGIC This project uses synthetic data only. Do not add client data, PII, proprietary documentation, or credentials to this Free Edition MVP.

# COMMAND ----------

from datetime import datetime, timezone

# Change these only if your Databricks workspace uses a different catalog or schema.
CATALOG = "workspace"
SCHEMA = "agentic_insurance_mvp"

RUN_ID = datetime.now(timezone.utc).strftime("mvp_%Y%m%dT%H%M%SZ")
ARTIFACT_VERSION = "0.1.0"
LOW_CONFIDENCE_THRESHOLD = 0.75


def fq_table(table_name: str) -> str:
    """Return a safely quoted three-part Unity Catalog table name."""
    return f"`{CATALOG}`.`{SCHEMA}`.`{table_name}`"


spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`")

print(f"Run ID: {RUN_ID}")
print(f"Working schema: {CATALOG}.{SCHEMA}")

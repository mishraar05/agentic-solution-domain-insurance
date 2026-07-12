# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Source Intelligence configuration
# MAGIC
# MAGIC The core solution consumes existing source-aligned tables. It never creates,
# MAGIC overwrites, ingests, or populates Bronze/source data.

# COMMAND ----------

from datetime import datetime, timezone

# Existing source tables supplied by the client/platform data pipeline.
SOURCE_CATALOG = "workspace"
SOURCE_SCHEMA = "agentic_insurance_demo_bronze"
SOURCE_TABLES = ("bronze_policy", "bronze_policyholder", "bronze_claim")
SOURCE_SYSTEM = "configured_source_system"

# Solution-owned recommendation artifacts. Source and output locations may differ.
OUTPUT_CATALOG = "workspace"
OUTPUT_SCHEMA = "agentic_insurance_mvp"

# Compatibility aliases for notebooks that only write recommendation artifacts.
CATALOG = OUTPUT_CATALOG
SCHEMA = OUTPUT_SCHEMA

RUN_ID = datetime.now(timezone.utc).strftime("si_%Y%m%dT%H%M%SZ")
ARTIFACT_VERSION = "0.2.0"
LOW_CONFIDENCE_THRESHOLD = 0.75


def _quoted_table(catalog: str, schema: str, table_name: str) -> str:
    """Return a safely quoted three-part Unity Catalog table name."""
    return f"`{catalog}`.`{schema}`.`{table_name}`"


def fq_source_table(table_name: str) -> str:
    """Return a configured, read-only source table name."""
    return _quoted_table(SOURCE_CATALOG, SOURCE_SCHEMA, table_name)


def fq_output_table(table_name: str) -> str:
    """Return a solution-owned recommendation table name."""
    return _quoted_table(OUTPUT_CATALOG, OUTPUT_SCHEMA, table_name)


def fq_table(table_name: str) -> str:
    """Compatibility alias for recommendation output tables."""
    return fq_output_table(table_name)


spark.sql(
    f"CREATE SCHEMA IF NOT EXISTS `{OUTPUT_CATALOG}`.`{OUTPUT_SCHEMA}`"
)

print(f"Run ID: {RUN_ID}")
print(f"Read-only source scope: {SOURCE_CATALOG}.{SOURCE_SCHEMA} {SOURCE_TABLES}")
print(f"Recommendation output schema: {OUTPUT_CATALOG}.{OUTPUT_SCHEMA}")

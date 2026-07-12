# Databricks notebook source
"""Perform the read-only preflight for configured source tables.

This is the first operational workflow step after shared configuration. It
lists tables in the configured source schema, confirms that every requested
table exists, and verifies that each table exposes at least one column.

The notebook reads only catalog metadata and Spark schemas. It never creates,
loads, modifies, repairs, or deletes source data. A missing table or empty
schema is treated as a platform prerequisite failure and stops the workflow
before any recommendation artifact is produced.

Run this notebook after ``00_config.py`` and before all analysis producers. It
has no persisted output; successful completion is the precondition consumed by
the next job task.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 01 — Validate existing source scope
# MAGIC
# MAGIC This preflight is read-only. Bronze/source creation and ingestion are outside
# MAGIC the solution boundary.

# COMMAND ----------

existing_source_tables = {
    row.tableName
    for row in spark.sql(
        f"SHOW TABLES IN `{SOURCE_CATALOG}`.`{SOURCE_SCHEMA}`"
    ).collect()
    if not row.isTemporary
}

missing_source_tables = set(SOURCE_TABLES) - existing_source_tables
assert not missing_source_tables, (
    "Configured source tables are unavailable: "
    f"{sorted(missing_source_tables)}. The source platform must provision them; "
    "this solution does not create Bronze data."
)

for table_name in SOURCE_TABLES:
    schema = spark.table(fq_source_table(table_name)).schema
    assert schema.fields, f"Configured source table has no columns: {table_name}"
    print(f"Validated read-only input: {SOURCE_CATALOG}.{SOURCE_SCHEMA}.{table_name}")

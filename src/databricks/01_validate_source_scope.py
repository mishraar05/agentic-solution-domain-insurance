# Databricks notebook source
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

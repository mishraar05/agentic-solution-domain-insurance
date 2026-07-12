# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 01 — Create synthetic Bronze tables
# MAGIC
# MAGIC These tables mimic raw source-aligned P&C structures. All values are synthetic and contain no real customer or claims data.

# COMMAND ----------

from decimal import Decimal
from pyspark.sql.types import (
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from datetime import date, datetime, timezone


def overwrite_delta(rows, schema, table_name: str) -> None:
    spark.createDataFrame(rows, schema=schema).write.format("delta").mode("overwrite").saveAsTable(fq_table(table_name))


policy_schema = StructType([
    StructField("policy_id", StringType(), False),
    StructField("policy_number", StringType(), False),
    StructField("policy_status", StringType(), False),
    StructField("effective_date", DateType(), False),
    StructField("expiration_date", DateType(), False),
    StructField("product_code", StringType(), False),
    StructField("insured_party_id", StringType(), False),
    StructField("source_updated_ts", TimestampType(), False),
])

policy_rows = [
    ("POL-0001", "AUTO-2026-0001", "ACTIVE", date(2026, 1, 1), date(2026, 12, 31), "PERSONAL_AUTO", "PTY-0001", datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)),
    ("POL-0002", "HOME-2026-0002", "CANCELLED", date(2026, 2, 1), date(2027, 1, 31), "HOMEOWNERS", "PTY-0002", datetime(2026, 3, 4, 14, 30, tzinfo=timezone.utc)),
]

policyholder_schema = StructType([
    StructField("party_id", StringType(), False),
    StructField("party_type", StringType(), False),
    StructField("display_name", StringType(), False),
    StructField("contact_channel", StringType(), True),
    StructField("source_updated_ts", TimestampType(), False),
])

policyholder_rows = [
    ("PTY-0001", "PERSON", "Sample Policyholder A", "EMAIL", datetime(2026, 1, 2, 9, 5, tzinfo=timezone.utc)),
    ("PTY-0002", "PERSON", "Sample Policyholder B", "PHONE", datetime(2026, 3, 4, 14, 35, tzinfo=timezone.utc)),
]

claim_schema = StructType([
    StructField("claim_id", StringType(), False),
    StructField("policy_id", StringType(), False),
    StructField("loss_date", DateType(), False),
    StructField("claim_status", StringType(), False),
    StructField("claimed_amount", DecimalType(12, 2), False),
    StructField("source_updated_ts", TimestampType(), False),
])

claim_rows = [
    ("CLM-0001", "POL-0001", date(2026, 2, 14), "OPEN", Decimal("1250.00"), datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc)),
    ("CLM-0002", "POL-0002", date(2026, 2, 20), "CLOSED", Decimal("300.00"), datetime(2026, 2, 23, 16, 15, tzinfo=timezone.utc)),
]

overwrite_delta(policy_rows, policy_schema, "bronze_policy")
overwrite_delta(policyholder_rows, policyholder_schema, "bronze_policyholder")
overwrite_delta(claim_rows, claim_schema, "bronze_claim")

print("Created synthetic Bronze tables:")
for table in ("bronze_policy", "bronze_policyholder", "bronze_claim"):
    print(f"- {CATALOG}.{SCHEMA}.{table}")

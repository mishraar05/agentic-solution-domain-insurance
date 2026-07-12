# Databricks notebook source
"""Publish a human-readable data-dictionary workbook on demand.

This optional reporting entry point is intentionally outside the core pipeline.
It reads a governed ``source_observation_dictionary`` run and renders a traced
Excel workbook with an overview sheet and one worksheet per source table.

By default, only human-``APPROVED`` recommendations are publishable. The
explicit ``draft`` mode includes proposals but adds a visible DRAFT status so
the workbook cannot be mistaken for an authoritative model. The output file is
a reporting artifact; this notebook never changes recommendation tables or
source/Bronze inputs.

Widgets
-------
``publish_mode`` accepts ``approved`` or ``draft``. ``export_dir`` selects the
workspace output directory. If the current run has no dictionary rows, the
latest run for the configured engagement is used and recorded in the workbook.

Run this notebook manually after review, not as part of the five-task core job.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 06 — Publish the source data dictionary (deliverable)
# MAGIC
# MAGIC Read-only reporting step: renders the governed `source_observation_dictionary`
# MAGIC as a formatted Excel workbook — one sheet per source table, stamped with run ID,
# MAGIC artifact version, and publication status for full traceability.
# MAGIC
# MAGIC Default publishes **APPROVED records only**. Set the `publish_mode` job
# MAGIC parameter to `draft` to export unapproved proposals with a DRAFT watermark
# MAGIC (useful before the review workbench exists). Not part of the core job;
# MAGIC run on demand after review.

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

import json
import os

from pyspark.sql import functions as F

from source_intelligence.dictionary_export import build_workbook

# COMMAND ----------

try:
    dbutils.widgets.text("publish_mode", "approved")
    publish_mode = dbutils.widgets.get("publish_mode").strip().lower() or "approved"
    dbutils.widgets.text("export_dir", "/Workspace/Shared/data_dictionary_exports")
    export_dir = dbutils.widgets.get("export_dir").strip()
except Exception:
    publish_mode, export_dir = "approved", "/Workspace/Shared/data_dictionary_exports"
assert publish_mode in ("approved", "draft"), "publish_mode must be 'approved' or 'draft'"
approved_only = publish_mode == "approved"

# COMMAND ----------

dictionary = spark.table(fq_output_table("source_observation_dictionary")).filter(
    (F.col("engagement_id") == ENGAGEMENT_ID) & (F.col("run_id") == RUN_ID)
)
if dictionary.count() == 0:
    # Fallback for on-demand publication: use the most recent run for this engagement.
    latest_run = (
        spark.table(fq_output_table("source_observation_dictionary"))
        .filter(F.col("engagement_id") == ENGAGEMENT_ID)
        .agg(F.max("run_id").alias("r")).collect()[0].r
    )
    assert latest_run, "No dictionary records exist for this engagement."
    dictionary = spark.table(fq_output_table("source_observation_dictionary")).filter(
        (F.col("engagement_id") == ENGAGEMENT_ID) & (F.col("run_id") == latest_run)
    )
    published_run_id = latest_run
else:
    published_run_id = RUN_ID

records = [row.asDict() for row in dictionary.collect()]
workbook, published = build_workbook(
    records, SOURCE_SYSTEM, published_run_id, ARTIFACT_VERSION, approved_only=approved_only
)
if approved_only and published == 0:
    print("No APPROVED records yet — nothing published. "
          "Run with publish_mode=draft for a watermarked working copy.")

# COMMAND ----------

os.makedirs(export_dir, exist_ok=True)
status_tag = "approved" if approved_only else "DRAFT"
file_path = os.path.join(
    export_dir, f"data_dictionary_{SOURCE_SYSTEM}_{published_run_id}_{status_tag}.xlsx"
)
workbook.save(file_path)
print(f"Published {published} attributes to {file_path}")
print(json.dumps({"run_id": published_run_id, "mode": publish_mode,
                  "records_published": published, "file": file_path}))

# Databricks notebook source
"""Shared runtime configuration for every Source Intelligence workflow task.

This notebook is the first entry point and is also imported with ``%run`` by
the later numbered notebooks. It centralizes source scope, recommendation
output locations, artifact versions, review thresholds, and the run identifier
so every task in one Databricks job operates on exactly the same context.

Inputs
------
``run_id`` is an optional Databricks widget supplied by the job definition.
All catalog, schema, source-table, and threshold settings are declared below.

Provides to downstream notebooks
---------------------------------
Validated constants plus helpers for safely quoted source and output table
names. It also makes the reusable ``src/source_intelligence`` package
importable from both Databricks Asset Bundle and interactive workspace paths.

Safety boundary
---------------
The notebook only checks that the configured output schema already exists. It
does not create infrastructure or create, ingest, overwrite, or populate any
source/Bronze table. Source tables are external read-only prerequisites.
"""

# MAGIC %md
# MAGIC # 00 — Source Intelligence configuration
# MAGIC
# MAGIC The core solution consumes existing source-aligned tables. It never creates,
# MAGIC overwrites, ingests, or populates Bronze/source data, and it never provisions
# MAGIC infrastructure: the output schema must already exist (platform-provisioned).
# MAGIC
# MAGIC **Run context:** one `run_id` job parameter is shared by every task in a job
# MAGIC run (set it to `si_job_{{job.run_id}}` in the job definition). Interactive
# MAGIC runs without the parameter generate a timestamp-based run ID.

# COMMAND ----------

import os
import re
import sys
from datetime import datetime, timezone

ENGAGEMENT_ID = "free-edition-synthetic-mvp"

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

ARTIFACT_VERSION = "0.3.0"
SCHEMA_VERSION = "1.0.0"
LOW_CONFIDENCE_THRESHOLD = 0.75
EVIDENCE_COVERAGE_FLOOR = 0.60

# COMMAND ----------

# Single run context for the whole job (contract pattern: si_<ts> | si_job_<id>).
RUN_ID_PATTERN = re.compile(r"^si_(\d{8}T\d{6}Z|job_\d+)$")


def _resolve_run_id() -> str:
    try:
        dbutils.widgets.text("run_id", "")
        candidate = dbutils.widgets.get("run_id").strip()
    except Exception:
        candidate = ""
    if candidate:
        if not RUN_ID_PATTERN.match(candidate):
            raise ValueError(
                f"run_id job parameter {candidate!r} violates the contract pattern "
                "si_<yyyymmdd>T<hhmmss>Z or si_job_<digits>."
            )
        return candidate
    return datetime.now(timezone.utc).strftime("si_%Y%m%dT%H%M%SZ")


RUN_ID = _resolve_run_id()
RUN_STARTED_AT = datetime.now(timezone.utc)

# COMMAND ----------

# Make the deterministic core importable from workspace files.
# Primary: resolve from the notebook path (robust across Databricks execution
# modes); fallback: cwd-relative for local/test execution.
def _parent_directories(path: str, maximum_depth: int = 6):
    """Return ``path`` and a bounded list of parents, nearest first."""
    current = os.path.abspath(path)
    parents = []
    for _ in range(maximum_depth):
        if current in parents:
            break
        parents.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return parents


def _resolve_repo_src() -> str:
    """Locate the ``src`` directory without assuming a workspace root path."""
    starting_points = []
    try:
        starting_points.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    try:
        nb_path = (dbutils.notebook.entry_point.getDbutils().notebook()
                   .getContext().notebookPath().get())
        workspace_path = (
            nb_path if nb_path.startswith("/Workspace/")
            else f"/Workspace{nb_path}"
        )
        starting_points.append(os.path.dirname(workspace_path))
    except Exception:
        pass
    starting_points.append(os.getcwd())
    candidates = []
    for starting_point in starting_points:
        candidates.extend(_parent_directories(starting_point))
    for candidate in candidates:
        if os.path.isdir(os.path.join(candidate, "source_intelligence")):
            return candidate
    raise RuntimeError(
        "Cannot locate source_intelligence modules relative to the deployed "
        "notebook or current working directory."
    )


_REPO_SRC = _resolve_repo_src()
if _REPO_SRC not in sys.path:
    sys.path.insert(0, _REPO_SRC)

# COMMAND ----------


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


# Validate — never create — the output destination (recommendation-only boundary).
_output_schemas = {
    row.databaseName
    for row in spark.sql(f"SHOW SCHEMAS IN `{OUTPUT_CATALOG}`").collect()
}
assert OUTPUT_SCHEMA in _output_schemas, (
    f"Output schema `{OUTPUT_CATALOG}`.`{OUTPUT_SCHEMA}` does not exist. "
    "Provision it separately (platform step); the core solution performs no DDL."
)

print(f"Run ID: {RUN_ID}")
print(f"Read-only source scope: {SOURCE_CATALOG}.{SOURCE_SCHEMA} {SOURCE_TABLES}")
print(f"Recommendation output schema: {OUTPUT_CATALOG}.{OUTPUT_SCHEMA}")

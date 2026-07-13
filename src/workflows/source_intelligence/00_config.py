# Databricks notebook source
"""Shared runtime configuration for every Source Intelligence workflow task.

This notebook is the first entry point and is also imported with ``%run`` by
the later numbered notebooks. It centralizes source scope, recommendation
output locations, artifact versions, review thresholds, model endpoint, and the run identifier
so every task in one Databricks job operates on exactly the same context.

Inputs
------
``run_id``, governed source/output scope, source naming convention, and the
latest permitted rule-pack effective date are Databricks widgets supplied by
the job definition. Threshold and artifact-version settings are declared below
because changing them requires versioned code and governance review.

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

# COMMAND ----------

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

import importlib
import os
import re
import sys
from datetime import datetime, timezone

def _required_widget(name: str) -> str:
    """Read a required job parameter without embedding environment inventory."""
    dbutils.widgets.text(name, "")
    value = dbutils.widgets.get(name).strip()
    if not value:
        raise ValueError(f"Required Databricks job parameter is empty: {name}")
    return value


ENGAGEMENT_ID = _required_widget("engagement_id")

# Existing read-only source scope supplied by deployment configuration.
SOURCE_CATALOG = _required_widget("source_catalog")
SOURCE_SCHEMA = _required_widget("source_schema")
SOURCE_TABLES = tuple(
    table.strip()
    for table in _required_widget("source_tables").split(",")
    if table.strip()
)
if not SOURCE_TABLES:
    raise ValueError("source_tables must contain at least one table name.")
SOURCE_SYSTEM = _required_widget("source_system")
_naming_convention = _required_widget("naming_convention")
NAMING_CONVENTION = (
    None if _naming_convention.upper() == "AUTO" else _naming_convention
)
RULE_EFFECTIVE_DATE = _required_widget("rule_effective_date")
try:
    datetime.strptime(RULE_EFFECTIVE_DATE, "%Y-%m-%d")
except ValueError as exc:
    raise ValueError("rule_effective_date must use YYYY-MM-DD format.") from exc

# Solution-owned recommendation destination supplied independently of source scope.
OUTPUT_CATALOG = _required_widget("output_catalog")
OUTPUT_SCHEMA = _required_widget("output_schema")

# Databricks-hosted model endpoint used only by the Source Documentation Agent.
DOCUMENTATION_MODEL_ENDPOINT = _required_widget("documentation_model_endpoint")
if not re.fullmatch(r"[A-Za-z0-9._-]+", DOCUMENTATION_MODEL_ENDPOINT):
    raise ValueError(
        "documentation_model_endpoint may contain only letters, numbers, dots, "
        "underscores, and hyphens."
    )
try:
    DOCUMENTATION_MAX_TOKENS = int(
        _required_widget("documentation_max_tokens")
    )
except ValueError as exc:
    raise ValueError("documentation_max_tokens must be an integer.") from exc
if DOCUMENTATION_MAX_TOKENS <= 0:
    raise ValueError("documentation_max_tokens must be greater than zero.")

# Compatibility aliases for notebooks that only write recommendation artifacts.
CATALOG = OUTPUT_CATALOG
SCHEMA = OUTPUT_SCHEMA

ARTIFACT_VERSION = "0.5.0"
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


def _is_source_root(candidate: str) -> bool:
    """Return True only for the parent of the real importable core package.

    The workflow directory is also named ``source_intelligence`` but contains
    Databricks entry points rather than the reusable Python package. Requiring
    ``__init__.py`` prevents that directory from shadowing the package at
    ``src/source_intelligence``.
    """
    package_dir = os.path.join(candidate, "source_intelligence")
    return (
        os.path.isdir(package_dir)
        and os.path.isfile(os.path.join(package_dir, "__init__.py"))
    )


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
        if _is_source_root(candidate):
            return candidate
    raise RuntimeError(
        "Cannot locate source_intelligence modules relative to the deployed "
        "notebook or current working directory."
    )


_REPO_SRC = _resolve_repo_src()
while _REPO_SRC in sys.path:
    sys.path.remove(_REPO_SRC)
sys.path.insert(0, _REPO_SRC)
print(f"Source Intelligence Python package root: {_REPO_SRC}")

_core_package = importlib.import_module("source_intelligence")
_expected_package_file = os.path.normcase(os.path.abspath(
    os.path.join(_REPO_SRC, "source_intelligence", "__init__.py")
))
_actual_package_file = os.path.normcase(os.path.abspath(
    getattr(_core_package, "__file__", "") or ""
))
assert _actual_package_file == _expected_package_file, (
    "The workflow directory is shadowing the reusable source_intelligence "
    f"package. Expected {_expected_package_file!r}, resolved "
    f"{_actual_package_file!r}. Redeploy the complete bundle source tree."
)

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
print(
    "Rule-pack selection: "
    f"source_system={SOURCE_SYSTEM}, "
    f"naming_convention={NAMING_CONVENTION or 'AUTO'}, "
    f"effective_date={RULE_EFFECTIVE_DATE}"
)
print(f"Recommendation output schema: {OUTPUT_CATALOG}.{OUTPUT_SCHEMA}")
print(f"Source Documentation model endpoint: {DOCUMENTATION_MODEL_ENDPOINT}")
print(f"Source Documentation output-token budget: {DOCUMENTATION_MAX_TOKENS}")

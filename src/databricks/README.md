# Agentic Insurance Domain Solution — Databricks MVP

This starter project implements the first safe, deterministic slice of the architecture:

1. Create synthetic P&C Bronze tables.
2. Generate a source-observation catalog / proposed source data dictionary.
3. Create a reviewer work queue for low-confidence, unresolved, or privacy-relevant entries.
4. Validate the MVP outputs.

It is designed for Databricks Free Edition and uses only built-in PySpark and Delta tables. It does **not** call an LLM, create a vector index, access external services, or load real data.

## Safety boundary

Do not upload client data, PII, claims narratives, proprietary COTS documentation, credentials, or production connection strings to Databricks Free Edition. The sample data is entirely synthetic.

## Run order

Upload this folder to a Databricks Workspace folder as source notebooks, then run in order:

1. `00_config.py`
2. `01_setup_synthetic_bronze.py`
3. `02_build_source_dictionary.py`
4. `03_create_review_queue.py`
5. `04_validate_mvp.py`

Each notebook runs `%run ./00_config`, so it can also be run individually after the configuration notebook has been uploaded alongside it.

## What gets created

The notebooks create this schema in the `workspace` catalog by default:

| Table | Purpose |
|---|---|
| `bronze_policy` | Synthetic, source-aligned policy data |
| `bronze_policyholder` | Synthetic party/policyholder data |
| `bronze_claim` | Synthetic claims data |
| `source_observation_dictionary` | Physical metadata plus proposed semantic interpretation and evidence |
| `review_queue` | Items requiring data-architect, steward, or privacy review |

## Configuration

In `00_config.py`, change `CATALOG` and `SCHEMA` if your workspace uses different names. The Free Edition default is normally the `workspace` catalog.

## Expected result

After the final notebook finishes, query:

```sql
SELECT *
FROM workspace.agentic_insurance_mvp.source_observation_dictionary
ORDER BY source_table, ordinal_position;
```

The resulting dictionary deliberately separates **observed** physical facts from **inferred** business meaning. It is a recommendation artifact and must be reviewed before being treated as authoritative.

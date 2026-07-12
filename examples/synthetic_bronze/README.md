# Synthetic Bronze demo fixture

This folder is an optional, isolated demonstration harness. It is not part of
the Source Intelligence production workflow.

Run `setup_synthetic_bronze.py` only when a disposable synthetic source is
needed for a demo or integration test. The notebook creates tables in
`workspace.agentic_insurance_demo_bronze` by default.

The core solution consumes configured, existing source tables and never calls
this setup notebook. To use the demo fixture, configure
`src/databricks/00_config.py` with the demo catalog, schema, and table names,
then run the core Source Intelligence job separately.

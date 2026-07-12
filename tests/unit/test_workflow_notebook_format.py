"""Validate Databricks source-notebook command boundaries.

Databricks magic commands such as ``%run`` and ``%md`` must occupy a command
containing only ``# MAGIC`` lines. Mixing a Python module docstring and magic
comments in one command causes Databricks to parse Markdown as Python and raise
a syntax error even though local ``compileall`` succeeds.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / "src" / "workflows" / "source_intelligence"
COMMAND_SEPARATOR = "# COMMAND ----------"


def test_workflow_files_are_databricks_source_notebooks():
    for path in WORKFLOW_DIR.glob("*.py"):
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "# Databricks notebook source", path


def test_magic_commands_are_not_mixed_with_python_statements():
    for path in WORKFLOW_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for command_number, command in enumerate(
            source.split(COMMAND_SEPARATOR), start=1
        ):
            lines = [line for line in command.splitlines() if line.strip()]
            magic_lines = [line for line in lines if line.startswith("# MAGIC")]
            if not magic_lines:
                continue
            assert len(magic_lines) == len(lines), (
                f"{path.name} command {command_number} mixes Databricks magic "
                "with Python or notebook-source header lines"
            )

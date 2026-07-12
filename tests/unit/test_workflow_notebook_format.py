"""Validate Databricks source-notebook command and import-path boundaries.

Databricks magic commands such as ``%run`` and ``%md`` must occupy a command
containing only ``# MAGIC`` lines. Mixing a Python module docstring and magic
comments in one command causes Databricks to parse Markdown as Python and raise
a syntax error even though local ``compileall`` succeeds.
"""

import ast
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


def test_config_requires_a_real_python_package_when_resolving_src():
    config = (WORKFLOW_DIR / "00_config.py").read_text(encoding="utf-8")
    assert 'os.path.isfile(os.path.join(package_dir, "__init__.py"))' in config
    assert "sys.path.insert(0, _REPO_SRC)" in config
    assert 'importlib.import_module("source_intelligence")' in config
    assert "_actual_package_file == _expected_package_file" in config


def test_workflow_directory_is_not_accepted_as_core_package_root(tmp_path):
    config_path = WORKFLOW_DIR / "00_config.py"
    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_is_source_root"
    )
    namespace = {}
    module = ast.Module(
        body=[ast.Import(names=[ast.alias(name="os")]), helper],
        type_ignores=[],
    )
    module = ast.fix_missing_locations(module)
    exec(compile(module, str(config_path), "exec"), namespace)

    src = tmp_path / "src"
    workflow_parent = src / "workflows"
    workflow_directory = workflow_parent / "source_intelligence"
    package_directory = src / "source_intelligence"
    workflow_directory.mkdir(parents=True)
    package_directory.mkdir()
    (package_directory / "__init__.py").write_text("", encoding="utf-8")

    assert not namespace["_is_source_root"](str(workflow_parent))
    assert namespace["_is_source_root"](str(src))


def test_routing_and_validation_use_canonical_attribute_table():
    documentation = (
        WORKFLOW_DIR / "03_generate_source_documentation.py"
    ).read_text(encoding="utf-8")
    routing = (WORKFLOW_DIR / "04_create_review_queue.py").read_text(
        encoding="utf-8"
    )
    validation = (WORKFLOW_DIR / "05_validate_source_intelligence.py").read_text(
        encoding="utf-8"
    )
    assert 'fq_table("source_attribute_observation")' in documentation
    assert "ai_query(" in documentation
    assert "is_prompt_eligible" in documentation
    assert 'fq_table("source_attribute_observation")' in routing
    assert 'fq_table("source_observation_dictionary")' not in routing
    assert 'fq_table("source_documentation_recommendation")' in routing
    assert 'fq_table("source_intelligence_review_queue")' in routing
    assert 'fq_output_table("source_intelligence_review_queue")' in validation
    assert 'fq_output_table("source_documentation_recommendation")' in validation
    assert 'attributes.filter(F.col("evidence_coverage")' in validation
    assert 'attributes.filter(F.col("formula_version")' in validation

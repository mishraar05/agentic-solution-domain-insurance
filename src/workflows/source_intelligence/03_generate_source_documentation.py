# Databricks notebook source
"""Generate governed source-column descriptions and glossary proposals.

This Source Documentation Agent reads only solution-owned canonical attribute
observations and minimized aggregate profile evidence produced for the current
``run_id``. It constructs an allow-listed prompt for each governance-eligible
column and invokes the configured Databricks-hosted model with ``ai_query`` and
a strict JSON response schema.

Personal and sensitive observations are rejected before prompt construction;
they produce an explicit ``UNRESOLVED`` recommendation without a model call.
Source values, arbitrary table metadata, claims narratives, credentials, and
proprietary documentation are never prompt inputs. Model errors fail the task
before persistence so a retry can recover without leaving partial output.

Every result is contract-validated and persisted to
``source_documentation_recommendation`` with ``PROPOSED`` approval state and a
Domain Steward reviewer role. The model does not assign confidence or approve
its own output. Run after ``02_build_source_dictionary.py`` and before review
routing.

Runtime prerequisite: Databricks serverless compute with ``ai_query`` support
and access to the configured Foundation Model API endpoint.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 03 — Generate source documentation recommendations
# MAGIC
# MAGIC LLM-assisted column descriptions and business-glossary proposals from
# MAGIC governed structural context. Outputs remain `PROPOSED` or `UNRESOLVED`
# MAGIC and always require Domain Steward review.

# COMMAND ----------

import json
from collections import defaultdict
from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType, StringType, StructField, StructType, TimestampType,
)

from source_intelligence.contract_validation import validate_records
from source_intelligence.source_documentation import (
    AIQueryInvocationError,
    AIQueryResponseShapeError,
    PROMPT_VERSION,
    build_prompt,
    build_prompt_context,
    build_recommendation,
    extract_ai_query_response,
    is_prompt_eligible,
    load_system_prompt,
    model_response_format,
    unresolved_model_output,
)

# COMMAND ----------

output_table = fq_table("source_documentation_recommendation")
already_written = (
    spark.catalog.tableExists(output_table)
    and spark.table(output_table).filter(F.col("run_id") == RUN_ID).count() > 0
)

if already_written:
    print(
        f"Idempotent skip: source documentation for run {RUN_ID} already exists."
    )
    documentation_df = spark.table(output_table).filter(F.col("run_id") == RUN_ID)
else:
    attribute_rows = (
        spark.table(fq_table("source_attribute_observation"))
        .filter(F.col("run_id") == RUN_ID)
        .collect()
    )
    assert attribute_rows, (
        f"No canonical attribute observations found for run {RUN_ID}."
    )

    profile_rows = (
        spark.table(fq_table("profile_evidence"))
        .filter(F.col("run_id") == RUN_ID)
        .collect()
    )
    profiles_by_attribute = defaultdict(list)
    for profile_row in profile_rows:
        profile = profile_row.asDict(recursive=True)
        profiles_by_attribute[(
            profile["source_table"], profile["source_column"]
        )].append(profile)

    system_prompt = load_system_prompt()
    observations = {}
    contexts = {}
    request_rows = []
    blocked_outputs = {}
    for attribute_row in attribute_rows:
        observation = attribute_row.asDict(recursive=True)
        key = (observation["source_table"], observation["source_column"])
        observations[key] = observation
        if is_prompt_eligible(observation):
            context = build_prompt_context(
                observation, profiles_by_attribute.get(key, [])
            )
            contexts[key] = context
            request_rows.append(Row(
                source_table=key[0],
                source_column=key[1],
                prompt=build_prompt(system_prompt, context),
            ))
        else:
            contexts[key] = {
                "prompt_eligible": False,
                "policy_reason": (
                    "Privacy policy prohibits this observation from LLM context."
                ),
                "privacy_class": observation["privacy_class"],
                "evidence_references": sorted(
                    observation["evidence_references"]
                ),
            }
            blocked_outputs[key] = unresolved_model_output(
                "Prompt context prohibited by privacy policy; a human must "
                "resolve the documentation without exposing personal values."
            )

    model_outputs = {}
    if request_rows:
        request_schema = StructType([
            StructField("source_table", StringType(), False),
            StructField("source_column", StringType(), False),
            StructField("prompt", StringType(), False),
        ])
        requests_df = spark.createDataFrame(request_rows, request_schema)
        endpoint = DOCUMENTATION_MODEL_ENDPOINT.replace("'", "''")
        response_format = json.dumps(
            model_response_format(), separators=(",", ":")
        ).replace("'", "''")
        invocation = F.expr(
            "ai_query("
            f"'{endpoint}', prompt, "
            "modelParameters => named_struct("
            f"'max_tokens', {DOCUMENTATION_MAX_TOKENS}, "
            "'temperature', 0.0), "
            f"responseFormat => '{response_format}', "
            "failOnError => false)"
        )
        result_rows = requests_df.select(
            "source_table", "source_column", invocation.alias("model_result")
        ).collect()
        failed_by_diagnostic = defaultdict(list)
        for result_row in result_rows:
            key = (result_row.source_table, result_row.source_column)
            try:
                model_outputs[key] = extract_ai_query_response(
                    result_row.model_result
                )
            except AIQueryInvocationError as exc:
                failed_by_diagnostic[exc.safe_diagnostic].append(key)
            except AIQueryResponseShapeError as exc:
                raise RuntimeError(
                    f"Unexpected ai_query response for {key}: {exc}"
                ) from exc
        if failed_by_diagnostic:
            failed_count = sum(
                len(keys) for keys in failed_by_diagnostic.values()
            )
            diagnostic_groups = []
            for diagnostic, keys in sorted(failed_by_diagnostic.items()):
                samples = ", ".join(
                    f"{table}.{column}" for table, column in keys[:5]
                )
                omitted = len(keys) - 5
                if omitted:
                    samples += f", +{omitted} more"
                diagnostic_groups.append(
                    f"{diagnostic} [{samples}]"
                )
            raise RuntimeError(
                f"Model invocation failed for {failed_count} source columns: "
                f"{'; '.join(diagnostic_groups)}; "
                "no documentation recommendations were persisted."
            )

    created_at = datetime.now(timezone.utc)
    recommendations = []
    for key, observation in observations.items():
        output = blocked_outputs.get(key, model_outputs.get(key))
        assert output is not None, f"Missing model output for {key}."
        recommendations.append(build_recommendation(
            observation=observation,
            context=contexts[key],
            model_output=output,
            model_endpoint=DOCUMENTATION_MODEL_ENDPOINT,
            created_at=created_at.isoformat(),
        ))

    validate_records(
        recommendations, "source_documentation_recommendation.json"
    )
    documentation_schema = StructType([
        StructField("schema_version", StringType(), False),
        StructField("recommendation_id", StringType(), False),
        StructField("run_id", StringType(), False),
        StructField("artifact_version", StringType(), False),
        StructField("engagement_id", StringType(), False),
        StructField("source_system", StringType(), False),
        StructField("source_table", StringType(), False),
        StructField("source_column", StringType(), False),
        StructField("context_fingerprint", StringType(), False),
        StructField("evidence_references", ArrayType(StringType()), False),
        StructField("generation_status", StringType(), False),
        StructField("proposed_column_description", StringType(), True),
        StructField("proposed_glossary_term", StringType(), True),
        StructField("proposed_glossary_definition", StringType(), True),
        StructField("proposed_glossary_concept_id", StringType(), True),
        StructField("resolution_reason", StringType(), False),
        StructField("assumptions", ArrayType(StringType()), False),
        StructField("contradictions", ArrayType(StringType()), False),
        StructField("prompt_version", StringType(), False),
        StructField("model_endpoint", StringType(), False),
        StructField("approval_state", StringType(), False),
        StructField("reviewer_role", StringType(), False),
        StructField("created_at", TimestampType(), False),
    ])
    field_names = [field.name for field in documentation_schema.fields]
    rows = [Row(**{
        name: created_at if name == "created_at" else recommendation[name]
        for name in field_names
    }) for recommendation in recommendations]
    documentation_df = spark.createDataFrame(rows, documentation_schema)
    documentation_df.write.format("delta").mode("append").saveAsTable(
        output_table
    )
    print(
        f"Persisted {len(recommendations)} Source Documentation Agent outputs "
        f"using prompt {PROMPT_VERSION}."
    )

# COMMAND ----------

display(documentation_df.orderBy("source_table", "source_column"))

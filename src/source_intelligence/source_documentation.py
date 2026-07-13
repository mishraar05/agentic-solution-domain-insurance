"""Build governed prompts and recommendations for source documentation.

The module keeps model orchestration independent from Databricks. It accepts
only canonical observation dictionaries and minimized profile summaries,
constructs a bounded prompt context, validates structured model output, and
creates a contract-shaped recommendation. It never reads a source table,
invokes a model, assigns confidence, or approves a recommendation.

Personal or sensitive observations are not prompt eligible. They produce an
explicit ``UNRESOLVED`` recommendation without an LLM call, preserving the
privacy boundary even when the caller accidentally supplies profile evidence.
"""

import hashlib
import json
import os

from source_intelligence.contract_validation import validate_records


PROMPT_VERSION = "1.0.0"
MODEL_OUTPUT_CONTRACT = "source_documentation_model_output.json"
RECOMMENDATION_CONTRACT = "source_documentation_recommendation.json"


class AIQueryInvocationError(RuntimeError):
    """An ``ai_query`` row reported a safely classified invocation failure."""

    def __init__(self, message, reason_code, diagnostic_fingerprint=None):
        super().__init__(message)
        self.reason_code = reason_code
        self.diagnostic_fingerprint = diagnostic_fingerprint

    @property
    def safe_diagnostic(self):
        """Return a bounded diagnostic containing no endpoint error text."""
        if self.diagnostic_fingerprint:
            return f"{self.reason_code}:{self.diagnostic_fingerprint}"
        return self.reason_code


class AIQueryResponseShapeError(ValueError):
    """An ``ai_query`` row did not match a governed response shape."""


def _classify_ai_query_error(error_message):
    """Map endpoint text to a bounded reason code and stable fingerprint.

    The raw text is used only in memory. It is never included in an exception
    message because serving errors can echo prompt fragments or endpoint
    details.
    """
    raw_message = str(error_message)
    normalized = raw_message.casefold()
    classifications = (
        ("UNSUPPORTED_BATCH_ENDPOINT", (
            "not supported for batch inference", "batch inference unsupported",
        )),
        ("RATE_LIMITED", (
            "rate limit", "rate_limit", "resource exhausted",
            "resource_exhausted", "too many requests", "429",
        )),
        ("STRUCTURED_OUTPUT_ERROR", (
            "responseformat", "response_format", "response format",
            "json schema", "json_schema", "structured output",
            "structured_output", "schema validation", "schema_validation",
            "invalid json", "invalid_json",
        )),
        ("TOKEN_LIMIT", (
            "token limit", "token_limit", "max tokens", "max_tokens",
            "maximum context length", "context length exceeded",
            "finish_reason length", "finish_reason\":\"length",
            "output truncated", "output_truncated",
        )),
        ("TIMEOUT", ("timeout", "timed out", "deadline exceeded")),
        ("PERMISSION_DENIED", (
            "permission denied", "permission_denied", "unauthorized",
            "forbidden", "403",
        )),
        ("INVALID_REQUEST", (
            "invalid request", "invalid_request", "invalid parameter",
            "invalid_parameter", "bad request", "bad_request", "400",
        )),
        ("SERVICE_UNAVAILABLE", (
            "service unavailable", "service_unavailable", "temporarily "
            "unavailable", "upstream unavailable", "502", "503",
        )),
    )
    reason_code = "MODEL_INVOCATION_FAILED"
    for candidate, markers in classifications:
        if any(marker in normalized for marker in markers):
            reason_code = candidate
            break
    fingerprint = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()[:12]
    return reason_code, fingerprint


def load_system_prompt(prompt_path=None):
    """Load the versioned system prompt from the repository."""
    path = prompt_path or os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "prompts",
        "01_source_documentation_agent.md",
    ))
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def is_prompt_eligible(observation):
    """Return whether governance permits this observation in LLM context."""
    return observation.get("privacy_class") == "INTERNAL"


def build_prompt_context(observation, profile_summaries=None):
    """Return a minimized, allow-listed context dictionary.

    Source row values and arbitrary metadata are intentionally impossible to
    pass through this function because only explicit structural and governed
    inference fields are copied.
    """
    if not is_prompt_eligible(observation):
        raise ValueError(
            "Personal or sensitive observations are not eligible for LLM prompts."
        )
    profiles = []
    for profile in profile_summaries or []:
        if (
            profile.get("evidence_class") not in {
                "AGGREGATE_PROFILE", "CONTROLLED_VALUE_SUMMARY"
            }
            or profile.get("is_minimized") is not True
            or profile.get("privacy_class") != "INTERNAL"
        ):
            raise ValueError(
                "Profile evidence is not minimized and prompt eligible."
            )
        evidence_reference = profile.get("evidence_reference") or (
            "profile_evidence:"
            f"{profile.get('run_id', observation['run_id'])}:"
            f"{observation['source_table']}.{observation['source_column']}:"
            f"{profile['profile_type'].lower()}"
        )
        profiles.append({
            "profile_type": profile["profile_type"],
            "profile_value": str(profile["profile_value"]),
            "evidence_reference": evidence_reference,
        })
    return {
        "observed_physical_metadata": {
            "source_system": observation["source_system"],
            "source_table": observation["source_table"],
            "source_column": observation["source_column"],
            "ordinal_position": observation["ordinal_position"],
            "physical_type": observation["physical_type"],
            "nullable": observation["nullable"],
        },
        "deterministic_inferences": {
            "key_role": observation["key_role"],
            "relationship_evidence": observation.get("relationship_evidence"),
            "proposed_business_name": observation["proposed_business_name"],
            "ontology_concept_id": observation.get("ontology_concept_id"),
            "domain": observation["domain"],
            "assumptions": observation.get("assumptions"),
            "contradictions": observation.get("contradictions"),
            "open_question": observation.get("open_question"),
        },
        "minimized_aggregate_profiles": profiles,
        "evidence_references": sorted(observation["evidence_references"]),
    }


def context_fingerprint(context):
    """Return a stable hash of the exact governed context sent to the model."""
    payload = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_prompt(system_prompt, context):
    """Combine fixed instructions and JSON context with clear trust boundaries."""
    return (
        f"{system_prompt}\n\n"
        "BEGIN UNTRUSTED SOURCE CONTEXT\n"
        f"{json.dumps(context, sort_keys=True)}\n"
        "END UNTRUSTED SOURCE CONTEXT"
    )


def model_response_format():
    """Return the simple strict JSON schema supplied to Databricks ``ai_query``."""
    schema = {
        "type": "object",
        "properties": {
            "generation_status": {
                "type": "string", "enum": ["PROPOSED", "UNRESOLVED"]
            },
            "column_description": {"type": ["string", "null"]},
            "glossary_term": {"type": ["string", "null"]},
            "glossary_definition": {"type": ["string", "null"]},
            "glossary_concept_id": {"type": ["string", "null"]},
            "resolution_reason": {"type": "string"},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "contradictions": {
                "type": "array", "items": {"type": "string"}
            },
        },
        "required": [
            "generation_status", "column_description", "glossary_term",
            "glossary_definition", "glossary_concept_id", "resolution_reason",
            "assumptions", "contradictions",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "source_documentation",
            "description": "A source-column description and glossary proposal",
            "schema": schema,
            "strict": True,
        },
    }


def extract_ai_query_response(model_result):
    """Normalize documented wrapper and direct structured-output results.

    Databricks returns ``errorMessage`` plus either ``response`` or ``result``
    when ``failOnError`` is false, depending on the structured-output execution
    path. Some Spark paths expose the parsed ``responseFormat`` object directly.
    These shapes are accepted only when they lead to the governed model-output
    contract; endpoint-native ``content`` or ``candidates`` payloads are
    deliberately not treated as documentation.
    """
    if model_result is None:
        raise AIQueryInvocationError(
            "ai_query returned a null result.", "NULL_MODEL_RESULT"
        )
    if hasattr(model_result, "asDict"):
        result = model_result.asDict(recursive=True)
    elif isinstance(model_result, dict):
        result = dict(model_result)
    else:
        raise AIQueryResponseShapeError(
            "Unexpected ai_query result type: "
            f"{type(model_result).__name__}."
        )

    if result.get("errorMessage"):
        # Endpoint text may contain request/model details; do not propagate it.
        reason_code, fingerprint = _classify_ai_query_error(
            result["errorMessage"]
        )
        raise AIQueryInvocationError(
            "ai_query reported a model error.", reason_code, fingerprint
        )
    payload_field = next(
        (field for field in ("response", "result") if field in result),
        None,
    )
    if payload_field:
        response = result[payload_field]
        if response is None:
            raise AIQueryInvocationError(
                f"ai_query returned a null {payload_field} without a model "
                "error.",
                f"NULL_{payload_field.upper()}_PAYLOAD",
            )
        if hasattr(response, "asDict"):
            return response.asDict(recursive=True)
        return response

    required = set(
        model_response_format()["json_schema"]["schema"]["required"]
    )
    if required <= set(result):
        return result
    raise AIQueryResponseShapeError(
        "Unexpected ai_query response fields: "
        f"{sorted(result)}; expected wrapper fields or governed structured "
        "output fields."
    )


def unresolved_model_output(reason):
    """Return a valid no-call result when governance blocks model context."""
    return {
        "generation_status": "UNRESOLVED",
        "column_description": None,
        "glossary_term": None,
        "glossary_definition": None,
        "glossary_concept_id": None,
        "resolution_reason": reason,
        "assumptions": [],
        "contradictions": [],
    }


def parse_model_output(output):
    """Parse and validate one structured LLM response."""
    result = json.loads(output) if isinstance(output, str) else dict(output)
    validate_records([result], MODEL_OUTPUT_CONTRACT)
    if not result["resolution_reason"].strip():
        raise ValueError("Documentation output requires a resolution reason.")
    proposed_fields = (
        "column_description", "glossary_term", "glossary_definition"
    )
    if result["generation_status"] == "PROPOSED":
        if any(not result[field] for field in proposed_fields):
            raise ValueError("PROPOSED documentation requires all text fields.")
    elif (
        any(result[field] is not None for field in proposed_fields)
        or result["glossary_concept_id"] is not None
    ):
        raise ValueError("UNRESOLVED documentation must not invent text fields.")
    return result


def build_recommendation(observation, context, model_output, model_endpoint,
                         created_at):
    """Create and validate one non-authoritative documentation recommendation."""
    output = parse_model_output(model_output)
    fingerprint = context_fingerprint(context)
    identity = "|".join((
        observation["run_id"], observation["source_table"],
        observation["source_column"], fingerprint, PROMPT_VERSION,
        model_endpoint,
    ))
    recommendation_id = "si_doc_" + hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:32]
    recommendation = {
        "schema_version": observation["schema_version"],
        "recommendation_id": recommendation_id,
        "run_id": observation["run_id"],
        "artifact_version": observation["artifact_version"],
        "engagement_id": observation["engagement_id"],
        "source_system": observation["source_system"],
        "source_table": observation["source_table"],
        "source_column": observation["source_column"],
        "context_fingerprint": fingerprint,
        "evidence_references": sorted(observation["evidence_references"]),
        "generation_status": output["generation_status"],
        "proposed_column_description": output["column_description"],
        "proposed_glossary_term": output["glossary_term"],
        "proposed_glossary_definition": output["glossary_definition"],
        "proposed_glossary_concept_id": output["glossary_concept_id"],
        "resolution_reason": output["resolution_reason"],
        "assumptions": output["assumptions"],
        "contradictions": output["contradictions"],
        "prompt_version": PROMPT_VERSION,
        "model_endpoint": model_endpoint,
        "approval_state": "PROPOSED",
        "reviewer_role": "DOMAIN_STEWARD",
        "created_at": created_at,
    }
    validate_records([recommendation], RECOMMENDATION_CONTRACT)
    return recommendation

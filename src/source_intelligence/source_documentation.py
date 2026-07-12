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

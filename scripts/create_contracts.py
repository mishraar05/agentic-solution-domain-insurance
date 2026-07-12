import os, json

CONTRACTS_DIR = r"d:\agentic-solution-domain-insurance\contracts"
os.makedirs(CONTRACTS_DIR, exist_ok=True)

COMMON_REF = {"$ref": "common.json#/$defs" if False else "common.json#/definitions"}

schemas = {}

# 1. source_intelligence_run.json
schemas["source_intelligence_run.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/source_intelligence_run.json",
    "title": "Source Intelligence Run",
    "description": "Run status, scope, context versions, metrics, and error information",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "engagement_id": {"$ref": "common.json#/definitions/engagement_id"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "source_scope": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of source tables included in the run"
        },
        "knowledge_pack_versions": {
            "type": "object",
            "description": "Version references for knowledge packs used",
            "additionalProperties": {"type": "string"}
        },
        "task_contract_version": {
            "type": "string",
            "description": "Version of the task contract used for this run"
        },
        "idempotency_key": {
            "type": "string",
            "description": "Normalized hash of scope + evidence snapshot + knowledge versions + task contract version"
        },
        "run_status": {
            "type": "string",
            "enum": ["STARTED", "RUNNING", "SUCCEEDED", "FAILED", "PARTIAL"],
            "description": "Current status of the run"
        },
        "started_at": {"$ref": "common.json#/definitions/timestamp_utc"},
        "completed_at": {"$ref": "common.json#/definitions/timestamp_utc"},
        "metrics": {
            "type": "object",
            "properties": {
                "objects_observed": {"type": "integer", "minimum": 0},
                "attributes_observed": {"type": "integer", "minimum": 0},
                "relationships_inferred": {"type": "integer", "minimum": 0},
                "privacy_classifications": {"type": "integer", "minimum": 0},
                "review_items_created": {"type": "integer", "minimum": 0},
                "policy_violations": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": False
        },
        "error_info": {
            "type": ["string", "null"],
            "description": "Error message if run failed"
        }
    },
    "required": ["schema_version", "run_id", "artifact_version", "engagement_id", "source_system", "source_scope", "run_status", "started_at"],
    "additionalProperties": False
}

# 2. source_object_observation.json
schemas["source_object_observation.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/source_object_observation.json",
    "title": "Source Object Observation",
    "description": "Object-level schema, profile, and recognition findings",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "engagement_id": {"$ref": "common.json#/definitions/engagement_id"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "source_table": {"$ref": "common.json#/definitions/source_table"},
        "object_type": {"type": "string", "enum": ["TABLE", "VIEW"], "description": "Type of source object"},
        "column_count": {"type": "integer", "minimum": 0},
        "row_count_estimate": {"type": "integer", "minimum": 0},
        "proposed_domain": {"$ref": "common.json#/definitions/domain"},
        "proposed_domain_confidence": {"$ref": "common.json#/definitions/confidence_score"},
        "cots_match_assessment": {
            "type": ["object", "null"],
            "properties": {
                "product": {"type": "string"},
                "module": {"type": "string"},
                "version": {"type": "string"},
                "match_strength": {"$ref": "common.json#/definitions/confidence_score"},
                "customization_candidates": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": False
        },
        "profile_summary": {
            "type": ["object", "null"],
            "properties": {
                "null_rate_avg": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "distinct_count_total": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": False
        },
        "observed_or_inferred": {"$ref": "common.json#/definitions/observed_or_inferred"},
        "evidence_references": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": ["string", "null"]},
        "contradictions": {"type": ["string", "null"]},
        "open_questions": {"type": ["string", "null"]},
        "privacy_class": {"$ref": "common.json#/definitions/privacy_class"},
        "privacy_rationale": {"type": "string"},
        "approval_state": {"$ref": "common.json#/definitions/approval_state"},
        "reviewer_role": {"$ref": "common.json#/definitions/reviewer_role"},
        "review_rationale": {"type": ["string", "null"]},
        "created_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "engagement_id", "source_system", "source_table", "object_type", "column_count", "proposed_domain", "proposed_domain_confidence", "observed_or_inferred", "privacy_class", "privacy_rationale", "approval_state", "created_at"],
    "additionalProperties": False
}

# 3. source_attribute_observation.json
schemas["source_attribute_observation.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/source_attribute_observation.json",
    "title": "Source Attribute Observation",
    "description": "Attribute-level facts and proposed semantics",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "engagement_id": {"$ref": "common.json#/definitions/engagement_id"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "source_table": {"$ref": "common.json#/definitions/source_table"},
        "source_column": {"$ref": "common.json#/definitions/source_column"},
        "ordinal_position": {"$ref": "common.json#/definitions/ordinal_position"},
        "physical_type": {"$ref": "common.json#/definitions/physical_type"},
        "nullable": {"$ref": "common.json#/definitions/nullable"},
        "key_role": {"$ref": "common.json#/definitions/key_role"},
        "relationship_evidence": {"type": ["string", "null"], "description": "Inferred relationship description"},
        "proposed_business_name": {"type": "string", "description": "Proposed business-friendly name"},
        "ontology_concept_id": {"type": ["string", "null"], "description": "Proposed ontology concept"},
        "domain": {"$ref": "common.json#/definitions/domain"},
        "observed_or_inferred": {"$ref": "common.json#/definitions/observed_or_inferred"},
        "confidence_score": {"$ref": "common.json#/definitions/confidence_score"},
        "confidence_components": {
            "type": "object",
            "properties": {
                "naming_strength": {"$ref": "common.json#/definitions/confidence_component"},
                "type_strength": {"$ref": "common.json#/definitions/confidence_component"},
                "relationship_strength": {"$ref": "common.json#/definitions/confidence_component"},
                "cots_match_strength": {"$ref": "common.json#/definitions/confidence_component"},
                "standard_consistency": {"$ref": "common.json#/definitions/confidence_component"}
            },
            "required": ["naming_strength", "type_strength", "relationship_strength", "cots_match_strength", "standard_consistency"],
            "additionalProperties": False
        },
        "evidence_coverage": {"$ref": "common.json#/definitions/evidence_coverage"},
        "confidence_reason": {"type": "string"},
        "formula_version": {"type": "string", "description": "Version of the confidence formula"},
        "assumptions": {"type": ["string", "null"]},
        "contradictions": {"type": ["string", "null"]},
        "open_question": {"type": ["string", "null"]},
        "privacy_class": {"$ref": "common.json#/definitions/privacy_class"},
        "privacy_rationale": {"type": "string"},
        "approval_state": {"$ref": "common.json#/definitions/approval_state"},
        "reviewer_role": {"$ref": "common.json#/definitions/reviewer_role"},
        "review_rationale": {"type": ["string", "null"]},
        "created_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "engagement_id", "source_system", "source_table", "source_column", "ordinal_position", "physical_type", "nullable", "key_role", "proposed_business_name", "domain", "observed_or_inferred", "confidence_score", "confidence_components", "evidence_coverage", "confidence_reason", "formula_version", "privacy_class", "privacy_rationale", "approval_state", "created_at"],
    "additionalProperties": False
}

# 4. profile_evidence.json
schemas["profile_evidence.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/profile_evidence.json",
    "title": "Profile Evidence",
    "description": "Approved, minimized profile summaries and evidence references",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "engagement_id": {"$ref": "common.json#/definitions/engagement_id"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "source_table": {"$ref": "common.json#/definitions/source_table"},
        "source_column": {"$ref": "common.json#/definitions/source_column"},
        "profile_type": {"type": "string", "enum": ["NULL_RATE", "DISTINCT_COUNT", "MIN_MAX", "PATTERN_SUMMARY", "CONTROLLED_VALUES"], "description": "Type of profile evidence"},
        "profile_value": {"type": "string", "description": "Profile result as string"},
        "evidence_class": {"type": "string", "enum": ["PHYSICAL_METADATA", "KEY_RELATIONSHIP", "AGGREGATE_PROFILE", "CONTROLLED_VALUE_SUMMARY", "COLUMN_NAME_PATTERN"], "description": "Evidence classification"},
        "is_minimized": {"type": "boolean", "description": "Whether the profile has been minimized per evidence policy"},
        "minimization_rule": {"type": "string", "description": "Minimization rule applied"},
        "observed_or_inferred": {"$ref": "common.json#/definitions/observed_or_inferred"},
        "privacy_class": {"$ref": "common.json#/definitions/privacy_class"},
        "approval_state": {"$ref": "common.json#/definitions/approval_state"},
        "created_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "engagement_id", "source_system", "source_table", "source_column", "profile_type", "profile_value", "evidence_class", "is_minimized", "minimization_rule", "observed_or_inferred", "privacy_class", "approval_state", "created_at"],
    "additionalProperties": False
}

# 5. relationship_candidate.json
schemas["relationship_candidate.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/relationship_candidate.json",
    "title": "Relationship Candidate",
    "description": "Proposed keys/relationships with evidence and confidence",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "engagement_id": {"$ref": "common.json#/definitions/engagement_id"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "from_table": {"$ref": "common.json#/definitions/source_table"},
        "from_column": {"$ref": "common.json#/definitions/source_column"},
        "to_table": {"$ref": "common.json#/definitions/source_table"},
        "to_column": {"$ref": "common.json#/definitions/source_column"},
        "relationship_type": {"type": "string", "enum": ["PRIMARY_KEY", "FOREIGN_KEY", "ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE"], "description": "Type of relationship"},
        "evidence_description": {"type": "string", "description": "Description of evidence supporting this relationship"},
        "naming_overlap": {"type": "boolean", "description": "Whether naming patterns overlap"},
        "type_compatible": {"type": "boolean", "description": "Whether data types are compatible"},
        "overlap_ratio": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0, "description": "Value overlap ratio if computed"},
        "confidence_score": {"$ref": "common.json#/definitions/confidence_score"},
        "confidence_reason": {"type": "string"},
        "observed_or_inferred": {"$ref": "common.json#/definitions/observed_or_inferred"},
        "assumptions": {"type": ["string", "null"]},
        "contradictions": {"type": ["string", "null"]},
        "approval_state": {"$ref": "common.json#/definitions/approval_state"},
        "reviewer_role": {"$ref": "common.json#/definitions/reviewer_role"},
        "review_rationale": {"type": ["string", "null"]},
        "created_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "engagement_id", "source_system", "from_table", "from_column", "to_table", "to_column", "relationship_type", "evidence_description", "naming_overlap", "type_compatible", "confidence_score", "confidence_reason", "observed_or_inferred", "approval_state", "created_at"],
    "additionalProperties": False
}

# 6. review_decision.json
schemas["review_decision.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/review_decision.json",
    "title": "Review Decision",
    "description": "Reviewer decision on a recommendation",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "source_table": {"$ref": "common.json#/definitions/source_table"},
        "source_column": {"$ref": "common.json#/definitions/source_column"},
        "recommendation_type": {"type": "string", "enum": ["SEMANTIC_MAPPING", "RELATIONSHIP", "PRIVACY", "KEY_ROLE", "DOMAIN", "ONTOLOGY"], "description": "Type of recommendation reviewed"},
        "review_reason": {"type": "string", "description": "Why the item was routed to review"},
        "recommended_reviewer_role": {"$ref": "common.json#/definitions/reviewer_role"},
        "reviewer_decision": {"$ref": "common.json#/definitions/approval_state"},
        "reviewer_rationale": {"type": "string", "description": "Why the reviewer made their decision"},
        "prior_recommendation_version": {"type": "string", "description": "Version of the recommendation being reviewed"},
        "invalidation_impact": {"type": ["string", "null"], "description": "Downstream artifacts invalidated by this decision"},
        "queue_status": {"type": "string", "enum": ["OPEN", "CLOSED"]},
        "decided_at": {"$ref": "common.json#/definitions/timestamp_utc"},
        "queued_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "source_table", "source_column", "recommendation_type", "review_reason", "recommended_reviewer_role", "reviewer_decision", "reviewer_rationale", "queue_status", "queued_at"],
    "additionalProperties": False
}

# 7. policy_violation_event.json
schemas["policy_violation_event.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/policy_violation_event.json",
    "title": "Policy Violation Event",
    "description": "Sanitized record of a prohibited-evidence rejection. Contains NO prohibited values.",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "run_id": {"$ref": "common.json#/definitions/run_id"},
        "artifact_version": {"$ref": "common.json#/definitions/artifact_version"},
        "source_system": {"$ref": "common.json#/definitions/source_system"},
        "source_table": {"$ref": "common.json#/definitions/source_table"},
        "source_column": {"$ref": "common.json#/definitions/source_column"},
        "evidence_class_attempted": {"type": "string", "description": "Class of evidence that was attempted (sanitized)"},
        "violation_type": {"type": "string", "enum": ["PII_VALUE_INSPECTION", "PROHIBITED_EVIDENCE", "CREDENTIAL_DETECTED", "CLIENT_DATA", "LICENSED_COTS"], "description": "Type of policy violation"},
        "action_taken": {"type": "string", "enum": ["REJECTED_BEFORE_PROFILE", "REJECTED_BEFORE_RETENTION", "REJECTED_BEFORE_INDEX", "REJECTED_BEFORE_PROMPT"], "description": "Where the violation was caught"},
        "sanitized_description": {"type": "string", "description": "Sanitized description with NO prohibited values"},
        "routed_to": {"$ref": "common.json#/definitions/reviewer_role"},
        "created_at": {"$ref": "common.json#/definitions/timestamp_utc"}
    },
    "required": ["schema_version", "run_id", "artifact_version", "source_system", "source_table", "source_column", "evidence_class_attempted", "violation_type", "action_taken", "sanitized_description", "routed_to", "created_at"],
    "additionalProperties": False
}

# 8. labelled_set.schema.json
schemas["labelled_set.schema.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://agentic-insurance/contracts/labelled_set.schema.json",
    "title": "Labelled Evaluation Set",
    "description": "Schema for the labelled evaluation set used to measure precision and recall",
    "type": "object",
    "properties": {
        "schema_version": {"$ref": "common.json#/definitions/schema_version"},
        "set_name": {"type": "string", "description": "Name of the labelled set"},
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Stable record identifier"},
                    "source_table": {"$ref": "common.json#/definitions/source_table"},
                    "source_column": {"$ref": "common.json#/definitions/source_column"},
                    "expected_business_name": {"type": "string"},
                    "expected_ontology_concept": {"type": ["string", "null"]},
                    "expected_domain": {"$ref": "common.json#/definitions/domain"},
                    "expected_privacy_class": {"$ref": "common.json#/definitions/privacy_class"},
                    "expected_key_role": {"$ref": "common.json#/definitions/key_role"},
                    "expected_relationship_target": {"type": ["string", "null"], "description": "Expected relationship target table.column or null"},
                    "expected_review_route": {"type": ["string", "null"], "enum": [None, "DATA_ARCHITECT", "DOMAIN_STEWARD", "PRIVACY_STEWARD", "NONE"]},
                    "lifecycle_state": {"type": "string", "enum": ["RESOLVED", "UNRESOLVED"], "description": "Whether the expected value is resolved or unresolved"},
                    "strata": {
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string"},
                            "privacy": {"type": "string"},
                            "ambiguity": {"type": "string", "enum": ["KNOWN", "AMBIGUOUS", "UNKNOWN"]},
                            "key_role": {"type": "string"},
                            "relationship": {"type": "string", "enum": ["YES", "NO"]},
                            "pattern_type": {"type": "string", "enum": ["KNOWN", "UNKNOWN"]},
                            "review_route": {"type": "string"}
                        },
                        "additionalProperties": False
                    }
                },
                "required": ["record_id", "source_table", "source_column", "expected_business_name", "expected_domain", "expected_privacy_class", "expected_key_role", "expected_review_route", "lifecycle_state"],
                "additionalProperties": False
            }
        }
    },
    "required": ["schema_version", "set_name", "records"],
    "additionalProperties": False
}

for name, schema in schemas.items():
    path = os.path.join(CONTRACTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Created: {name}")

print(f"\nAll {len(schemas)} contract schemas created.")

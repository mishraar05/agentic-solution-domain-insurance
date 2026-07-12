# Source Documentation Agent

## Purpose

The Source Documentation Agent uses a Databricks-hosted LLM to propose two
human-facing artifacts for every canonical source attribute:

1. a source-column description explaining the apparent business meaning; and
2. a business-glossary term and definition that are independent of the
   physical source name.

The agent is intentionally separate from deterministic metadata extraction,
relationship inference, privacy classification, and confidence calculation.
Its output is a recommendation, never an observed fact or an approval.

## Workflow position

```text
External read-only source tables
        |
        v
Canonical observations + minimized profiles       deterministic
        |
        v
Prompt eligibility and context allow-list          deterministic governance
        |
        +---- prohibited context ----> UNRESOLVED, no LLM call
        |
        v
Databricks ai_query + strict JSON response          LLM-assisted
        |
        v
source_documentation_recommendation                 PROPOSED / UNRESOLVED
        |
        v
Domain Steward review                               human authority
```

The Databricks job entry point is
`src/workflows/source_intelligence/03_generate_source_documentation.py`. Pure,
locally testable prompt and response handling lives in
`src/source_intelligence/source_documentation.py`. The versioned prompt is
`prompts/01_source_documentation_agent.md`.

## Allowed prompt context

Only explicitly copied fields can enter a prompt:

- source system, table, and column names;
- ordinal position, physical type, and nullability;
- deterministic key, relationship, business-name, ontology, and domain
  proposals, labelled as inferences;
- assumptions, contradictions, and open questions;
- minimized aggregate profile evidence such as null rate and distinct count;
- evidence references.

The context builder cannot pass arbitrary metadata or source rows. It rejects
every observation whose privacy class is not `INTERNAL` before prompt
construction, even if a caller supplies profile evidence.

Never permitted in a prompt:

- source row values or record samples;
- personal or sensitive attributes;
- claims narratives;
- credentials or connection strings;
- proprietary COTS documentation;
- arbitrary source comments that have not passed an evidence policy.

## Structured result

The model must return the strict
`source_documentation_model_output.json` shape. The workflow converts that
response into `source_documentation_recommendation.json`, adding:

- the exact run, source attribute, artifact version, and evidence references;
- a SHA-256 fingerprint of the allow-listed context;
- prompt version and model endpoint;
- `PROPOSED` approval state and `DOMAIN_STEWARD` reviewer role;
- creation timestamp and stable recommendation identifier.

The raw prompt and unrestricted model response are not persisted. The model
does not produce a confidence score. Existing deterministic confidence remains
responsible only for workflow routing and never grants approval.

## Resolution rules

`PROPOSED` requires a non-empty column description, glossary term, and glossary
definition. `UNRESOLVED` requires all three to be null and must explain what is
missing or prohibited. Ambiguous AS400 names such as `POLNBR` may be proposed
only when other governed context supports the meaning; otherwise they remain
unresolved for a Domain Steward.

Every result creates a `SOURCE_DOCUMENTATION` review item. A model-generated
proposal therefore reaches a human even when deterministic naming confidence
would otherwise be high.

## Runtime and failure behavior

The model endpoint is supplied through the
`documentation_model_endpoint` bundle variable. The workflow uses serverless
`ai_query`, temperature `0.0`, a bounded output token count, strict structured
output, and per-row endpoint error reporting. Databricks currently documents
serverless compute, a supported Model Serving region, and an accessible model
endpoint as prerequisites for `ai_query`.

If any eligible row receives an endpoint error, the task fails before writing
the output table. A retry with the same run identifier can therefore recover
without partial results. After a successful append, the run-scoped idempotency
guard prevents duplicates.

## Non-goals

The agent does not generate DDL, transformation logic, ingestion, mappings,
target models, migrations, or authoritative glossary content. It does not use
vector search or semantic retrieval. Those remain separately governed future
capabilities.

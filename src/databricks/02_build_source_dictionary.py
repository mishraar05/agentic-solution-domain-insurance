# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 02 — Generate source-observation dictionary
# MAGIC
# MAGIC This deterministic MVP is the first implementation of the Source Intelligence Agent. It profiles physical schema metadata, applies transparent naming rules, and writes proposed semantics with evidence and confidence components.

# COMMAND ----------

from datetime import datetime, timezone
from pyspark.sql import Row
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

def semantic_for(table_name: str, column_name: str) -> dict:
    """Transparent rule set; replace or augment with governed agent/RAG logic later."""
    name = column_name.lower()
    table = table_name.lower().replace("bronze_", "")
    proposed_name = column_name.replace("_", " ").title()
    ontology_concept = None
    domain = "Shared"
    inferred = True
    confidence = 0.55
    reason = "Naming-pattern inference only"

    if "policy" in table or name.startswith("policy_"):
        domain = "Policy"
    elif "claim" in table or name.startswith("claim_") or name == "loss_date":
        domain = "Claims"
    elif "party" in table or "party" in name or "insured" in name:
        domain = "Shared"

    exact = {
        "policy_id": ("Policy Identifier", "Policy.Identifier", "Policy", 0.95),
        "policy_number": ("Policy Number", "Policy.PolicyNumber", "Policy", 0.95),
        "policy_status": ("Policy Status", "Policy.Status", "Policy", 0.90),
        "effective_date": ("Policy Effective Date", "Policy.EffectiveDate", "Policy", 0.90),
        "expiration_date": ("Policy Expiration Date", "Policy.ExpirationDate", "Policy", 0.90),
        "product_code": ("Insurance Product Code", "Product.Code", "Shared", 0.85),
        "insured_party_id": ("Insured Party Identifier", "Party.Identifier", "Shared", 0.85),
        "party_id": ("Party Identifier", "Party.Identifier", "Shared", 0.95),
        "party_type": ("Party Type", "Party.Type", "Shared", 0.90),
        "claim_id": ("Claim Identifier", "Claim.Identifier", "Claims", 0.95),
        "loss_date": ("Loss Date", "Claim.LossDate", "Claims", 0.90),
        "claim_status": ("Claim Status", "Claim.Status", "Claims", 0.90),
        "claimed_amount": ("Claimed Amount", "Claim.ClaimedAmount", "Claims", 0.85),
        "source_updated_ts": ("Source Updated Timestamp", "Technical.SourceUpdatedTimestamp", "Shared", 0.95),
    }
    if name in exact:
        proposed_name, ontology_concept, domain, confidence = exact[name]
        reason = "Approved MVP naming rule"

    privacy = "INTERNAL"
    privacy_reason = "Technical or business metadata; no direct PII detected by MVP rule"
    if any(token in name for token in ("display_name", "email", "phone", "address", "birth", "ssn")):
        privacy = "PERSONAL_DATA"
        privacy_reason = "Column name matches personal-data rule; privacy review required"

    return {
        "proposed_business_name": proposed_name,
        "ontology_concept_id": ontology_concept,
        "domain": domain,
        "observed_or_inferred": "INFERRED" if inferred else "OBSERVED",
        "confidence_score": confidence,
        "confidence_reason": reason,
        "privacy_class": privacy,
        "privacy_rationale": privacy_reason,
    }


def key_role_for(table_name: str, column_name: str) -> str:
    primary_keys = {
        "bronze_policy": "policy_id",
        "bronze_policyholder": "party_id",
        "bronze_claim": "claim_id",
    }
    if primary_keys.get(table_name) == column_name:
        return "PRIMARY_KEY_CANDIDATE"
    if column_name.endswith("_id"):
        return "FOREIGN_KEY_CANDIDATE"
    return "NON_KEY"


def relationship_evidence(table_name: str, column_name: str) -> str:
    if table_name == "bronze_claim" and column_name == "policy_id":
        return "Inferred relationship: bronze_claim.policy_id -> bronze_policy.policy_id"
    if table_name == "bronze_policy" and column_name == "insured_party_id":
        return "Inferred relationship: bronze_policy.insured_party_id -> bronze_policyholder.party_id"
    return None


records = []
created_at = datetime.now(timezone.utc)
for table_name in SOURCE_TABLES:
    source_schema = spark.table(fq_source_table(table_name)).schema
    for ordinal_position, field in enumerate(source_schema.fields, start=1):
        semantic = semantic_for(table_name, field.name)
        relation = relationship_evidence(table_name, field.name)
        naming_strength = 1.0 if semantic["confidence_score"] >= 0.85 else 0.55
        relationship_strength = 0.9 if relation else 0.4
        type_strength = 0.8
        assumptions = None if semantic["ontology_concept_id"] else "Business meaning inferred from naming pattern; steward validation required."
        records.append(Row(
            engagement_id="free-edition-synthetic-mvp",
            source_system=SOURCE_SYSTEM,
            source_table=table_name,
            source_column=field.name,
            ordinal_position=ordinal_position,
            physical_type=str(field.dataType),
            nullable=field.nullable,
            key_role=key_role_for(table_name, field.name),
            relationship_evidence=relation,
            proposed_business_name=semantic["proposed_business_name"],
            ontology_concept_id=semantic["ontology_concept_id"],
            domain=semantic["domain"],
            observed_or_inferred=semantic["observed_or_inferred"],
            confidence_score=float(semantic["confidence_score"]),
            naming_strength=float(naming_strength),
            type_strength=float(type_strength),
            relationship_strength=float(relationship_strength),
            confidence_reason=semantic["confidence_reason"],
            assumptions=assumptions,
            contradictions=None,
            open_question=None if semantic["confidence_score"] >= LOW_CONFIDENCE_THRESHOLD else "Confirm semantic meaning with data steward.",
            privacy_class=semantic["privacy_class"],
            privacy_rationale=semantic["privacy_rationale"],
            approval_state="PROPOSED",
            reviewer_role=None,
            review_rationale=None,
            run_id=RUN_ID,
            artifact_version=ARTIFACT_VERSION,
            created_at=created_at,
        ))

dictionary_schema = StructType([
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_table", StringType(), False),
    StructField("source_column", StringType(), False),
    StructField("ordinal_position", IntegerType(), False),
    StructField("physical_type", StringType(), False),
    StructField("nullable", BooleanType(), False),
    StructField("key_role", StringType(), False),
    StructField("relationship_evidence", StringType(), True),
    StructField("proposed_business_name", StringType(), False),
    StructField("ontology_concept_id", StringType(), True),
    StructField("domain", StringType(), False),
    StructField("observed_or_inferred", StringType(), False),
    StructField("confidence_score", DoubleType(), False),
    StructField("naming_strength", DoubleType(), False),
    StructField("type_strength", DoubleType(), False),
    StructField("relationship_strength", DoubleType(), False),
    StructField("confidence_reason", StringType(), False),
    StructField("assumptions", StringType(), True),
    StructField("contradictions", StringType(), True),
    StructField("open_question", StringType(), True),
    StructField("privacy_class", StringType(), False),
    StructField("privacy_rationale", StringType(), False),
    StructField("approval_state", StringType(), False),
    StructField("reviewer_role", StringType(), True),
    StructField("review_rationale", StringType(), True),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("created_at", TimestampType(), False),
])

dictionary_df = spark.createDataFrame(records, schema=dictionary_schema)
dictionary_df.write.format("delta").mode("overwrite").saveAsTable(fq_table("source_observation_dictionary"))

display(dictionary_df.orderBy("source_table", "ordinal_position"))

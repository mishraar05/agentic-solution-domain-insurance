"""Infer candidate keys and relationships from runtime metadata only.

The engine has no built-in knowledge of available tables, synthetic fixtures,
source products, or client systems. It receives table and column metadata from
the current configured run, identifies structural identifier patterns, and
proposes reviewable candidates. Unknown or abbreviated source conventions stay
unresolved unless governed metadata or a future authorized source-pattern pack
supplies additional evidence.

No function asserts database constraints or referential integrity. Candidate
keys and relationships remain ``PROPOSED`` and require Data Architect review.
"""

import re


LAYER_PREFIXES = {"bronze", "raw", "source", "src", "stage", "staging", "stg"}
IDENTIFIER_SUFFIXES = {"id", "key"}


def _tokens(name):
    """Normalize snake, kebab, spaced, and camel-like names into tokens."""
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(name))
    return tuple(
        token.lower()
        for token in re.split(r"[^A-Za-z0-9]+", separated)
        if token
    )


def _table_entity_tokens(table_name):
    tokens = list(_tokens(table_name))
    while tokens and tokens[0] in LAYER_PREFIXES:
        tokens.pop(0)
    return tuple(tokens)


def identifier_signature(column_name):
    """Return the semantic tail of a conventional identifier name, if any."""
    tokens = _tokens(column_name)
    if not tokens or tokens[-1] not in IDENTIFIER_SUFFIXES:
        return None
    return tokens[-2:] if len(tokens) >= 2 else tokens


def _descriptor(column, ordinal_position):
    if isinstance(column, str):
        return {
            "name": column,
            "nullable": True,
            "ordinal_position": ordinal_position,
        }
    return {
        "name": column["name"],
        "nullable": column.get("nullable", True),
        "ordinal_position": column.get("ordinal_position", ordinal_position),
    }


def infer_key_roles(table_name, columns):
    """Infer one possible primary key and remaining identifier candidates.

    A table-name-aligned non-null identifier is preferred. If no identifier
    matches the table name, the earliest non-null identifier is proposed as the
    primary candidate. This is a transparent heuristic, not a uniqueness claim.
    """
    descriptors = [
        _descriptor(column, position)
        for position, column in enumerate(columns, start=1)
    ]
    roles = {column["name"]: "NON_KEY" for column in descriptors}
    identifiers = [
        column for column in descriptors
        if identifier_signature(column["name"])
    ]
    if not identifiers:
        return roles

    entity_tokens = _table_entity_tokens(table_name)
    aligned = [
        column for column in identifiers
        if _tokens(column["name"])[:-1] == entity_tokens
        or (
            entity_tokens
            and identifier_signature(column["name"])[0] == entity_tokens[-1]
        )
    ]
    candidates = aligned or identifiers
    primary = sorted(
        candidates,
        key=lambda column: (
            column["nullable"],
            column["ordinal_position"],
            column["name"],
        ),
    )[0]
    roles[primary["name"]] = "PRIMARY_KEY_CANDIDATE"
    for column in identifiers:
        if column["name"] != primary["name"]:
            roles[column["name"]] = "FOREIGN_KEY_CANDIDATE"
    return roles


def infer_key_role(table_name, column_name, columns=None):
    """Convenience inference for one column; table-wide metadata is preferred."""
    if columns is not None:
        return infer_key_roles(table_name, columns).get(column_name, "NON_KEY")
    signature = identifier_signature(column_name)
    if not signature:
        return "NON_KEY"
    entity_tokens = _table_entity_tokens(table_name)
    if entity_tokens and signature[0] == entity_tokens[-1]:
        return "PRIMARY_KEY_CANDIDATE"
    return "FOREIGN_KEY_CANDIDATE"


def discover_relationship_candidates(attributes):
    """Discover relationships by identifier signature and physical type.

    ``attributes`` is a list of runtime metadata dictionaries containing table,
    column, physical type, and inferred key role. Multiple plausible targets
    remain multiple candidates so ambiguity reaches human review.
    """
    primary_candidates = [
        attribute for attribute in attributes
        if attribute["key_role"] == "PRIMARY_KEY_CANDIDATE"
    ]
    foreign_candidates = [
        attribute for attribute in attributes
        if attribute["key_role"] == "FOREIGN_KEY_CANDIDATE"
    ]
    relationships = []
    for source in foreign_candidates:
        source_signature = identifier_signature(source["source_column"])
        if source_signature is None:
            continue
        for target in primary_candidates:
            if source["source_table"] == target["source_table"]:
                continue
            target_signature = identifier_signature(target["source_column"])
            exact_name = (
                source["source_column"].lower()
                == target["source_column"].lower()
            )
            signature_match = source_signature == target_signature
            if not (exact_name or signature_match):
                continue
            type_compatible = source["physical_type"] == target["physical_type"]
            naming_strength = 1.0 if exact_name else 0.9
            confidence = (
                0.9 if exact_name and type_compatible
                else 0.85 if signature_match and type_compatible
                else 0.55
            )
            relationships.append({
                "from_table": source["source_table"],
                "from_column": source["source_column"],
                "to_table": target["source_table"],
                "to_column": target["source_column"],
                "naming_overlap": True,
                "naming_strength": naming_strength,
                "type_compatible": type_compatible,
                "confidence_score": confidence,
                "evidence_description": (
                    "Runtime metadata candidate from exact identifier naming."
                    if exact_name
                    else "Runtime metadata candidate from identifier suffix naming."
                ),
                "confidence_reason": (
                    "Identifier naming and physical types are compatible."
                    if type_compatible
                    else "Identifier naming matches but physical types conflict."
                ),
                "contradictions": (
                    None if type_compatible
                    else "Candidate columns have incompatible physical types."
                ),
            })
    return relationships


def relationship_evidence_by_attribute(candidates):
    """Return readable evidence grouped by the candidate source attribute."""
    evidence = {}
    for candidate in candidates:
        key = (candidate["from_table"], candidate["from_column"])
        description = (
            f"Inferred relationship: {candidate['from_table']}."
            f"{candidate['from_column']} -> {candidate['to_table']}."
            f"{candidate['to_column']}"
        )
        evidence.setdefault(key, []).append(description)
    return {
        key: "; ".join(sorted(descriptions))
        for key, descriptions in evidence.items()
    }


def compute_relationship_strength(table_name, column_name, has_relationship):
    """Compute generic relationship evidence strength for confidence scoring."""
    del table_name  # retained for a stable public call shape
    if has_relationship:
        return 0.9
    if identifier_signature(column_name):
        return 0.5
    return 0.4

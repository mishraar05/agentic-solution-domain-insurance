"""Pack-driven semantic classification: rules live in knowledge packs, not code.

Replaces hardcoded EXACT_MATCHES / PII tokens / type keyword groups with
versioned rule packs plus the enriched ontology. Deterministic and auditable:
the same inputs with the same pack versions always produce the same result,
and every inference carries rule_pack_id, rule_version, and rule_id provenance.

Handles separator-free abbreviated names (AS400 style, e.g. POLNBR, CLMSTS,
EFFDT) via greedy longest-match segmentation against the token-expansion rules.
"""
import os
import re
from datetime import date
from itertools import product

from governed_knowledge_foundation.knowledge_pack_io import load_knowledge_pack

_PACK_CACHE = {}
MAX_TOKEN_HYPOTHESES = 32


class RulePackResolutionError(ValueError):
    """Raised when governed selection metadata cannot choose one pack."""


class TokenHypothesisLimitError(ValueError):
    """Raised when ambiguous token expansions exceed the governed limit."""


def _pack_dir(explicit=None):
    return explicit or os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "knowledge_packs"))


def load_pack(relative_path, pack_dir=None):
    path = os.path.join(_pack_dir(pack_dir), relative_path)
    if path not in _PACK_CACHE:
        _PACK_CACHE[path] = load_knowledge_pack(path)
    return _PACK_CACHE[path]


def active_pack_versions(pack_ids=None, pack_dir=None):
    """Return manifest versions for the governed packs used by a run."""
    selected = set(pack_ids) if pack_ids is not None else None
    return {
        entry["pack_id"]: entry["pack_version"]
        for entry in load_pack("manifest.json", pack_dir)["packs"]
        if selected is None or entry["pack_id"] in selected
    }


def detect_naming_convention(column_name):
    """Classify only the physical naming shape; do not infer semantics."""
    if re.search(r"[_\-\s]", column_name):
        return "snake_case"
    if re.search(r"(?<=[a-z0-9])(?=[A-Z])", column_name):
        return "camelCase"
    if column_name.isupper() and column_name.isalnum():
        return "AS400_ABBREVIATED"
    return "snake_case"


def resolve_rule_pack(capability, source_system="*", naming_convention=None,
                      effective_date=None, pack_dir=None):
    """Resolve one governed rule pack using explicit selection precedence.

    Exact source-system and naming-convention matches outrank wildcards; newer
    packs effective on or before ``effective_date`` outrank older packs. An
    equal-precedence tie fails closed instead of depending on manifest order.
    """
    requested_date = (
        date.fromisoformat(effective_date) if effective_date else date.max
    )
    source_key = source_system.casefold()
    convention_key = naming_convention.casefold() if naming_convention else None
    candidates = []
    for entry in load_pack("manifest.json", pack_dir)["packs"]:
        if entry.get("capability") != capability:
            continue
        pack = load_pack(entry["path"], pack_dir)
        selection = pack.get("selection", {})
        sources = [str(value).casefold() for value in selection.get(
            "source_systems", ["*"]
        )]
        if source_key not in sources and "*" not in sources:
            continue
        conventions = [str(value).casefold() for value in selection.get(
            "naming_conventions", ["*"]
        )]
        if convention_key and convention_key not in conventions and "*" not in conventions:
            continue
        pack_date = date.fromisoformat(selection["effective_date"])
        if pack_date > requested_date:
            continue
        score = (
            int(source_key in sources and source_key != "*"),
            int(bool(convention_key) and convention_key in conventions),
            int(entry.get("priority", 0)),
            pack_date.toordinal(),
        )
        candidates.append((score, entry, pack))
    if not candidates:
        raise RulePackResolutionError(
            f"No {capability!r} rule pack applies to source_system="
            f"{source_system!r}, naming_convention={naming_convention!r}, "
            f"effective_date={effective_date!r}."
        )
    candidates.sort(key=lambda item: item[0], reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        tied = sorted(item[1]["pack_id"] for item in candidates if item[0] == candidates[0][0])
        raise RulePackResolutionError(
            f"Ambiguous {capability!r} rule-pack selection: {tied}."
        )
    _, entry, pack = candidates[0]
    return {
        "path": entry["path"],
        "pack": pack,
        "source_system": source_system,
        "naming_convention": naming_convention,
        "effective_date": effective_date,
    }


def _manual_resolution(path, pack, source_system, naming_convention,
                       effective_date):
    return {
        "path": path,
        "pack": pack,
        "source_system": source_system,
        "naming_convention": naming_convention,
        "effective_date": effective_date,
    }


def _provenance(pack, rule_id, resolution=None):
    item = {"rule_pack_id": pack["pack_id"],
            "rule_version": pack["pack_version"], "rule_id": rule_id}
    if resolution:
        item.update({
            "source_system": resolution["source_system"],
            "naming_convention": resolution["naming_convention"],
            "effective_date": resolution["effective_date"],
        })
    return item


def provenance_references(provenance):
    """Serialize applied rules as stable evidence-reference identifiers.

    Rule provenance stays in the existing contract's evidence-reference
    collection, avoiding a Delta table schema change.
    """
    references = {
        "rule:{rule_pack_id}:{rule_version}:{rule_id}".format(**item)
        for item in provenance
    }
    for item in provenance:
        if "source_system" not in item:
            continue
        values = {
            key: re.sub(r"[^A-Za-z0-9._*-]", "_", str(item.get(key) or "AUTO"))
            for key in ("source_system", "naming_convention", "effective_date")
        }
        references.add(
            f"pack_selection:{item['rule_pack_id']}:{item['rule_version']}:"
            f"source={values['source_system']}:"
            f"convention={values['naming_convention']}:"
            f"as_of={values['effective_date']}"
        )
    return sorted(references)


# ---------------------------------------------------------------- tokenization
def segment_column_name_hypotheses(column_name, expansions):
    """Return every governed expansion for a physical column name.

    Segmentation remains greedy by token length, but duplicate token rules are
    retained as competing hypotheses. This prevents ambiguous abbreviations
    such as EXP from silently becoming whichever rule appeared last in YAML.
    """
    known = {}
    for expansion in expansions:
        known.setdefault(expansion["token"].upper(), []).append(expansion)
    rough = re.split(
        r"[_\-\s]+",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", column_name),
    )
    option_groups = []
    for part in filter(None, rough):
        upper = part.upper()
        if upper in known:
            option_groups.append((upper, known[upper]))
            continue
        i, segments = 0, []
        while i < len(upper):
            match = next(
                (upper[i:j] for j in range(len(upper), i, -1)
                 if upper[i:j] in known),
                None,
            )
            if match is None:
                segments = []
                break
            segments.append((match, known[match]))
            i += len(match)
        if segments:
            option_groups.extend(segments)
        else:
            option_groups.append((upper, [{
                "token": upper,
                "expansion": part.lower(),
                "rule_id": None,
            }]))

    count = 1
    for _, options in option_groups:
        count *= len(options)
    if count > MAX_TOKEN_HYPOTHESES:
        raise TokenHypothesisLimitError(
            f"{column_name!r} creates {count} token hypotheses; governed "
            f"limit is {MAX_TOKEN_HYPOTHESES}."
        )

    hypotheses = []
    for choices in product(*(options for _, options in option_groups)):
        hypotheses.append({
            "tokens": [choice["expansion"] for choice in choices],
            "rule_ids": [choice["rule_id"] for choice in choices
                         if choice["rule_id"]],
            "ambiguous_tokens": sorted({
                token for token, options in option_groups if len(options) > 1
            }),
        })
    return hypotheses or [{
        "tokens": [column_name.lower()],
        "rule_ids": [],
        "ambiguous_tokens": [],
    }]


def segment_column_name(column_name, expansions):
    """Backward-compatible primary segmentation; classification uses all hypotheses."""
    hypothesis = segment_column_name_hypotheses(column_name, expansions)[0]
    return hypothesis["tokens"], hypothesis["rule_ids"]


# -------------------------------------------------------------- naming/domain
def _concept_matches(ontology, expanded, strengths):
    matches = []
    token_set = set(expanded.split())
    for concept in ontology["concepts"]:
        names = {
            concept["name"].lower(),
            *[synonym.lower() for synonym in concept.get("synonyms", [])],
        }
        if expanded in names:
            matches.append((strengths["expanded_exact"], concept, "expanded_exact"))
            continue
        target_words = set().union(*(name.split() for name in names))
        if token_set and token_set <= target_words:
            matches.append((strengths["expanded_partial"], concept, "expanded_partial"))
        elif token_set and len(token_set & target_words) / len(token_set) > 0.5:
            matches.append((strengths["token_overlap"], concept, "token_overlap"))
    return matches


def _unresolved_naming(column_name, proposed, pack, resolution, provenance,
                       reason, contradictions=None, candidates=None):
    provenance.append(_provenance(
        pack, pack["matching"]["rule_id"], resolution
    ))
    return {
        "proposed_business_name": proposed or column_name,
        "ontology_concept_id": None,
        "ontology_concept_type": None,
        "domain": "Shared",
        "naming_strength": pack["matching"]["fallback_strength"],
        "reason": reason,
        "provenance": provenance,
        "contradictions": contradictions,
        "semantic_candidates": sorted(set(candidates or [])),
        "requires_semantic_mapper": True,
        "naming_contradicted": contradictions is not None,
    }


def classify_naming_kb(table_name, column_name, pack_dir=None,
                       naming_pack=None,
                       ontology_pack="ontology/insurance_ontology_v1.yaml",
                       source_system="*", naming_convention=None,
                       effective_date=None):
    """Match a column against the ontology using the naming rule pack.

    Returns the proposed name, ontology concept and concept type, domain,
    naming strength, explanation, and applied-rule provenance.
    """
    convention = naming_convention or detect_naming_convention(column_name)
    if naming_pack:
        pack = load_pack(naming_pack, pack_dir)
        resolution = _manual_resolution(
            naming_pack, pack, source_system, convention, effective_date
        )
    else:
        resolution = resolve_rule_pack(
            "naming", source_system, convention, effective_date, pack_dir
        )
        pack = resolution["pack"]
    ontology = load_pack(ontology_pack, pack_dir)
    strengths = pack["matching"]["strengths"]
    hypotheses = segment_column_name_hypotheses(
        column_name, pack["token_expansions"]
    )
    provenance = []
    for rule_id in sorted({
        rule_id for hypothesis in hypotheses
        for rule_id in hypothesis["rule_ids"]
    }):
        provenance.append(_provenance(pack, rule_id, resolution))
    raw = column_name.lower()

    raw_matches = [
        concept for concept in ontology["concepts"]
        if raw in {value.lower() for value in concept.get("physical_name_variants", [])}
    ]
    if len(raw_matches) == 1:
        concept = raw_matches[0]
        provenance.append(_provenance(
            pack, pack["matching"]["rule_id"], resolution
        ))
        return {
            "proposed_business_name": concept["name"],
            "ontology_concept_id": concept["concept_id"],
            "ontology_concept_type": concept["concept_type"],
            "domain": concept["domain"],
            "naming_strength": strengths["variant_exact"],
            "reason": (
                f"Rule-pack match (variant_exact) via {pack['pack_id']} "
                f"v{pack['pack_version']}"
            ),
            "provenance": provenance,
            "contradictions": None,
            "semantic_candidates": [concept["concept_id"]],
            "requires_semantic_mapper": False,
            "naming_contradicted": False,
        }
    if len(raw_matches) > 1:
        candidates = [concept["concept_id"] for concept in raw_matches]
        return _unresolved_naming(
            column_name, column_name, pack, resolution, provenance,
            "Multiple ontology concepts declare the same physical variant.",
            f"Physical variant {column_name!r} maps to multiple governed concepts: "
            f"{', '.join(sorted(candidates))}.",
            candidates,
        )

    expanded_values = [" ".join(hypothesis["tokens"]) for hypothesis in hypotheses]
    ambiguous_tokens = sorted({
        token for hypothesis in hypotheses
        for token in hypothesis["ambiguous_tokens"]
    })
    matches = []
    for expanded in expanded_values:
        matches.extend(_concept_matches(ontology, expanded, strengths))
    candidates = sorted({match[1]["concept_id"] for match in matches})
    proposed = expanded_values[0].title() if expanded_values else column_name
    if ambiguous_tokens:
        alternatives = ", ".join(sorted(set(expanded_values)))
        candidate_text = ", ".join(candidates) if candidates else "none"
        contradiction = (
            f"Ambiguous token(s) {', '.join(ambiguous_tokens)} have governed "
            f"expansions: {alternatives}. Closed ontology candidates: "
            f"{candidate_text}."
        )
        return _unresolved_naming(
            column_name, column_name, pack, resolution, provenance,
            "Ambiguous token expansion; closed-candidate semantic mapping "
            "or steward review required.",
            contradiction, candidates,
        )
    if matches:
        top_strength = max(match[0] for match in matches)
        top = {
            match[1]["concept_id"]: match
            for match in matches if match[0] == top_strength
        }
        if len(top) > 1:
            tied = sorted(top)
            return _unresolved_naming(
                column_name, proposed, pack, resolution, provenance,
                "Equal-strength ontology matches; steward review required.",
                f"Equal-strength ontology candidates: {', '.join(tied)}.", tied,
            )
        _, concept, kind = next(iter(top.values()))
        provenance.append(_provenance(
            pack, pack["matching"]["rule_id"], resolution
        ))
        business_name = proposed if kind == "token_overlap" else concept["name"]
        return {
            "proposed_business_name": business_name,
            "ontology_concept_id": concept["concept_id"],
            "ontology_concept_type": concept["concept_type"],
            "domain": concept["domain"],
            "naming_strength": top_strength,
            "reason": f"Rule-pack match ({kind}) via {pack['pack_id']} v{pack['pack_version']}",
            "provenance": provenance,
            "contradictions": None,
            "semantic_candidates": [concept["concept_id"]],
            "requires_semantic_mapper": False,
            "naming_contradicted": False,
        }
    fallback_name = (
        column_name
        if convention == "AS400_ABBREVIATED"
        and not any(hypothesis["rule_ids"] for hypothesis in hypotheses)
        else proposed
    )
    return _unresolved_naming(
        column_name, fallback_name, pack, resolution, provenance,
        "No rule-pack match; expanded name only; steward review required.",
    )


# -------------------------------------------------------------------- privacy
def classify_privacy_kb(column_name, pack_dir=None,
                        privacy_pack=None, naming_pack=None,
                        source_system="*", naming_convention=None,
                        effective_date=None):
    """Classify privacy from the rule pack. Returns (class, rationale, provenance)."""
    convention = naming_convention or detect_naming_convention(column_name)
    if privacy_pack:
        pack = load_pack(privacy_pack, pack_dir)
        resolution = _manual_resolution(
            privacy_pack, pack, source_system, convention, effective_date
        )
    else:
        resolution = resolve_rule_pack(
            "privacy", source_system, convention, effective_date, pack_dir
        )
        pack = resolution["pack"]
    if naming_pack:
        naming = load_pack(naming_pack, pack_dir)
    else:
        naming = resolve_rule_pack(
            "naming", source_system, convention, effective_date, pack_dir
        )["pack"]
    hypotheses = segment_column_name_hypotheses(
        column_name, naming["token_expansions"]
    )
    raw = column_name.lower()
    results = []
    for hypothesis in hypotheses:
        expanded = " ".join(hypothesis["tokens"])
        matched = None
        for exception in pack.get("exceptions", []):
            subject = expanded if exception["match_on"] == "expanded" else raw
            if re.search(exception["pattern"], subject):
                matched = exception
                break
        if matched is None:
            for rule in pack["rules"]:
                subject = expanded if rule["match_on"] == "expanded" else raw
                if re.search(rule["pattern"], subject):
                    matched = rule
                    break
        results.append(matched or pack["default"])
    rank = {"INTERNAL": 0, "PERSONAL_DATA": 1, "SENSITIVE": 2, "RESTRICTED": 3}
    selected = max(results, key=lambda item: rank.get(item["privacy_class"], 3))
    return (selected["privacy_class"], selected["rationale"],
            [_provenance(pack, selected["rule_id"], resolution)])


# ---------------------------------------------------------------------- types
def check_type_compatibility_kb(physical_type, concept_type, pack_dir=None,
                                type_pack=None, source_system="*",
                                naming_convention=None, effective_date=None):
    """Type strength from concept_type vs physical family. Returns (strength, provenance)."""
    if type_pack:
        pack = load_pack(type_pack, pack_dir)
        resolution = _manual_resolution(
            type_pack, pack, source_system, naming_convention, effective_date
        )
    else:
        resolution = resolve_rule_pack(
            "type", source_system, naming_convention, effective_date, pack_dir
        )
        pack = resolution["pack"]
    families = pack["type_families"]
    compat = pack["compatibility"]
    family = None
    for name, markers in families.items():
        if any(marker in str(physical_type) for marker in markers):
            family = name
            break
    provenance = [_provenance(pack, compat["rule_id"], resolution)]
    expected = compat["expected"].get(concept_type or "ATTRIBUTE", [])
    if family is None:
        return compat["strengths"]["tolerated"], provenance
    if family in expected:
        return compat["strengths"]["match"], provenance
    if family == "STRING":
        return compat["strengths"]["tolerated"], provenance
    return compat["strengths"]["mismatch"], provenance

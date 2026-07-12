"""Provide deterministic quality and idempotency helpers for synthetic tests.

The functions navigate machine-readable fixture tables, inspect nulls,
duplicates, orphan relationships, and type conflicts, and derive stable hashes
from canonicalized inputs. They also map fixture issues to governed reviewer
roles. This module operates only on isolated synthetic structures and is not a
production source-data profiling service.
"""

import hashlib
import json


def get_table(tables, table_name):
    """Return a named table fixture or raise a precise error."""
    for table in tables:
        if table["name"] == table_name:
            return table
    raise KeyError(f"Fixture table not found: {table_name}")


def get_column(table, column_name):
    """Return a named column definition."""
    for column in table["columns"]:
        if column["name"] == column_name:
            return column
    raise KeyError(f"Fixture column not found: {table['name']}.{column_name}")


def column_values(table, column_name):
    return [row.get(column_name) for row in table["rows"]]


def has_null_or_empty(values):
    return any(value is None or value == "" for value in values)


def has_duplicates(values):
    usable = [value for value in values if value is not None and value != ""]
    return len(usable) != len(set(usable))


def orphan_values(child_values, parent_values):
    parent = {value for value in parent_values if value is not None}
    return sorted({value for value in child_values if value is not None and value not in parent}, key=str)


def canonical_input_key(tables):
    """Create a stable input-derived key independent of dictionary ordering."""
    payload = json.dumps(tables, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relationship_columns(fixture):
    target = fixture["target"]
    child = get_table(fixture["input"]["tables"], target["table"])
    child_column = get_column(child, target["column"])
    parent_table_name, parent_column_name = target["relationship_target"].split(".", 1)
    parent = get_table(fixture["input"]["tables"], parent_table_name)
    parent_column = get_column(parent, parent_column_name)
    return child, child_column, parent, parent_column


def review_for_issues(issues, privacy_class="INTERNAL"):
    """Route deterministic quality findings without granting approval."""
    if privacy_class != "INTERNAL" or "PROHIBITED_EVIDENCE" in issues:
        return "PRIVACY_STEWARD", "privacy or prohibited evidence requires review"
    architect_issues = {
        "DUPLICATE_IDENTIFIER", "MISSING_PRIMARY_KEY", "ORPHAN_FOREIGN_KEY",
        "RELATIONSHIP_TYPE_MISMATCH",
    }
    if architect_issues.intersection(issues):
        issue = sorted(architect_issues.intersection(issues))[0]
        return "DATA_ARCHITECT", issue.replace("_", " ").lower()
    if "NULL_OR_EMPTY_VALUE" in issues:
        return "DOMAIN_STEWARD", "incomplete source values require review"
    if issues:
        issue = sorted(issues)[0]
        return "DOMAIN_STEWARD", issue.replace("_", " ").lower()
    return None, None

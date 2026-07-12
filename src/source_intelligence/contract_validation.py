"""Validate producer records against the repository's JSON contracts.

Every workflow producer calls this module before persistence so malformed or
incomplete recommendations fail at the write boundary. The dependency-free
validator resolves local and cross-file ``$ref`` values rooted at ``contracts``
and implements the schema features used by this project: types, enums,
constants, patterns, required properties, additional properties, arrays,
objects, item limits, and numeric bounds. It validates logical records before
Spark-specific serialization changes timestamps or nested objects.
"""
import json
import os
import re

_SCHEMA_CACHE = {}

TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _contracts_dir(explicit=None):
    if explicit:
        return explicit
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "contracts"))


def load_contract(name, contracts_dir=None):
    """Load a contract JSON by filename (cached)."""
    directory = _contracts_dir(contracts_dir)
    path = os.path.join(directory, name)
    if path not in _SCHEMA_CACHE:
        with open(path, "r", encoding="utf-8") as handle:
            _SCHEMA_CACHE[path] = json.load(handle)
    return _SCHEMA_CACHE[path]


def _resolve_ref(reference, root_schema, contracts_dir):
    """Resolve '#/...', 'file.json#/...' references."""
    if reference.startswith("#/"):
        node = root_schema
        pointer = reference[2:]
    else:
        file_part, _, pointer = reference.partition("#/")
        node = load_contract(file_part, contracts_dir)
        root_schema = node
    for token in pointer.split("/"):
        if token:
            node = node[token.replace("~1", "/").replace("~0", "~")]
    return node, root_schema


class ContractValidationError(AssertionError):
    pass


def validate_instance(value, schema, root_schema=None, path="$", contracts_dir=None):
    """Validate value against schema; raises ContractValidationError on failure."""
    root_schema = root_schema if root_schema is not None else schema
    if "$ref" in schema:
        resolved, new_root = _resolve_ref(schema["$ref"], root_schema, contracts_dir)
        return validate_instance(value, resolved, new_root, path, contracts_dir)
    if "const" in schema and value != schema["const"]:
        raise ContractValidationError(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractValidationError(f"{path}: {value!r} not in enum {schema['enum']}")
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(TYPE_CHECKS[t](value) for t in allowed):
            raise ContractValidationError(
                f"{path}: expected type {allowed}, got {type(value).__name__}")
    if "pattern" in schema and isinstance(value, str):
        if not re.search(schema["pattern"], value):
            raise ContractValidationError(f"{path}: {value!r} does not match {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractValidationError(f"{path}: {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractValidationError(f"{path}: {value} above maximum {schema['maximum']}")
    if isinstance(value, dict):
        missing = [k for k in schema.get("required", []) if k not in value]
        if missing:
            raise ContractValidationError(f"{path}: missing required keys {missing}")
        props = schema.get("properties", {})
        extra = [key for key in value if key not in props]
        additional = schema.get("additionalProperties")
        if additional is False:
            if extra:
                raise ContractValidationError(f"{path}: additional properties not allowed: {extra}")
        elif isinstance(additional, dict):
            for key in extra:
                validate_instance(
                    value[key], additional, root_schema,
                    f"{path}.{key}", contracts_dir,
                )
        for key, subschema in props.items():
            if key in value:
                validate_instance(value[key], subschema, root_schema, f"{path}.{key}", contracts_dir)
    if isinstance(value, list) and "items" in schema:
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ContractValidationError(
                f"{path}: expected at least {schema['minItems']} item(s)"
            )
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ContractValidationError(
                f"{path}: expected at most {schema['maxItems']} item(s)"
            )
        for index, item in enumerate(value):
            validate_instance(item, schema["items"], root_schema, f"{path}[{index}]", contracts_dir)


def validate_records(records, contract_name, contracts_dir=None):
    """Validate a list of contract-shaped dicts; raises on the first failure."""
    schema = load_contract(contract_name, contracts_dir)
    for index, record in enumerate(records):
        validate_instance(record, schema, path=f"record[{index}]", contracts_dir=contracts_dir)
    return len(records)

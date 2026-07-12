"""Small dependency-free validator for the JSON Schema features used by fixtures."""

import re


TYPE_CHECKS = {
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "null": lambda value: value is None,
}


def _resolve_ref(root_schema, reference):
    assert reference.startswith("#/"), f"Only local refs are supported: {reference}"
    node = root_schema
    for token in reference[2:].split("/"):
        node = node[token.replace("~1", "/").replace("~0", "~")]
    return node


def validate_instance(value, schema, root_schema=None, path="$"):
    """Validate the subset used by expanded_synthetic_fixtures.schema.json."""
    root_schema = root_schema or schema
    if "$ref" in schema:
        return validate_instance(value, _resolve_ref(root_schema, schema["$ref"]), root_schema, path)
    if "const" in schema:
        assert value == schema["const"], f"{path}: expected constant {schema['const']!r}"
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: {value!r} not in enum"
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        assert any(TYPE_CHECKS[item](value) for item in allowed), f"{path}: expected type {allowed}, got {type(value).__name__}"
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        assert not missing, f"{path}: missing required keys {missing}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            assert not extra, f"{path}: unexpected keys {sorted(extra)}"
        for key, child in value.items():
            if key in properties:
                validate_instance(child, properties[key], root_schema, f"{path}.{key}")
    if isinstance(value, list):
        assert len(value) >= schema.get("minItems", 0), f"{path}: too few items"
        if schema.get("uniqueItems"):
            serialized = [repr(item) for item in value]
            assert len(serialized) == len(set(serialized)), f"{path}: items are not unique"
        if "items" in schema:
            for index, item in enumerate(value):
                validate_instance(item, schema["items"], root_schema, f"{path}[{index}]")
    if isinstance(value, str):
        assert len(value) >= schema.get("minLength", 0), f"{path}: string is too short"
        if "pattern" in schema:
            assert re.search(schema["pattern"], value), f"{path}: value does not match pattern"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema:
            assert value >= schema["minimum"], f"{path}: below minimum"
        if "maximum" in schema:
            assert value <= schema["maximum"], f"{path}: above maximum"

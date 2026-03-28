"""Infer JSON schemas from sample data."""

from __future__ import annotations

import re
from typing import Any


__all__ = [
    "infer",
    "infer_type",
    "merge_schemas",
    "to_json_schema",
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URI_RE = re.compile(r"^https?://")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def infer(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Infer a JSON Schema from a list of sample dicts.

    Args:
        samples: List of dictionaries to analyze.

    Returns:
        JSON Schema (dict) compatible with draft-07.
    """
    if not samples:
        return {"type": "object", "properties": {}}

    all_keys: dict[str, list[Any]] = {}
    key_counts: dict[str, int] = {}

    for sample in samples:
        for key, value in sample.items():
            all_keys.setdefault(key, []).append(value)
            key_counts[key] = key_counts.get(key, 0) + 1

    properties: dict[str, Any] = {}
    required: list[str] = []
    total = len(samples)

    for key, values in all_keys.items():
        properties[key] = _infer_from_values(values)
        if key_counts[key] == total:
            required.append(key)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = sorted(required)

    return schema


def infer_type(value: Any) -> dict[str, Any]:
    """Infer a JSON Schema type for a single value.

    Args:
        value: Any JSON-compatible value.

    Returns:
        JSON Schema type descriptor.
    """
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        schema: dict[str, Any] = {"type": "string"}
        fmt = _detect_format(value)
        if fmt:
            schema["format"] = fmt
        return schema
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        item_schemas = [infer_type(item) for item in value]
        return {"type": "array", "items": _merge_type_list(item_schemas)}
    if isinstance(value, dict):
        properties = {k: infer_type(v) for k, v in value.items()}
        return {
            "type": "object",
            "properties": properties,
            "required": sorted(properties.keys()),
        }

    return {}


def merge_schemas(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merge two JSON Schemas into one that accepts values valid for either.

    Args:
        a: First schema.
        b: Second schema.

    Returns:
        Merged schema.
    """
    if not a:
        return b
    if not b:
        return a

    type_a = a.get("type")
    type_b = b.get("type")

    if type_a == type_b == "object":
        return _merge_object_schemas(a, b)

    if type_a == type_b:
        return dict(a)

    # Different types -> anyOf
    return {"anyOf": [a, b]}


def to_json_schema(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Infer a JSON Schema from samples and wrap with a ``$schema`` URI.

    Args:
        samples: List of dictionaries to analyze.

    Returns:
        Full JSON Schema document with ``$schema`` key.
    """
    schema = infer(samples)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **schema,
    }


def _infer_from_values(values: list[Any]) -> dict[str, Any]:
    schemas = [infer_type(v) for v in values]
    merged = _merge_type_list(schemas)

    # Detect enums for small sets of strings
    if merged.get("type") == "string":
        unique_values = set(values)
        if 2 <= len(unique_values) <= 10 and len(values) >= 3:
            merged["enum"] = sorted(unique_values)

    # Track numeric constraints
    if merged.get("type") in ("integer", "number"):
        numeric_values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric_values:
            merged["minimum"] = min(numeric_values)
            merged["maximum"] = max(numeric_values)

    # Track string length constraints
    if merged.get("type") == "string":
        string_values = [v for v in values if isinstance(v, str)]
        if string_values:
            lengths = [len(s) for s in string_values]
            merged["minLength"] = min(lengths)
            merged["maxLength"] = max(lengths)

    return merged


def _merge_type_list(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    if not schemas:
        return {}
    if len(schemas) == 1:
        return schemas[0]

    types: set[str] = set()
    for s in schemas:
        t = s.get("type")
        if t:
            types.add(t)

    if len(types) == 1:
        return schemas[0]

    # integer + number -> number
    if types == {"integer", "number"}:
        return {"type": "number"}

    # Multiple types
    if types:
        unique = _dedupe_schemas(schemas)
        if len(unique) == 1:
            return unique[0]
        return {"anyOf": unique}

    return schemas[0]


def _dedupe_schemas(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: list[dict[str, Any]] = []
    for s in schemas:
        if s not in seen:
            seen.append(s)
    return seen


def _merge_object_schemas(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    props_a = a.get("properties", {})
    props_b = b.get("properties", {})
    req_a = set(a.get("required", []))
    req_b = set(b.get("required", []))

    all_keys = set(props_a) | set(props_b)
    properties: dict[str, Any] = {}

    for key in all_keys:
        if key in props_a and key in props_b:
            properties[key] = merge_schemas(props_a[key], props_b[key])
        elif key in props_a:
            properties[key] = props_a[key]
        else:
            properties[key] = props_b[key]

    # Required only if required in both
    required = sorted(req_a & req_b)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def _detect_format(value: str) -> str | None:
    if _EMAIL_RE.match(value):
        return "email"
    if _URI_RE.match(value):
        return "uri"
    if _UUID_RE.match(value):
        return "uuid"
    if _DATETIME_RE.match(value):
        return "date-time"
    if _DATE_RE.match(value):
        return "date"
    return None

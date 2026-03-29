"""Infer JSON schemas from sample data."""

from __future__ import annotations

import re
from typing import Any, Literal

__all__ = [
    "infer",
    "infer_type",
    "merge_schemas",
    "register_format",
    "to_json_schema",
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URI_RE = re.compile(r"^https?://")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_custom_formats: dict[str, re.Pattern[str]] = {}

Strictness = Literal["loose", "normal", "strict"]


def register_format(name: str, pattern: str) -> None:
    """Register a custom format detector.

    After registration, strings matching *pattern* will have their schema
    ``format`` set to *name*.

    Args:
        name: Format name (e.g. ``"phone"``, ``"credit-card"``).
        pattern: Regular expression that matches the format.
    """
    _custom_formats[name] = re.compile(pattern)


def infer(
    samples: list[dict[str, Any]],
    *,
    strictness: Strictness = "normal",
) -> dict[str, Any]:
    """Infer a JSON Schema from a list of sample dicts.

    Args:
        samples: List of dictionaries to analyze.
        strictness: Controls how aggressively fields are marked required and
            constraints are applied.

            * ``"loose"`` -- no fields are required, no numeric/string
              constraints.
            * ``"normal"`` -- fields present in *all* samples are required,
              constraints are included (default).
            * ``"strict"`` -- fields present in *any* sample are required,
              constraints are included, and ``additionalProperties`` is
              ``False``.

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
        properties[key] = _infer_from_values(values, strictness)
        if strictness == "strict":
            required.append(key)
        elif strictness == "normal" and key_counts[key] == total:
            required.append(key)
        # loose: never add to required

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = sorted(required)
    if strictness == "strict":
        schema["additionalProperties"] = False

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


def merge_schemas(*schemas: dict[str, Any]) -> dict[str, Any]:
    """Merge one or more JSON Schemas into one that accepts values valid for any.

    When called with two schemas this behaves identically to the previous
    two-argument version.  With more than two schemas the merge is applied
    left-to-right (i.e. ``merge_schemas(a, b, c)`` equals
    ``merge_schemas(merge_schemas(a, b), c)``).

    Args:
        *schemas: Two or more schemas to merge.

    Returns:
        Merged schema.

    Raises:
        TypeError: If fewer than two schemas are provided.
    """
    if len(schemas) < 2:
        raise TypeError(
            f"merge_schemas expected at least 2 schemas, got {len(schemas)}"
        )

    result = schemas[0]
    for other in schemas[1:]:
        result = _merge_two(result, other)
    return result


def to_json_schema(
    samples: list[dict[str, Any]],
    *,
    strictness: Strictness = "normal",
) -> dict[str, Any]:
    """Infer a JSON Schema from samples and wrap with a ``$schema`` URI.

    Args:
        samples: List of dictionaries to analyze.
        strictness: Passed through to :func:`infer`.

    Returns:
        Full JSON Schema document with ``$schema`` key.
    """
    schema = infer(samples, strictness=strictness)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **schema,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _infer_from_values(
    values: list[Any],
    strictness: Strictness = "normal",
) -> dict[str, Any]:
    schemas = [infer_type(v) for v in values]
    merged = _merge_type_list(schemas)

    # Detect enums for small sets of strings
    if merged.get("type") == "string":
        unique_values = set(values)
        if 2 <= len(unique_values) <= 10 and len(values) >= 3:
            merged["enum"] = sorted(unique_values)

    if strictness == "loose":
        return merged

    # Track numeric constraints
    if merged.get("type") in ("integer", "number"):
        numeric_values = [
            v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)
        ]
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


def _merge_two(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merge exactly two schemas."""
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
            properties[key] = _merge_two(props_a[key], props_b[key])
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
    # Check custom formats first (user-registered take priority)
    for name, pattern in _custom_formats.items():
        if pattern.search(value):
            return name

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

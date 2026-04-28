import pytest

from philiprehberger_schema_infer import (
    infer,
    infer_from_jsonl,
    infer_type,
    infer_with_confidence,
    merge_schemas,
    register_format,
    to_dataclass,
    to_json_schema,
    to_typescript,
)
from philiprehberger_schema_infer import _custom_formats


def test_infer_simple():
    samples = [{"name": "Alice", "age": 30}]
    schema = infer(samples)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"


def test_infer_required():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    schema = infer(samples)
    assert "name" in schema["required"]
    assert "age" in schema["required"]


def test_infer_optional_field():
    samples = [
        {"name": "Alice", "email": "a@b.com"},
        {"name": "Bob"},
    ]
    schema = infer(samples)
    assert "name" in schema["required"]
    assert "email" not in schema.get("required", [])


def test_infer_type_string():
    assert infer_type("hello")["type"] == "string"


def test_infer_type_integer():
    assert infer_type(42)["type"] == "integer"


def test_infer_type_float():
    assert infer_type(3.14)["type"] == "number"


def test_infer_type_boolean():
    assert infer_type(True)["type"] == "boolean"


def test_infer_type_null():
    assert infer_type(None)["type"] == "null"


def test_infer_type_list():
    schema = infer_type([1, 2, 3])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "integer"


def test_infer_type_nested_object():
    schema = infer_type({"a": 1})
    assert schema["type"] == "object"
    assert "a" in schema["properties"]


def test_infer_email_format():
    schema = infer_type("user@example.com")
    assert schema.get("format") == "email"


def test_infer_uri_format():
    schema = infer_type("https://example.com")
    assert schema.get("format") == "uri"


def test_infer_date_format():
    schema = infer_type("2026-03-10")
    assert schema.get("format") == "date"


def test_infer_datetime_format():
    schema = infer_type("2026-03-10T14:30:00Z")
    assert schema.get("format") == "date-time"


def test_infer_uuid_format():
    schema = infer_type("550e8400-e29b-41d4-a716-446655440000")
    assert schema.get("format") == "uuid"


def test_merge_same_type():
    a = {"type": "string"}
    b = {"type": "string"}
    result = merge_schemas(a, b)
    assert result["type"] == "string"


def test_merge_different_types():
    a = {"type": "string"}
    b = {"type": "integer"}
    result = merge_schemas(a, b)
    assert "anyOf" in result


def test_merge_objects():
    a = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
    b = {"type": "object", "properties": {"y": {"type": "string"}}, "required": ["y"]}
    result = merge_schemas(a, b)
    assert "x" in result["properties"]
    assert "y" in result["properties"]


def test_infer_empty():
    schema = infer([])
    assert schema["type"] == "object"


# --- Custom format registration ---


def test_register_format_phone():
    _custom_formats.clear()
    register_format("phone", r"^\+\d{1,3}-\d{3,14}$")
    schema = infer_type("+1-5551234567")
    assert schema.get("format") == "phone"
    _custom_formats.clear()


def test_register_format_credit_card():
    _custom_formats.clear()
    register_format("credit-card", r"^\d{4}-\d{4}-\d{4}-\d{4}$")
    schema = infer_type("4111-1111-1111-1111")
    assert schema.get("format") == "credit-card"
    _custom_formats.clear()


def test_custom_format_takes_priority():
    _custom_formats.clear()
    # Register a format that matches email-like strings
    register_format("custom-email", r"^[^@]+@[^@]+$")
    schema = infer_type("user@example.com")
    assert schema.get("format") == "custom-email"
    _custom_formats.clear()


def test_builtin_formats_still_work_without_custom():
    _custom_formats.clear()
    assert infer_type("user@example.com").get("format") == "email"
    assert infer_type("https://example.com").get("format") == "uri"


# --- Strictness levels ---


def test_strictness_loose_no_required():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    schema = infer(samples, strictness="loose")
    assert "required" not in schema


def test_strictness_loose_no_constraints():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    schema = infer(samples, strictness="loose")
    assert "minimum" not in schema["properties"]["age"]
    assert "maximum" not in schema["properties"]["age"]
    assert "minLength" not in schema["properties"]["name"]
    assert "maxLength" not in schema["properties"]["name"]


def test_strictness_normal_default():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    schema = infer(samples)
    assert "name" in schema["required"]
    assert "minimum" in schema["properties"]["age"]


def test_strictness_strict_all_required():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob"},
    ]
    schema = infer(samples, strictness="strict")
    assert "name" in schema["required"]
    assert "age" in schema["required"]
    assert schema["additionalProperties"] is False


def test_strictness_strict_additional_properties_false():
    samples = [{"x": 1}]
    schema = infer(samples, strictness="strict")
    assert schema["additionalProperties"] is False


# --- Variadic merge_schemas ---


def test_merge_three_schemas():
    a = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
    b = {"type": "object", "properties": {"y": {"type": "string"}}, "required": ["y"]}
    c = {"type": "object", "properties": {"z": {"type": "boolean"}}, "required": ["z"]}
    result = merge_schemas(a, b, c)
    assert "x" in result["properties"]
    assert "y" in result["properties"]
    assert "z" in result["properties"]
    # No field is required in all three
    assert "required" not in result or result.get("required") == []


def test_merge_schemas_requires_at_least_two():
    try:
        merge_schemas({"type": "string"})
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_merge_schemas_union_required():
    a = {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "string"}}, "required": ["x", "y"]}
    b = {"type": "object", "properties": {"x": {"type": "integer"}, "z": {"type": "boolean"}}, "required": ["x", "z"]}
    result = merge_schemas(a, b)
    # x is required in both, so it stays required
    assert "x" in result["required"]
    # y and z are only in one each, so not required
    assert "y" not in result.get("required", [])
    assert "z" not in result.get("required", [])


# --- to_json_schema ---


def test_to_json_schema_includes_schema_uri():
    samples = [{"name": "Alice"}]
    schema = to_json_schema(samples)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"


def test_to_json_schema_passes_strictness():
    samples = [{"name": "Alice"}, {"name": "Bob"}]
    schema = to_json_schema(samples, strictness="loose")
    assert "required" not in schema


# --- Confidence scores ---


def test_infer_with_confidence_consistent_types():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Carol", "age": 35},
    ]
    result = infer_with_confidence(samples)
    assert result["name"]["confidence"] == 1.0
    assert result["age"]["confidence"] == 1.0
    assert result["name"]["type"] == "string"
    assert result["age"]["type"] == "integer"


def test_infer_with_confidence_mixed_types():
    samples = [
        {"value": 42},
        {"value": "hello"},
        {"value": 99},
    ]
    result = infer_with_confidence(samples)
    # 2 out of 3 are integers => confidence ~0.67
    assert result["value"]["confidence"] == 0.67


def test_infer_with_confidence_all_same():
    samples = [
        {"flag": True},
        {"flag": False},
        {"flag": True},
    ]
    result = infer_with_confidence(samples)
    assert result["flag"]["confidence"] == 1.0
    assert result["flag"]["type"] == "boolean"


def test_infer_with_confidence_empty():
    result = infer_with_confidence([])
    assert result == {}


def test_infer_with_confidence_single_sample():
    samples = [{"x": 1}]
    result = infer_with_confidence(samples)
    assert result["x"]["confidence"] == 1.0


def test_infer_with_confidence_partial_fields():
    samples = [
        {"a": 1, "b": "hello"},
        {"a": 2},
    ]
    result = infer_with_confidence(samples)
    assert "a" in result
    assert "b" in result
    assert result["a"]["confidence"] == 1.0
    assert result["b"]["confidence"] == 1.0


# --- TypeScript interface output ---


def test_to_typescript_basic():
    samples = [
        {"name": "Alice", "age": 30, "active": True},
    ]
    ts = to_typescript(samples, name="User")
    assert "interface User {" in ts
    assert "name: string;" in ts
    assert "age: number;" in ts
    assert "active: boolean;" in ts
    assert ts.endswith("}")


def test_to_typescript_optional_fields():
    samples = [
        {"name": "Alice", "email": "a@b.com"},
        {"name": "Bob"},
    ]
    ts = to_typescript(samples, name="Person")
    assert "name: string;" in ts
    assert "email?: string;" in ts


def test_to_typescript_default_name():
    samples = [{"x": 1}]
    ts = to_typescript(samples)
    assert "interface InferredType {" in ts


def test_to_typescript_array_field():
    samples = [{"tags": ["a", "b", "c"]}]
    ts = to_typescript(samples, name="Item")
    assert "tags: string[];" in ts


def test_to_typescript_empty_properties():
    samples: list[dict[str, object]] = []
    ts = to_typescript(samples, name="Empty")
    assert "interface Empty {" in ts
    assert ts.strip().endswith("}")


def test_to_typescript_null_field():
    samples = [{"value": None}]
    ts = to_typescript(samples, name="Nullable")
    assert "value: null;" in ts


def test_to_typescript_nested_object():
    samples = [{"address": {"city": "NYC", "zip": "10001"}}]
    ts = to_typescript(samples, name="Contact")
    assert "interface Contact {" in ts
    # The nested object renders as an inline object type
    assert "city: string;" in ts
    assert "zip: string;" in ts


def test_to_typescript_strictness_strict():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob"},
    ]
    ts = to_typescript(samples, name="Strict", strictness="strict")
    # In strict mode, all fields are required (no ?)
    assert "name: string;" in ts
    assert "age: number;" in ts
    assert "?" not in ts


# --- Python dataclass output ---


def test_to_dataclass_basic():
    samples = [
        {"name": "Alice", "age": 30, "active": True},
    ]
    code = to_dataclass(samples, name="User")
    assert "@dataclass" in code
    assert "class User:" in code
    assert "name: str" in code
    assert "age: int" in code
    assert "active: bool" in code


def test_to_dataclass_optional_fields():
    samples = [
        {"name": "Alice", "email": "a@b.com"},
        {"name": "Bob"},
    ]
    code = to_dataclass(samples, name="Person")
    assert "name: str" in code
    assert "email: str | None = None" in code


def test_to_dataclass_default_name():
    samples = [{"x": 1}]
    code = to_dataclass(samples)
    assert "class InferredModel:" in code


def test_to_dataclass_includes_imports():
    samples = [{"x": 1}]
    code = to_dataclass(samples)
    assert "from __future__ import annotations" in code
    assert "from dataclasses import dataclass" in code


def test_to_dataclass_empty_properties():
    samples: list[dict[str, object]] = []
    code = to_dataclass(samples, name="Empty")
    assert "class Empty:" in code
    assert "pass" in code


def test_to_dataclass_array_field():
    samples = [{"tags": ["a", "b"]}]
    code = to_dataclass(samples, name="Item")
    assert "tags: list[str]" in code


def test_to_dataclass_float_field():
    samples = [{"score": 9.5}]
    code = to_dataclass(samples, name="Result")
    assert "score: float" in code


def test_to_dataclass_required_before_optional():
    samples = [
        {"name": "Alice", "age": 30, "email": "a@b.com"},
        {"name": "Bob", "age": 25},
    ]
    code = to_dataclass(samples, name="Person")
    lines = code.split("\n")
    field_lines = [l.strip() for l in lines if l.strip().startswith(("age:", "email:", "name:"))]
    # Required fields (age, name) should appear before optional (email)
    required_indices = [i for i, l in enumerate(field_lines) if "= None" not in l]
    optional_indices = [i for i, l in enumerate(field_lines) if "= None" in l]
    if required_indices and optional_indices:
        assert max(required_indices) < min(optional_indices)


def test_to_dataclass_strictness_strict():
    samples = [
        {"name": "Alice", "age": 30},
        {"name": "Bob"},
    ]
    code = to_dataclass(samples, name="Strict", strictness="strict")
    # In strict mode, all fields are required (no = None defaults)
    assert "= None" not in code


# --- Format detection in infer() ---


def test_infer_detects_email_format_in_schema():
    samples = [
        {"email": "alice@example.com"},
        {"email": "bob@example.com"},
    ]
    schema = infer(samples)
    assert schema["properties"]["email"].get("format") == "email"


def test_infer_detects_uri_format_in_schema():
    samples = [
        {"url": "https://example.com"},
    ]
    schema = infer(samples)
    assert schema["properties"]["url"].get("format") == "uri"


def test_infer_detects_uuid_format_in_schema():
    samples = [
        {"id": "550e8400-e29b-41d4-a716-446655440000"},
    ]
    schema = infer(samples)
    assert schema["properties"]["id"].get("format") == "uuid"


def test_infer_detects_datetime_format_in_schema():
    samples = [
        {"created": "2026-03-10T14:30:00Z"},
    ]
    schema = infer(samples)
    assert schema["properties"]["created"].get("format") == "date-time"


def test_infer_detects_date_format_in_schema():
    samples = [
        {"birthday": "2000-01-15"},
    ]
    schema = infer(samples)
    assert schema["properties"]["birthday"].get("format") == "date"


def test_infer_from_jsonl_basic(tmp_path):
    file = tmp_path / "data.jsonl"
    file.write_text(
        '{"name": "Alice", "age": 30}\n'
        '{"name": "Bob", "age": 25}\n'
    )
    schema = infer_from_jsonl(file)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["age"]["type"] == "integer"


def test_infer_from_jsonl_empty_file(tmp_path):
    file = tmp_path / "empty.jsonl"
    file.write_text("")
    schema = infer_from_jsonl(file)
    assert schema == {"type": "object", "properties": {}}


def test_infer_from_jsonl_skips_blank_lines(tmp_path):
    file = tmp_path / "blanks.jsonl"
    file.write_text(
        '{"x": 1}\n'
        '\n'
        '   \n'
        '{"x": 2}\n'
    )
    schema = infer_from_jsonl(file)
    assert schema["properties"]["x"]["type"] == "integer"


def test_infer_from_jsonl_raises_on_invalid_line(tmp_path):
    file = tmp_path / "bad.jsonl"
    file.write_text(
        '{"x": 1}\n'
        'not json\n'
    )
    with pytest.raises(ValueError, match="line 2"):
        infer_from_jsonl(file)


def test_infer_from_jsonl_skip_invalid(tmp_path):
    file = tmp_path / "mixed.jsonl"
    file.write_text(
        '{"x": 1}\n'
        'not json\n'
        '[1,2,3]\n'
        '{"x": 2}\n'
    )
    schema = infer_from_jsonl(file, skip_invalid=True)
    assert schema["properties"]["x"]["type"] == "integer"


def test_infer_from_jsonl_rejects_non_object(tmp_path):
    file = tmp_path / "list.jsonl"
    file.write_text('[1,2,3]\n')
    with pytest.raises(ValueError, match="not a JSON object"):
        infer_from_jsonl(file)

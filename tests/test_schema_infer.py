from philiprehberger_schema_infer import (
    infer,
    infer_type,
    merge_schemas,
    register_format,
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

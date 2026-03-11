from philiprehberger_schema_infer import infer, infer_type, merge_schemas


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

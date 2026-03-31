# philiprehberger-schema-infer

[![Tests](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-schema-infer.svg)](https://pypi.org/project/philiprehberger-schema-infer/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-schema-infer)](https://github.com/philiprehberger/py-schema-infer/commits/main)

Infer JSON schemas from sample data.

## Installation

```bash
pip install philiprehberger-schema-infer
```

## Usage

### Infer schema from samples

```python
from philiprehberger_schema_infer import infer

samples = [
    {"name": "Alice", "age": 30, "active": True},
    {"name": "Bob", "age": 25, "email": "bob@test.com"},
]

schema = infer(samples)
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string", "minLength": 3, "maxLength": 5},
#     "age": {"type": "integer", "minimum": 25, "maximum": 30},
#     "active": {"type": "boolean"},
#     "email": {"type": "string", "format": "email", ...}
#   },
#   "required": ["age", "name"]
# }
```

### Full JSON Schema output

```python
from philiprehberger_schema_infer import to_json_schema

schema = to_json_schema(samples)
# {
#   "$schema": "https://json-schema.org/draft/2020-12/schema",
#   "type": "object",
#   "properties": { ... },
#   "required": [...]
# }
```

### Single value type inference

```python
from philiprehberger_schema_infer import infer_type

infer_type([1, 2, 3])
# {"type": "array", "items": {"type": "integer"}}
```

### Schema strictness levels

Control how aggressively fields are marked required and constraints are applied:

```python
from philiprehberger_schema_infer import infer

# Loose: no required fields, no numeric/string constraints
schema = infer(samples, strictness="loose")

# Normal (default): fields in all samples are required, constraints included
schema = infer(samples, strictness="normal")

# Strict: all fields required, additionalProperties set to False
schema = infer(samples, strictness="strict")
```

### Custom format detection

Register domain-specific regex patterns for format detection:

```python
from philiprehberger_schema_infer import register_format, infer_type

register_format("phone", r"^\+\d{1,3}-\d{3,14}$")
register_format("credit-card", r"^\d{4}-\d{4}-\d{4}-\d{4}$")

infer_type("+1-5551234567")
# {"type": "string", "format": "phone"}
```

### Merge schemas

Combine multiple inferred schemas with union/intersection logic for required fields:

```python
from philiprehberger_schema_infer import merge_schemas

merged = merge_schemas(schema_a, schema_b, schema_c)
```

## API

| Function | Description |
|---|---|
| `infer(samples, *, strictness="normal")` | Infer JSON Schema from a list of dicts. Supports `"loose"`, `"normal"`, and `"strict"` levels. |
| `infer_type(value)` | Infer schema type for a single value |
| `merge_schemas(*schemas)` | Merge two or more schemas into one accepting any of them |
| `register_format(name, pattern)` | Register a custom regex pattern for string format detection |
| `to_json_schema(samples, *, strictness="normal")` | Wraps `infer()` output with `$schema` URI for draft 2020-12 |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-schema-infer)

🐛 [Report issues](https://github.com/philiprehberger/py-schema-infer/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-schema-infer/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)

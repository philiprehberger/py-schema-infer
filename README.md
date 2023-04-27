# philiprehberger-schema-infer

[![Tests](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-schema-infer.svg)](https://pypi.org/project/philiprehberger-schema-infer/)
[![GitHub release](https://img.shields.io/github/v/release/philiprehberger/py-schema-infer)](https://github.com/philiprehberger/py-schema-infer/releases)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-schema-infer)](https://github.com/philiprehberger/py-schema-infer/commits/main)
[![License](https://img.shields.io/github/license/philiprehberger/py-schema-infer)](LICENSE)
[![Bug Reports](https://img.shields.io/github/issues/philiprehberger/py-schema-infer/bug)](https://github.com/philiprehberger/py-schema-infer/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
[![Feature Requests](https://img.shields.io/github/issues/philiprehberger/py-schema-infer/enhancement)](https://github.com/philiprehberger/py-schema-infer/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

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

### Merge schemas

```python
from philiprehberger_schema_infer import merge_schemas

merged = merge_schemas(schema_a, schema_b)
```

## API

| Name | Description |
|---|---|
| `infer(samples)` | Infer JSON Schema from a list of dicts. Includes `minimum`/`maximum` for numbers and `minLength`/`maxLength` for strings. |
| `infer_type(value)` | Infer schema type for a single value |
| `merge_schemas(a, b)` | Merge two schemas into one accepting either |
| `to_json_schema(samples)` | Wraps `infer()` output with `$schema` URI for draft 2020-12 |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this package useful, consider starring the repository.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Philip%20Rehberger-blue?logo=linkedin)](https://www.linkedin.com/in/philiprehberger/)
[![More packages](https://img.shields.io/badge/More%20packages-philiprehberger-orange)](https://github.com/philiprehberger?tab=repositories)

## License

[MIT](LICENSE)

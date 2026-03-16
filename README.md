# philiprehberger-schema-infer

[![Tests](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-schema-infer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-schema-infer.svg)](https://pypi.org/project/philiprehberger-schema-infer/)
[![License](https://img.shields.io/github/license/philiprehberger/py-schema-infer)](LICENSE)

Infer JSON schemas from sample data.

## Installation

```bash
pip install philiprehberger-schema-infer
```

## Usage

```python
from philiprehberger_schema_infer import infer, infer_type, merge_schemas

samples = [
    {"name": "Alice", "age": 30, "active": True},
    {"name": "Bob", "age": 25, "email": "bob@test.com"},
]

schema = infer(samples)
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string"},
#     "age": {"type": "integer"},
#     "active": {"type": "boolean"},
#     "email": {"type": "string", "format": "email"}
#   },
#   "required": ["age", "name"]
# }

# Single value
infer_type([1, 2, 3])
# {"type": "array", "items": {"type": "integer"}}

# Merge schemas
merged = merge_schemas(schema_a, schema_b)
```

## API

- `infer(samples)` — Infer JSON Schema from list of dicts
- `infer_type(value)` — Infer type for a single value
- `merge_schemas(a, b)` — Merge two schemas

## License

MIT

# Changelog

## 0.5.0 (2026-04-27)

- Add `infer_from_jsonl(path)` to infer schemas directly from a `.jsonl` file (one JSON object per line)
- `infer_from_jsonl` accepts `skip_invalid=True` to silently skip malformed lines

## 0.4.0 (2026-04-01)

- Add `infer_with_confidence(samples)` for per-field confidence scores indicating type consistency across samples
- Add `to_typescript(samples, *, name, strictness)` to generate TypeScript interface definitions from sample data
- Add `to_dataclass(samples, *, name, strictness)` to generate Python dataclass definitions from sample data
- Add format detection for `date-time`, `email`, `uri`, `uuid`, and `date` patterns via `infer()` and `infer_type()`

## 0.3.1 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility

## 0.3.0 (2026-03-28)

- Add `register_format(name, pattern)` for custom format detector registration (e.g., phone, credit card)
- Add `strictness` parameter to `infer()` and `to_json_schema()` with `"loose"`, `"normal"`, and `"strict"` levels
- Change `merge_schemas()` to accept variadic arguments for combining multiple schemas at once

## 0.2.0 (2026-03-27)

- Add `minimum` and `maximum` constraints for integer and number fields
- Add `minLength` and `maxLength` constraints for string fields
- Add `to_json_schema(samples)` wrapper that includes `$schema` URI for draft 2020-12
- Add pytest and mypy configuration to pyproject.toml

## 0.1.4

- Add Development section to README

## 0.1.1

- Add project URLs to pyproject.toml

## 0.1.0 (2026-03-10)

- Initial release

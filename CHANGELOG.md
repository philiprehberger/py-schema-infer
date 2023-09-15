# Changelog

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

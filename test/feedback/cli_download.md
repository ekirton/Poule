# cli_download test feedback

**Severity:** medium

**Spec reference:** specification/prebuilt-distribution.md §4.9

## Issue

`test_downloads_only_configured_libraries` and `test_include_model_null_onnx_prints_warning_and_skips` assume config.toml-driven library selection via `load_config()`. The `config.py` module has been deleted — the library set is now hardcoded to all 6 libraries.

### Failing tests

1. **`test_downloads_only_configured_libraries`** — Writes config.toml with `["stdlib"]` and expects only stdlib to be downloaded. Now all 6 are always downloaded.
2. **`test_include_model_null_onnx_prints_warning_and_skips`** — Fails because download now attempts all 6 libraries but the mock manifest only has stdlib and mathcomp entries.

## Recommendation

Remove config.toml usage from test helpers. Update mock manifests to include all 6 libraries. Remove the test asserting selective download since library selection is no longer configurable.

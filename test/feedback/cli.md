# cli test feedback

**Severity:** medium

**Spec reference:** specification/prebuilt-distribution.md §3

## Issue

`TestDbOptionRequired` (7 tests) asserts that `--db` is a required option that exits with code 2 when missing. The `--db` option now defaults to `/data/index.db` so that CLI commands work without specifying it explicitly inside the container.

These tests should be updated to either:
- Test that the default path `/data/index.db` is used when `--db` is omitted
- Test that a missing index at the default path produces a clear error message

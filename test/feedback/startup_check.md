# startup_check test feedback

**Severity:** high

**Spec reference:** specification/prebuilt-distribution.md §3 (Supported libraries), §4.9

**Commit reference:** 32810f6 — "Remove per-library selection; always include all 6 indexes"

## Issue

All tests in `test_startup_check.py` (except `TestReadIndexedLibraries` and `TestEntrypointWiring`) assume the old architecture where startup_check reads config.toml, compares against per-library indexes, downloads missing per-library DBs, and merges them locally.

The architecture has changed:
- `config.py` is deleted — library selection is not configurable
- Users do not have per-library index files — only a single pre-merged `index.db`
- `index.db` is downloaded as a single asset from GitHub Releases on first container start
- `startup_check` now checks if `index.db` exists, downloads it if missing, and reports status

### Tests that need rewriting

1. **`TestStartupCheckMatches`** — Patches `merge_indexes`; merge is no longer called from startup_check
2. **`TestStartupCheckMismatch`** — Tests config-driven rebuild with per-library DBs; this flow no longer exists
3. **`TestStartupCheckDownload`** — Tests per-library download via `_download_missing`; replaced by single `index.db` download
4. **`TestStartupCheckDefaultConfig`** — Tests config.toml default; config.toml is deleted

### Tests that still pass

1. **`TestReadIndexedLibraries`** — Tests metadata reading from index.db; unchanged
2. **`TestEntrypointWiring`** — Tests entrypoint.sh references startup_check; unchanged

## Recommendation

Rewrite tests to cover the new behavior:
- `index.db` exists → report libraries and versions
- `index.db` missing → download from GitHub Releases, then report
- `index.db` missing + download fails → print error message
- Library/version metadata read correctly from `index_meta`

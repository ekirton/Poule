# Library Indexing

Offline extraction and indexing of Coq/Rocq library declarations into a portable SQLite database.

**Stories**: [Epic 1: Library Indexing](../requirements/stories/tree-search-mcp.md#epic-1-library-indexing)

---

## What Gets Indexed

For each declaration in a Coq library:

- Fully qualified name and module path
- Kind (lemma, theorem, definition, instance, ...)
- Pretty-printed statement and type (for display and full-text search)
- Structural representation (for structural and type-based search)
- Symbol set (constants, inductives, constructors referenced, for symbol-based search)
- Dependency edges (what this declaration uses, what uses it)

## Phased Scope

### Phase 1 (MVP)
- Coq standard library only
- Single SQLite database, offline extraction
- Single command to index

### Phase 2
- MathComp
- User's current project (incremental re-indexing on file save)

### Phase 3
- Any opam-installed Coq library
- Configurable scope per project

## Extraction Method

Declarations are extracted from compiled Coq libraries using available tooling (coq-lsp or SerAPI).

## Design Rationale

### Why offline indexing

Real-time extraction during search is too slow — parsing and type-checking a Coq file takes seconds. The index is built once (or incrementally updated) and queried many times. This also allows the MCP server to start instantly by loading a pre-built database.

### Why SQLite

Single file, no external services, portable across machines. SQLite provides built-in full-text search. The entire standard library index fits comfortably in a single database file.

### Why zero-config

The target user is a Coq developer who wants search, not a systems administrator. Indexing must work with a single command, no GPU, no network access, no API keys (beyond Claude Code itself).

# Coq Library Extraction

Offline extraction of declarations from compiled Coq/Rocq libraries into the search index.

**Feature**: [Library Indexing](../features/library-indexing.md)
**Stories**: [Epic 1: Library Indexing](../requirements/stories/tree-search-mcp.md#epic-1-library-indexing)

---

## Extraction Pipeline

```
.vo files (compiled Coq libraries)
  │
  ▼
coq-lsp or SerAPI
  │  Read each declaration's Constr.t kernel term
  │
  ▼
Per-declaration processing:
  1. constr_to_tree()         → raw expression tree
  2. coq_normalize()          → normalized tree (see coq-normalization.md)
  3. cse_normalize()          → CSE-reduced tree
  4. extract_symbols()        → symbol set {constants, inductives, constructors}
  5. extract_dependencies()   → dependency edges (uses, instance_of, ...)
  6. wl_histogram(h=1,3,5)    → WL kernel vectors for structural screening
  7. pretty_print()           → human-readable statement and type for FTS
  │
  ▼
SQLite database (see storage.md)
  Write: declarations, dependencies, symbols, wl_vectors, symbol_freq,
         declarations_fts, index_meta
```

## Extraction Targets

### Phase 1 (MVP)

- **Coq standard library**: All declarations from the installed Coq/Rocq stdlib `.vo` files.
- **MathComp**: All declarations from the installed MathComp `.vo` files, indexed into the same database distinguished by module path.

### Phase 2

- **User project**: Declarations from a user-specified project directory. Supports incremental re-indexing — only changed files are re-extracted.

## Extraction Tooling

Declarations are read from compiled `.vo` files via coq-lsp or SerAPI. Both tools provide access to `Constr.t` kernel terms, which are the input to the normalization pipeline. The choice between them is an implementation decision — both produce equivalent kernel terms.

Key requirement: the extraction tool must be version-compatible with the installed Coq/Rocq version. The extracted library version is recorded in `index_meta` for stale detection.

## Error Handling

Extraction of individual declarations may fail (e.g., unsupported term constructors, serialization errors). Failures are logged with the declaration name and error, but do not abort the indexing run. The index is usable with partial coverage; missing declarations are a degraded-quality outcome, not a fatal error.

## Index Construction

The indexing command:
1. Detects the installed Coq/Rocq version and target library versions
2. Extracts all declarations through the pipeline above
3. Computes global symbol frequencies across all declarations
4. Writes everything to a single SQLite database
5. Records the index schema version and library versions in `index_meta`

The entire process runs without GPU, network access, or external API keys.

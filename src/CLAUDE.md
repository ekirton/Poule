# Implementation Guidelines

## Source of Authority

`specification/*.md` is authoritative for all implementation decisions.

Authority chain: `specification/*.md` → `doc/architecture/` → `doc/features/` → `doc/requirements/`

## Upstream Authority Is Immutable

Do not modify `test/`, `specification/`, `doc/architecture/`, or `doc/architecture/data-models/` when writing implementation code.

- If a test fails, fix the implementation — not the test.
- If a test imports from a specific module path, create that module at that path.
- If a test expects a specific function signature, implement that exact signature.
- If a test expects a specific exception type, raise that exact exception.
- File feedback in the appropriate `feedback/` folder if upstream appears wrong.

## Import Paths

Tests define the expected package structure:

| Package | Location |
|---------|----------|
| `wily_rooster.models.enums` | Enumerations (`SortKind`, `DeclKind`) |
| `wily_rooster.models.labels` | Node label hierarchy (15 concrete types) |
| `wily_rooster.models.tree` | `TreeNode`, `ExprTree`, utility functions |
| `wily_rooster.models.responses` | `SearchResult`, `LemmaDetail`, `Module` |
| `wily_rooster.normalization.constr_node` | `ConstrNode` variant types |
| `wily_rooster.normalization.normalize` | `constr_to_tree`, `coq_normalize` |
| `wily_rooster.normalization.cse` | `cse_normalize` |
| `wily_rooster.normalization.errors` | `NormalizationError` |
| `wily_rooster.storage.writer` | `IndexWriter` |
| `wily_rooster.storage.reader` | `IndexReader` |
| `wily_rooster.storage.errors` | `StorageError`, `IndexNotFoundError`, `IndexVersionError` |
| `wily_rooster.channels.wl_kernel` | WL histogram, cosine, size filter, screening |
| `wily_rooster.channels.mepo` | Symbol weight, relevance, iterative selection |
| `wily_rooster.channels.fts` | FTS5 query preprocessing and search |
| `wily_rooster.channels.ted` | Zhang-Shasha TED, rename cost, similarity |
| `wily_rooster.channels.const_jaccard` | Jaccard similarity, constant extraction |
| `wily_rooster.fusion.fusion` | Score clamping, collapse match, structural score, RRF |
| `wily_rooster.pipeline.context` | `PipelineContext`, `create_context` |
| `wily_rooster.pipeline.search` | `search_by_structure`, `search_by_type`, `search_by_symbols`, `search_by_name`, `score_candidates` |
| `wily_rooster.pipeline.parser` | `CoqParser`, `ParseError` |
| `wily_rooster.extraction.pipeline` | `run_extraction`, `discover_libraries` |
| `wily_rooster.extraction.kind_mapping` | `map_kind` |
| `wily_rooster.extraction.errors` | `ExtractionError` |
| `wily_rooster.server.handlers` | Tool handler functions |
| `wily_rooster.server.validation` | Input validation functions |
| `wily_rooster.server.errors` | Error formatting, error code constants |

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
| `Poule.models.enums` | Enumerations (`SortKind`, `DeclKind`) |
| `Poule.models.labels` | Node label hierarchy (15 concrete types) |
| `Poule.models.tree` | `TreeNode`, `ExprTree`, utility functions |
| `Poule.models.responses` | `SearchResult`, `LemmaDetail`, `Module` |
| `Poule.normalization.constr_node` | `ConstrNode` variant types |
| `Poule.normalization.normalize` | `constr_to_tree`, `coq_normalize` |
| `Poule.normalization.cse` | `cse_normalize` |
| `Poule.normalization.errors` | `NormalizationError` |
| `Poule.storage.writer` | `IndexWriter` |
| `Poule.storage.reader` | `IndexReader` |
| `Poule.storage.errors` | `StorageError`, `IndexNotFoundError`, `IndexVersionError` |
| `Poule.channels.wl_kernel` | WL histogram, cosine, size filter, screening |
| `Poule.channels.mepo` | Symbol weight, relevance, iterative selection |
| `Poule.channels.fts` | FTS5 query preprocessing and search |
| `Poule.channels.ted` | Zhang-Shasha TED, rename cost, similarity |
| `Poule.channels.const_jaccard` | Jaccard similarity, constant extraction |
| `Poule.fusion.fusion` | Score clamping, collapse match, structural score, RRF |
| `Poule.pipeline.context` | `PipelineContext`, `create_context` |
| `Poule.pipeline.search` | `search_by_structure`, `search_by_type`, `search_by_symbols`, `search_by_name`, `score_candidates` |
| `Poule.pipeline.parser` | `CoqParser`, `ParseError` |
| `Poule.extraction.pipeline` | `run_extraction`, `discover_libraries` |
| `Poule.extraction.kind_mapping` | `map_kind` |
| `Poule.extraction.errors` | `ExtractionError` |
| `Poule.server.handlers` | Tool handler functions |
| `Poule.server.validation` | Input validation functions |
| `Poule.server.errors` | Error formatting, error code constants |

# CLI

The command-line interface for both indexing and search operations.

**Feature**: [CLI Search](../features/cli-search.md)
**Stories**: [Epic 1: Library Indexing](../requirements/stories/tree-search-mcp.md#epic-1-library-indexing), [Epic 7: Standalone CLI Search](../requirements/stories/tree-search-mcp.md#epic-7-standalone-cli-search)

---

## Entry Point

A single CLI entry point exposes two command groups:

- **`index`** — library extraction and index construction (existing)
- **Search subcommands** — `search-by-name`, `search-by-type`, `search-by-structure`, `search-by-symbols`, `get-lemma`, `find-related`, `list-modules`

All search subcommands share common options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--db` | path | required | Path to the SQLite index database |
| `--json` | flag | false | Output results as JSON instead of human-readable format |
| `--limit` | integer | 50 | Maximum number of results (clamped to [1, 200]) |

## Search Subcommand Signatures

### search-by-name

```
wily-rooster search-by-name --db <path> <pattern> [--limit N] [--json]
```

Positional argument: `pattern` — the name search query.

### search-by-type

```
wily-rooster search-by-type --db <path> <type_expr> [--limit N] [--json]
```

Positional argument: `type_expr` — a Coq type expression.

### search-by-structure

```
wily-rooster search-by-structure --db <path> <expression> [--limit N] [--json]
```

Positional argument: `expression` — a Coq expression.

### search-by-symbols

```
wily-rooster search-by-symbols --db <path> <symbol> [<symbol> ...] [--limit N] [--json]
```

Positional arguments: one or more symbol names.

### get-lemma

```
wily-rooster get-lemma --db <path> <name> [--json]
```

Positional argument: `name` — fully qualified declaration name. `--limit` does not apply.

### find-related

```
wily-rooster find-related --db <path> <name> --relation <rel> [--limit N] [--json]
```

Positional argument: `name` — fully qualified declaration name.
Required option: `--relation` — one of `uses`, `used_by`, `same_module`, `same_typeclass`.

### list-modules

```
wily-rooster list-modules --db <path> [<prefix>] [--json]
```

Optional positional argument: `prefix` — module prefix to filter by (default: empty, lists all top-level modules).

## Pipeline Integration

```
CLI subcommand
  │
  │ create_context(db_path)
  ▼
PipelineContext
  │
  │ pipeline.search_by_*(ctx, ..., limit)
  ▼
Ranked results
  │
  │ format_*(results, json_mode)
  ▼
stdout
```

Each CLI subcommand:
1. Opens the index database and creates a `PipelineContext` (same as MCP server startup)
2. Calls the corresponding `pipeline.search_by_*` function with validated parameters
3. Formats results and writes to stdout

The CLI reuses `PipelineContext` and all pipeline functions identically to the MCP server. No search logic lives in the CLI layer.

## Index State Checks

On startup, the CLI performs the same index checks as the MCP server:
1. Database file existence → error message to stderr, exit code 1
2. Schema version match → error message to stderr, exit code 1

## Output Formats

### Human-Readable (default)

For `SearchResult` lists:
```
<name>  <kind>  <score>
  <statement>
  module: <module>
```

One block per result, separated by blank lines.

For `LemmaDetail`:
```
<name>  (<kind>)
  <statement>
  module:       <module>
  dependencies: <count>
  dependents:   <count>
  symbols:      <comma-separated list>
  node_count:   <n>
```

For `Module` lists:
```
<module_name>  (<declaration_count> declarations)
```

### JSON (`--json`)

For search commands: a JSON array of `SearchResult` or `Module` objects, one per line (compact format).

For `get-lemma`: a single JSON `LemmaDetail` object.

JSON field names and value types match the MCP response types defined in [data-models/response-types.md](data-models/response-types.md).

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Database file missing | Print error to stderr, exit 1 |
| Schema version mismatch | Print error to stderr, exit 1 |
| Declaration not found (`get-lemma`, `find-related`) | Print error to stderr, exit 1 |
| Parse failure (type/structure queries) | Print parse error to stderr, exit 1 |
| Empty results | Print nothing (human-readable) or `[]` (JSON), exit 0 |

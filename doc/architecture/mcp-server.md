# MCP Server

The thin adapter layer between Claude Code and the search backend.

**Feature**: [MCP Tool Surface](../features/mcp-tool-surface.md)
**Stories**: [Epic 2: MCP Server and Tool Surface](../requirements/stories/tree-search-mcp.md#epic-2-mcp-server-and-tool-surface)

---

## Transport

The server communicates via stdio transport, compatible with Claude Code's MCP configuration.

## Tool Signatures

```typescript
// Structural search: find declarations with similar expression structure
search_by_structure(
  expr: string,        // Coq expression or type (parsed by backend)
  limit: number = 50   // candidates to return (bias toward high recall)
) → SearchResult[]

// Symbol search: find declarations sharing symbols with the query
search_by_symbols(
  symbols: string[],   // constant/inductive names
  limit: number = 50
) → SearchResult[]

// Name search: find declarations by name pattern
search_by_name(
  pattern: string,     // glob or regex on qualified names
  limit: number = 50
) → SearchResult[]

// Type search: find declarations whose type matches a pattern
search_by_type(
  type_pattern: string, // Coq type expression
  limit: number = 50
) → SearchResult[]

// Get full details for a specific declaration
get_lemma(
  name: string         // fully qualified name
) → LemmaDetail

// Navigate the dependency graph
find_related(
  name: string,
  relation: "uses" | "used_by" | "same_module" | "same_typeclass",
  limit: number = 20
) → SearchResult[]

// Browse module structure
list_modules(
  prefix: string = ""  // e.g., "Coq.Arith" or "mathcomp.algebra"
) → Module[]
```

## Response Types

```typescript
SearchResult = {
  name: string,          // fully qualified name
  statement: string,     // pretty-printed statement
  type: string,          // pretty-printed type
  module: string,        // containing module
  kind: string,          // "lemma" | "theorem" | "definition" | "instance" | ...
  score: number          // relevance score (0-1)
}

LemmaDetail = SearchResult & {
  dependencies: string[],  // names this declaration uses
  dependents: string[],    // names that use this declaration
  proof_sketch: string,    // tactic script or proof term (if available)
  symbols: string[],       // constant symbols appearing in the statement
  node_count: number       // expression tree size (for diagnostics)
}
```

## Server Responsibilities

The MCP server is a thin adapter. It:
- Validates inputs (pattern syntax, expression parsing)
- Translates MCP tool calls to search backend queries
- Formats search backend results into MCP response objects
- Handles errors (unknown declarations, parse failures) with structured error responses

It does **not** implement search logic, manage storage, or interact with Coq directly.

## Error Contract

All error responses use MCP's standard error format with a structured `error` object containing a `code` and human-readable `message`.

| Condition | Error Code | Message |
|-----------|-----------|---------|
| No index database at configured path | `INDEX_MISSING` | Index database not found at `{path}`. Run the indexing command to create it. |
| Index schema version does not match tool version | `INDEX_VERSION_MISMATCH` | Index schema version `{found}` is incompatible with tool version `{expected}`. Re-indexing from scratch. |
| Library version changed (stale index detected) | `INDEX_REBUILDING` | Detected library update. Rebuilding index before serving queries. |
| `get_lemma` with unknown name | `NOT_FOUND` | Declaration `{name}` not found in the index. |
| Malformed query expression | `PARSE_ERROR` | Failed to parse expression: `{details}` |

On startup, the server checks the index in this order:
1. Does the database file exist? If not → `INDEX_MISSING`.
2. Does the `schema_version` in `index_meta` match the tool's expected version? If not → full re-index.
3. Do the library versions in `index_meta` match the currently installed versions? If not → full rebuild before serving queries.

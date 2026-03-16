# System Overview

**Feature**: [Semantic Search for Coq/Rocq Libraries](../features/semantic-search.md)

The system has four components connected in a pipeline from offline extraction through online search.

---

## Component Diagram

```
┌─────────────────────────────────────────────────┐
│                   Claude Code                    │
│                                                  │
│  Receives user queries, formulates MCP tool      │
│  calls, filters and explains results             │
└──────────────────┬──────────────────────────────┘
                   │ MCP tool calls
                   ▼
┌─────────────────────────────────────────────────┐
│              MCP Server (thin adapter)           │
│                                                  │
│  Tools:                                          │
│    search_by_name(pattern)                       │
│    search_by_type(type_pattern)                  │
│    search_by_structure(expr, limit)              │
│    search_by_symbols(symbols[], limit)           │
│    get_lemma(name) → details + dependencies      │
│    find_related(name, relation)                  │
│    list_modules(prefix)                          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP / stdio
                   ▼
┌─────────────────────────────────────────────────┐
│              Search Backend                      │
│                                                  │
│  Index:                                          │
│    SQLite DB with:                               │
│      - declarations table                        │
│      - dependencies table                        │
│      - symbols table                             │
│      - wl_vectors table                          │
│      - FTS5 index on names + statements          │
│                                                  │
│  Retrieval channels:                             │
│    1. WL kernel screening (structural)           │
│    2. MePo/SInE symbol overlap (syntactic)       │
│    3. FTS5 full-text search (lexical)            │
│    4. TED fine ranking (structural, small exprs) │
│    5. Const name Jaccard (lightweight)           │
│                                                  │
│  Fusion: reciprocal rank fusion across channels  │
└──────────────────┬──────────────────────────────┘
                   │ offline indexing
                   ▼
┌─────────────────────────────────────────────────┐
│           Coq Library Extraction                 │
│                                                  │
│  Via coq-lsp or SerAPI:                          │
│    - Extract all declarations with Constr.t      │
│    - Serialize to tree representation            │
│    - Compute CSE-normalized forms                │
│    - Extract dependency edges                    │
│    - Extract symbol sets                         │
│    - Compute WL encodings at h=1,3,5            │
│    - Pretty-print for FTS indexing               │
│                                                  │
│  Targets: stdlib, MathComp, user project         │
└─────────────────────────────────────────────────┘
```

## Data Flow

**Offline (indexing)**:
1. Coq Library Extraction reads compiled `.vo` files via coq-lsp or SerAPI
2. Each declaration is converted to an expression tree, normalized, and indexed
3. The Search Backend stores all index data in a single SQLite database

**Server startup (index lifecycle)**:
1. The MCP Server checks for the index database at the configured path
2. If the database is missing, the server returns an `INDEX_MISSING` error on all tool calls
3. If the database exists, the server reads the `index_meta` table and checks:
   a. Schema version matches the tool's expected version — if not, triggers a full re-index
   b. Library versions match the currently installed versions — if not, triggers a full rebuild
4. Once a valid index is confirmed, the server loads WL histograms into memory and begins serving queries

**Online (query)**:
1. The LLM in Claude Code receives a user query and formulates MCP tool calls
2. The MCP Server translates tool calls to Search Backend queries
3. The Search Backend runs the appropriate retrieval channels and fuses results
4. Results flow back through the MCP Server to the LLM
5. The LLM filters, ranks, and explains results to the user

## Component Responsibilities

| Component | Responsibility | Does NOT do |
|-----------|---------------|-------------|
| Claude Code / LLM | Intent interpretation, query formulation, result filtering, explanation | Retrieval, indexing |
| MCP Server | Protocol translation, input validation, response formatting | Search logic, storage |
| Search Backend | Retrieval channels, fusion, index queries | Coq parsing, user interaction |
| Coq Library Extraction | Declaration extraction, tree conversion, normalization, index construction | Online queries |

## Index Lifecycle

The index is a derived artifact. Its lifecycle is managed by the MCP Server on startup:

```
Server start
  │
  ├─ Database missing? → INDEX_MISSING error on all tool calls
  │
  ├─ Schema version mismatch? → Full re-index from scratch
  │
  ├─ Library version changed? → Full rebuild before serving queries
  │
  └─ All checks pass → Load histograms into memory, serve queries
```

Re-indexing is always a full rebuild. See [storage.md](storage.md) for the `index_meta` table schema and [mcp-server.md](mcp-server.md) for the error contract.

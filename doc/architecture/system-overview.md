# System Overview

**Feature**: [Semantic Search for Coq/Rocq Libraries](../features/semantic-search.md), [Proof Session Management](../features/proof-session-management.md)

The system has two major subsystems — semantic search (Phase 1) and proof interaction (Phase 2) — sharing a single MCP server entry point.

---

## Component Diagram

```
┌─────────────────────────┐   ┌─────────────────┐
│       Claude Code       │   │  Terminal user   │
│                         │   │                  │
│  Formulates MCP tool    │   │  CLI subcommands │
│  calls, filters and     │   │                  │
│  explains results       │   │                  │
└───────────┬─────────────┘   └────────┬─────────┘
            │ MCP tool calls (stdio)    │ CLI
            ▼                           ▼
┌────────────────────────────────┐  ┌────────────┐
│    MCP Server (thin adapter)   │  │    CLI     │
│                                │  │            │
│  Search tools (Phase 1):      │  │  index     │
│    search_by_name, ...         │  │  search-*  │
│                                │  │  get-lemma │
│  Proof tools (Phase 2):       │  │  ...       │
│    open_proof_session, ...     │  │            │
└──────┬──────────────┬─────────┘  └─────┬──────┘
       │ search       │ session          │ search
       │ queries      │ operations       │ queries
       ▼              ▼                  ▼
┌────────────┐  ┌──────────────────────────────┐
│  Retrieval │  │   Proof Session Manager       │
│  Pipeline  │  │                                │
│            │  │  Session Registry              │
│  Channels: │  │    session_id → SessionState   │
│  WL, MePo, │  │                                │
│  FTS5, TED,│  │  Per-session:                  │
│  Const     │  │    CoqBackend (one process)    │
│  Jaccard   │  │    State history               │
│            │  │    Premise extraction           │
│  Fusion:   │  │                                │
│  RRF       │  └──────────────┬─────────────────┘
└──────┬─────┘                 │ coq-lsp / SerAPI
       │ SQLite queries        │ (bidirectional, stateful)
       ▼                       ▼
┌──────────────┐  ┌──────────────────────────────┐
│   Storage    │  │  Coq Backend Processes        │
│   (SQLite)   │  │  (one per session)            │
│              │  │                                │
│ declarations │  │  Load .v files                 │
│ dependencies │  │  Execute tactics               │
│ wl_vectors   │  │  Report proof state + premises │
│ symbol_freq  │  └──────────────────────────────┘
│ index_meta   │
└──────┬───────┘
       ▲
       │ writes during indexing
┌──────┴───────┐
│  Coq Library │
│  Extraction  │
│              │
│  Via coq-lsp │
│  or SerAPI   │
└──────────────┘
```

## Data Flow

**Offline (indexing)**:
1. Coq Library Extraction reads compiled `.vo` files via coq-lsp or SerAPI
2. Each declaration is converted to an expression tree, normalized, and indexed
3. The Search Backend stores all index data in a single SQLite database

**Server startup (index lifecycle)**:
1. The MCP Server checks for the index database at the configured path
2. If the database is missing, the server returns an `INDEX_MISSING` error on all search tool calls
3. If the database exists, the server reads the `index_meta` table and checks:
   a. Schema version matches the tool's expected version — if not, triggers a full re-index
   b. Library versions match the currently installed versions — if not, triggers a full rebuild
4. Once a valid index is confirmed, the server loads WL histograms into memory and begins serving queries

**Online (search query)**:
1. The LLM in Claude Code receives a user query and formulates MCP tool calls
2. The MCP Server translates search tool calls to Search Backend queries
3. The Search Backend runs the appropriate retrieval channels and fuses results
4. Results flow back through the MCP Server to the LLM
5. The LLM filters, ranks, and explains results to the user

**Online (proof interaction)**:
1. The LLM (or a tool builder) opens a proof session via `open_proof_session`
2. The Proof Session Manager spawns a dedicated Coq backend process for the session
3. The backend loads the .v file and positions at the named proof
4. Subsequent tool calls (submit tactic, observe state, step forward/backward) are routed to the session's backend
5. Proof states are serialized to JSON with a version-stable schema (see [proof-serialization.md](proof-serialization.md))
6. Premise queries trigger analysis of the backend's internal state at each tactic step
7. Trace extraction materializes all states and tactics into a single ProofTrace response
8. When the session is closed (explicitly or by timeout), the backend process is terminated

## Component Responsibilities

| Component | Responsibility | Does NOT do |
|-----------|---------------|-------------|
| Claude Code / LLM | Intent interpretation, query formulation, result filtering, explanation | Retrieval, indexing, proof state management |
| MCP Server | Protocol translation, input validation, response formatting, proof state serialization | Search logic, storage, session state management |
| CLI | Command-line interface for indexing and search, output formatting | Search logic, proof interaction |
| Retrieval Pipeline | Retrieval channels, metric computation, fusion, index queries | Coq parsing, user interaction, proof interaction |
| Storage | SQLite schema, index metadata, FTS5 index | Online queries, proof interaction |
| Proof Session Manager | Session lifecycle, Coq backend process management, tactic dispatch, state caching, premise extraction | Search logic, serialization format, protocol translation |
| Coq Library Extraction | Declaration extraction, tree conversion, normalization, index construction | Online queries, proof interaction |

## Index Lifecycle

The index is a derived artifact. Its lifecycle is managed by the MCP Server on startup:

```
Server start
  │
  ├─ Database missing? → INDEX_MISSING error on all search tool calls
  │
  ├─ Schema version mismatch? → Full re-index from scratch
  │
  ├─ Library version changed? → Full rebuild before serving queries
  │
  └─ All checks pass → Load histograms into memory, serve queries
```

Re-indexing is always a full rebuild. See [storage.md](storage.md) for the `index_meta` table schema and [mcp-server.md](mcp-server.md) for the error contract.

Note: Proof interaction tools do not depend on the search index. A proof session can be opened and used even when the index is missing or being rebuilt. The two subsystems are independent at runtime.

# Component Boundaries

System-level view of all components, their boundaries, and the dependency graph.

---

## Component Taxonomy

| Component | Owns | Architecture Doc |
|-----------|------|-----------------|
| Coq Library Extraction | Declaration extraction, tree conversion, normalization, index construction | [coq-extraction.md](coq-extraction.md), [coq-normalization.md](coq-normalization.md) |
| Storage | SQLite schema, index metadata, FTS5 index | [storage.md](storage.md) |
| Retrieval Pipeline | Retrieval channels, metric computation, fusion | [retrieval-pipeline.md](retrieval-pipeline.md) |
| MCP Server | Protocol translation, input validation, error handling, response formatting, proof state serialization, visualization dispatch | [mcp-server.md](mcp-server.md) |
| CLI | Command-line interface for indexing, search, proof replay, and batch extraction, output formatting | [cli.md](cli.md) |
| Proof Session Manager | Session lifecycle, Coq backend process management, tactic dispatch, state caching, premise extraction | [proof-session.md](proof-session.md) |
| Extraction Campaign Orchestrator | Project/file enumeration, per-proof extraction loop, failure isolation, streaming output, summary statistics | [extraction-campaign.md](extraction-campaign.md) |
| Mermaid Renderer | Proof state, proof tree, dependency, and sequence diagram generation as Mermaid syntax | [mermaid-renderer.md](mermaid-renderer.md) |
| Claude Code / LLM | Intent interpretation, query formulation, result filtering, explanation | External (not owned by this project) |

### Cross-Cutting Concerns

| Concern | Owns | Architecture Doc |
|---------|------|-----------------|
| Coq Expression Normalization | Tree normalization pipeline, CSE reduction | [coq-normalization.md](coq-normalization.md) |
| Proof Serialization | JSON serialization of proof types, schema versioning, determinism, diff computation | [proof-serialization.md](proof-serialization.md) |
| Extraction Output Format | JSON Lines serialization of extraction records, provenance metadata, record type discrimination | [extraction-output.md](extraction-output.md) |
| Extraction Checkpointing | Incremental re-extraction, campaign resumption, checkpoint file management (P1) | [extraction-checkpointing.md](extraction-checkpointing.md) |
| Extraction Reporting | Quality reports, scope filtering, benchmark generation, ML export (P1/P2) | [extraction-reporting.md](extraction-reporting.md) |
| Extraction Dependency Graph | Theorem-level dependency graph extraction from premise annotations (P1) | [extraction-dependency-graph.md](extraction-dependency-graph.md) |

Proof Serialization is used by the MCP Server (for formatting responses) and the Proof Session Manager (for trace export). It is not a standalone runtime component — it is a shared serialization contract.

Extraction Output Format extends Proof Serialization concepts to the batch extraction context. It defines the JSON Lines stream structure, record type discrimination, and provenance metadata. It is used by the Extraction Campaign Orchestrator.

Coq Backend Processes (one per session) are owned by the Proof Session Manager. They appear as a separate box in the dependency graph because they are separate OS processes, but they are not an independent component — their lifecycle is fully managed by the session manager.

## Dependency Graph

```
Claude Code / LLM          Terminal user
  │                           │                    │
  │ MCP tool calls (stdio)    │ CLI subcommands    │ CLI (Phase 3)
  ▼                           ▼                    ▼
MCP Server                  CLI                  CLI
  │         │       │         │         │          │
  │ search  │ proof │ viz     │ search  │ proof    │ batch
  │ queries │ sess  │ tools   │ queries │ replay   │ extraction
  ▼         ▼       ▼         ▼         ▼          ▼
Retrieval   Proof  Mermaid  Retrieval  Proof    Extraction Campaign
Pipeline    Sess.  Renderer Pipeline   Session  Orchestrator
  │         Mgr      │        │        Manager     │
  │ SQLite    │      │        │ SQLite   │        │ session ops
  │ queries   │      │ pure   │ queries  │        │ (reuse)
  ▼           ▼      │ fn     ▼          │        │
Storage     Coq     (no     Storage     │        │
(SQLite)    Backend  deps)  (SQLite)     │        │
  ▲         Procs                        ▼        ▼
  │         (per-                   Proof Session Manager
  │          session)                 │
  │ Writes during indexing            │ coq-lsp / SerAPI
  │                                   ▼
Coq Library Extraction             Coq Backend Processes
  │                                (per-session)
  │ coq-lsp / SerAPI
  ▼
Compiled .vo files (external)      JSON Lines output
                                   (Phase 3 batch output)
```

Note: All three subsystems are independent at runtime. The Proof Session Manager and the Search Backend (Retrieval Pipeline + Storage) are independent. The Extraction Campaign Orchestrator depends on the Proof Session Manager but not on the Search Backend or MCP Server. Proof interaction does not require a search index, and search does not require proof sessions. Extraction does not require a search index or the MCP Server. The Mermaid Renderer is a pure function component with no runtime dependencies — it receives structured data from the MCP Server and returns Mermaid text.

## Boundary Contracts

### Claude Code → MCP Server

| Property | Value |
|----------|-------|
| Transport | stdio |
| Protocol | MCP (Model Context Protocol) |
| Direction | Request-response |
| Search tools | `search_by_name`, `search_by_type`, `search_by_structure`, `search_by_symbols`, `get_lemma`, `find_related`, `list_modules` |
| Proof tools (P0) | `open_proof_session`, `close_proof_session`, `list_proof_sessions`, `observe_proof_state`, `get_proof_state_at_step`, `extract_proof_trace`, `submit_tactic`, `step_backward`, `step_forward`, `get_proof_premises`, `get_step_premises` |
| Proof tools (P1) | `submit_tactic_batch` |
| Visualization tools | `visualize_proof_state`, `visualize_proof_tree`, `visualize_dependencies`, `visualize_proof_sequence` |
| Search response types | `SearchResult`, `LemmaDetail`, `Module`, structured errors |
| Proof response types | `ProofState`, `ProofTrace`, `PremiseAnnotation`, `Session`, structured errors (see [data-models/proof-types.md](data-models/proof-types.md)) |
| Visualization response types | Mermaid syntax strings, node counts, truncation flags, structured errors |
| Error contract | See [mcp-server.md](mcp-server.md) § Error Contract |

### CLI → Proof Session Manager (proof replay)

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process), async via `asyncio.run()` |
| Direction | Request-response |
| Input | File path + proof name (replay-proof command) |
| Output | ProofTrace, optionally list[PremiseAnnotation], or structured errors |
| Shared with | MCP Server → Proof Session Manager (same `SessionManager` API) |
| Lifecycle | Session created and closed within a single command invocation |

### CLI → Extraction Campaign Orchestrator

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process) |
| Direction | Request-response (blocking, long-running) |
| Input | List of project directories, extraction options (scope filter, output path, incremental flag) |
| Output | JSON Lines file written to output path; exit code 0 on success, 1 on error |
| Lifecycle | Campaign runs to completion within a single CLI invocation |

### Extraction Campaign Orchestrator → Proof Session Manager

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process), reuses same `SessionManager` API as MCP Server and CLI proof replay |
| Direction | Request-response |
| Input | File path + theorem name (per-proof extraction) |
| Output | ProofTrace + list[PremiseAnnotation], or structured errors |
| Shared with | MCP Server → Proof Session Manager, CLI → Proof Session Manager (same API surface) |
| Lifecycle | One session per proof; session created, proof replayed and extracted, session closed within per-proof loop iteration |
| Failure contract | Backend crash, tactic failure, timeout → ExtractionError record; orchestrator continues with next proof |

### CLI → Retrieval Pipeline

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process) |
| Direction | Request-response |
| Input | Parsed and validated query parameters (identical to MCP server) |
| Output | Ranked result lists with scores |
| Shared with | MCP Server → Retrieval Pipeline (same `PipelineContext` and pipeline functions) |

### MCP Server → Mermaid Renderer

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process) |
| Direction | Request-response (pure function, no state) |
| Input | ProofState, ProofTrace, or dependency adjacency list + configuration (detail level, max depth, max nodes) |
| Output | Mermaid syntax string(s) |
| Dependencies | None — the renderer is a pure function with no external dependencies |
| Visualization tools | `visualize_proof_state`, `visualize_proof_tree`, `visualize_dependencies`, `visualize_proof_sequence` |

### MCP Server → Retrieval Pipeline

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process) |
| Direction | Request-response |
| Input | Parsed and validated query parameters |
| Output | Ranked result lists with scores |

### Retrieval Pipeline → Storage

| Property | Value |
|----------|-------|
| Mechanism | SQLite queries |
| Direction | Read-only during online queries |
| Tables read | `declarations`, `dependencies`, `wl_vectors`, `symbol_freq`, `declarations_fts` |
| Assumptions | WL histograms loaded into memory at startup; SQLite queries for other data |

### Coq Library Extraction → Storage

| Property | Value |
|----------|-------|
| Mechanism | SQLite writes |
| Direction | Write-only during offline indexing |
| Tables written | All tables including `index_meta` |
| Assumptions | Exclusive write access during indexing; database is replaced atomically |

### MCP Server → Proof Session Manager

| Property | Value |
|----------|-------|
| Mechanism | Internal function calls (in-process) |
| Direction | Request-response |
| Input | Session ID + operation-specific parameters (tactic string, step index, etc.) |
| Output | ProofState, ProofTrace, PremiseAnnotation, Session metadata, or structured errors |
| Statefulness | The session manager is stateful — each session maintains independent state across calls |

### Proof Session Manager → Coq Backend Processes

| Property | Value |
|----------|-------|
| Mechanism | Process-level communication (stdin/stdout) via coq-lsp or SerAPI protocol |
| Direction | Bidirectional, stateful |
| Cardinality | One backend process per active session |
| Lifecycle | Process spawned on session open, terminated on session close or timeout |
| Crash handling | Backend crash is detected and reported as `BACKEND_CRASHED`; other sessions unaffected |

### MCP Server → Storage (index lifecycle)

| Property | Value |
|----------|-------|
| Mechanism | SQLite read of `index_meta` |
| Direction | Read-only on startup |
| Purpose | Schema version check, library version check |
| Phase 1 behavior | Validates `schema_version` only; library versions stored for informational purposes. Schema mismatch → `INDEX_VERSION_MISMATCH` error directing user to re-index manually. |
| Phase 2 behavior | Additionally validates `coq_version` and `mathcomp_version` against installed versions; mismatch → `INDEX_VERSION_MISMATCH` error. |

## Source-to-Specification Mapping

| Architecture Document | Produces Specifications |
|----------------------|----------------------|
| [data-models/](data-models/) | [specification/data-structures.md](../../specification/data-structures.md) |
| [coq-extraction.md](coq-extraction.md) | [specification/extraction.md](../../specification/extraction.md) |
| [coq-normalization.md](coq-normalization.md) | [specification/coq-normalization.md](../../specification/coq-normalization.md), [specification/cse-normalization.md](../../specification/cse-normalization.md) |
| [storage.md](storage.md) | [specification/storage.md](../../specification/storage.md) |
| [retrieval-pipeline.md](retrieval-pipeline.md) | [specification/pipeline.md](../../specification/pipeline.md), [specification/fusion.md](../../specification/fusion.md), [specification/channel-wl-kernel.md](../../specification/channel-wl-kernel.md), [specification/channel-mepo.md](../../specification/channel-mepo.md), [specification/channel-fts.md](../../specification/channel-fts.md), [specification/channel-ted.md](../../specification/channel-ted.md), [specification/channel-const-jaccard.md](../../specification/channel-const-jaccard.md) |
| [mcp-server.md](mcp-server.md) | [specification/mcp-server.md](../../specification/mcp-server.md) |
| [cli.md](cli.md) | [specification/cli.md](../../specification/cli.md) |
| [proof-session.md](proof-session.md) | [specification/proof-session.md](../../specification/proof-session.md), [specification/coq-proof-backend.md](../../specification/coq-proof-backend.md) |
| [proof-serialization.md](proof-serialization.md) | [specification/proof-serialization.md](../../specification/proof-serialization.md) |
| [data-models/proof-types.md](data-models/proof-types.md) | [specification/data-structures.md](../../specification/data-structures.md) (proof types section) |
| [extraction-campaign.md](extraction-campaign.md) | [specification/extraction-campaign.md](../../specification/extraction-campaign.md) |
| [extraction-output.md](extraction-output.md) | [specification/extraction-output.md](../../specification/extraction-output.md) |
| [extraction-checkpointing.md](extraction-checkpointing.md) | [specification/extraction-checkpointing.md](../../specification/extraction-checkpointing.md) |
| [extraction-dependency-graph.md](extraction-dependency-graph.md) | [specification/extraction-dependency-graph.md](../../specification/extraction-dependency-graph.md) |
| [extraction-reporting.md](extraction-reporting.md) | [specification/extraction-reporting.md](../../specification/extraction-reporting.md) |
| [mermaid-renderer.md](mermaid-renderer.md) | specification/mermaid-renderer.md (pending) |
| [data-models/extraction-types.md](data-models/extraction-types.md) | [specification/data-structures.md](../../specification/data-structures.md) §4.8 |

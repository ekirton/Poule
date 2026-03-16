# User Stories: Tree-Based Semantic Search MCP

Derived from [doc/architecture/system-overview.md](../../architecture/system-overview.md).

---

## Epic 1: Library Indexing

### 1.1 Index the Standard Library

**As a** Coq developer setting up the tool for the first time,
**I want to** index the Coq standard library with a single command,
**so that** I can start searching immediately without manual configuration.

**Acceptance criteria:**
- A CLI command extracts all declarations from the installed Coq standard library
- Extraction produces a single SQLite database file with no external service dependencies
- The database contains declarations, dependencies, and all data required by the retrieval channels
- The command completes without requiring a GPU, external API keys, or network access
- Errors during extraction of individual declarations are logged but do not abort the full indexing run

### 1.2 Index MathComp

**As a** Coq developer working with MathComp,
**I want to** index the MathComp library alongside the standard library,
**so that** I can search across both libraries in a single query.

**Acceptance criteria:**
- The indexing command accepts MathComp as a target library
- MathComp declarations are stored in the same database as stdlib declarations, distinguished by module path
- Fully qualified names and module membership are recorded correctly for MathComp's nested module structure

### 1.3 Index a User Project

**As a** Coq developer working on my own project,
**I want to** index my project's declarations alongside library declarations,
**so that** I can search my own lemmas with the same tools.

**Acceptance criteria:**
- The indexing command accepts a user project directory as a target
- Project declarations are indexed into the same database
- Re-indexing updates changed declarations without rebuilding the entire index

---

## Epic 2: MCP Server and Tool Surface

### 2.1 Start the MCP Server

**As a** Claude Code user,
**I want** the MCP server to start and connect to Claude Code,
**so that** the search tools are available in my conversation.

**Acceptance criteria:**
- The server starts via stdio transport compatible with Claude Code's MCP configuration
- The server exposes all 7 tools: `search_by_name`, `search_by_type`, `search_by_structure`, `search_by_symbols`, `get_lemma`, `find_related`, `list_modules`
- The server connects to the SQLite index database specified by configuration
- The server returns well-formed MCP tool responses with typed `SearchResult` and `LemmaDetail` objects

### 2.2 Search by Name

**As a** Coq developer who partially remembers a lemma name,
**I want to** search for declarations by name pattern,
**so that** I can find lemmas when I know part of their identifier.

**Acceptance criteria:**
- `search_by_name` accepts glob or regex patterns on fully qualified names
- Results include name, statement, type, module, kind, and relevance score
- Results are ranked by relevance
- Default limit is 50; callers can override

### 2.3 Search by Type

**As a** Coq developer who knows the type signature I need,
**I want to** search for declarations whose type matches a pattern,
**so that** I can find lemmas by their logical content.

**Acceptance criteria:**
- `search_by_type` accepts a Coq type expression as input
- The backend parses the expression and retrieves candidates using multiple retrieval channels
- Results are fused across channels to maximize recall
- Results include the standard `SearchResult` fields

### 2.4 Search by Structure

**As a** Coq developer (or the LLM on my behalf),
**I want to** find declarations structurally similar to a given expression,
**so that** I can discover lemmas with related logical shapes even when names and symbols differ.

**Acceptance criteria:**
- `search_by_structure` accepts a Coq expression string
- The backend computes structural similarity between the query expression and indexed declarations
- Results are returned ranked by structural similarity score

### 2.5 Search by Symbols

**As a** Coq developer (or the LLM on my behalf),
**I want to** find declarations that use specific constant/inductive/constructor symbols,
**so that** I can locate lemmas involving particular definitions.

**Acceptance criteria:**
- `search_by_symbols` accepts an array of symbol names
- The backend ranks results by symbol relevance, weighting rare symbols more heavily
- Results are returned ranked by relevance score

### 2.6 Get Lemma Details

**As a** Coq developer who found a candidate result,
**I want to** retrieve full details for a specific declaration,
**so that** I can understand its dependencies, dependents, and proof structure.

**Acceptance criteria:**
- `get_lemma` accepts a fully qualified declaration name
- Response includes all `SearchResult` fields plus: dependencies, dependents, proof sketch (if available), symbols list, and node count
- Returns a clear error if the name is not found in the index

### 2.7 Find Related Declarations

**As a** Coq developer exploring a neighborhood of the library,
**I want to** navigate the dependency graph from a known declaration,
**so that** I can discover related lemmas by structural relationships.

**Acceptance criteria:**
- `find_related` accepts a declaration name and a relation type: `uses`, `used_by`, `same_module`, or `same_typeclass`
- Results are limited by a configurable limit (default 20)
- Results include the standard `SearchResult` fields

### 2.8 List Modules

**As a** Coq developer browsing library structure,
**I want to** list modules under a given prefix,
**so that** I can orient myself within the library hierarchy.

**Acceptance criteria:**
- `list_modules` accepts a module prefix (e.g., `Coq.Arith`, `mathcomp.algebra`)
- Returns module names and their declaration counts
- An empty prefix lists top-level modules

---

## Epic 3: Retrieval Quality

### 3.1 Multi-Channel Fusion

**As a** user performing a search,
**I want** results to be drawn from multiple retrieval channels and fused,
**so that** I get high recall across different notions of similarity.

**Acceptance criteria:**
- Each search query engages applicable retrieval channels (structural, symbolic, lexical)
- Results are combined across channels so that items appearing in multiple channels rank higher
- Items appearing in multiple channels are ranked higher than items from a single channel

### 3.2 Recall Target

**As a** project maintainer,
**I want** the retrieval stage to surface the relevant lemma in the top-50 results at least 70% of the time,
**so that** the LLM filtering layer has sufficient candidates to work with.

**Acceptance criteria:**
- A hand-curated evaluation set of (query, relevant lemma) pairs from common Coq workflows exists
- The system achieves >= 70% recall@50 on this evaluation set
- Recall metrics are tracked and reported during development

### 3.3 Latency Target

**As a** user in a conversational workflow,
**I want** first-pass retrieval to complete in under 1 second,
**so that** the search feels responsive within the conversation.

**Acceptance criteria:**
- Retrieval completes in < 1 second for an index of up to 50K declarations
- Latency is measured end-to-end from MCP tool call receipt to response

---

## Epic 4: Coq-Specific Normalization

### 4.1 Expression Normalization

**As a** developer relying on structural search,
**I want** Coq expressions to be normalized before indexing and comparison,
**so that** surface-level syntactic variation does not obscure structural similarity.

**Acceptance criteria:**
- Expressions are normalized so that surface-level syntactic variation does not affect retrieval
- Normalization handles at minimum: application form, type casts, universe annotations, projections, and notation expansion
- Section/module names are fully qualified
- Normalized forms are consistent between indexing and query time

---

## Epic 5: End-to-End User Experience

### 5.1 Natural Language Lemma Search

**As a** Coq developer using Claude Code,
**I want to** describe what I need in natural language and get a useful, explained result,
**so that** I can find lemmas without knowing exact names, types, or search syntax.

**Acceptance criteria:**
- The user describes a need conversationally (e.g., "find a lemma about commutativity of addition on natural numbers")
- The LLM formulates one or more tool calls to the MCP server
- The LLM filters results, selects the most relevant, and explains *why* each is relevant
- The user receives a useful answer within one conversational turn

### 5.2 Iterative Refinement

**As a** Coq developer whose initial search didn't find what I need,
**I want** the LLM to reformulate and retry searches automatically,
**so that** I don't have to manually guess different query strategies.

**Acceptance criteria:**
- When initial results are insufficient, the LLM issues follow-up tool calls with reformulated queries
- Reformulation strategies include: broadening symbol sets, following dependency links, trying different structural patterns, and name pattern variations
- The user sees the refined results without needing to re-prompt

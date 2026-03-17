# Vernacular Introspection — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Claude Code users working on Coq projects cannot currently inspect definitions, check types, evaluate expressions, or locate names without manually switching to a Coq toplevel and copying output back into the conversation. This constant context-switching breaks flow, introduces copy errors, and forces users to act as a relay between two tools that should be connected.

This initiative wraps Coq's built-in vernacular introspection commands — `Print`, `Check`, `About`, `Locate`, `Search`, `Compute`, and `Eval` — as MCP-accessible capabilities. These commands are the bread and butter of everyday Coq development: they answer questions like "what does this definition expand to?", "what is the type of this term?", "where is this name defined?", and "what does this expression reduce to?". By exposing them through the existing MCP server, Claude can answer these questions directly, keeping the developer in a single conversational workflow.

**Success metrics:**
- Claude can resolve type, definition, and location queries for all declarations in the Coq standard library without user intervention
- Round-trip latency for any single introspection command < 1 second
- Users report reduced context-switching between Claude Code and the Coq toplevel in qualitative feedback
- Commands work correctly both inside and outside active proof sessions

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq developers using Claude Code | Inspect types, definitions, and metadata without leaving the conversation | Primary |
| Coq learners and educators | Ask Claude to explain what a term computes to or what a definition contains | Primary |
| AI researchers building proof tools | Programmatic access to Coq's introspection commands for automated workflows | Secondary |

---

## 3. Competitive Context

**Current workflow (without this initiative):**
- User asks Claude about a Coq definition or type
- Claude either guesses (often incorrectly) or asks the user to run `Print`, `Check`, etc. in a separate toplevel
- User switches to CoqIDE, Proof General, or coq-lsp, runs the command, copies the output, and pastes it back into the conversation
- Claude can then reason about the actual output

**Lean ecosystem (comparative baseline):**
- Lean's language server exposes hover information, go-to-definition, and type information programmatically
- LeanDojo and related tools provide programmatic access to term evaluation and type checking
- Lean users working with AI tools benefit from tight integration between the language server and external tooling

**Coq ecosystem (current state):**
- coq-lsp provides hover and type information within IDE clients, but this information is not accessible to external tools like Claude Code
- SerAPI can execute vernacular commands programmatically, but is version-locked and not MCP-integrated
- No existing tool exposes Coq's introspection commands through a protocol accessible to AI assistants

**How this changes the workflow:**
- Claude issues introspection commands directly through the MCP server
- Results arrive in the conversation without user intervention
- Claude can chain multiple queries (e.g., locate a name, then print its definition, then check the type of a subterm) to build understanding autonomously

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R6-P0-1 | Show the full definition body of a named constant, inductive type, or fixpoint (equivalent to Coq's `Print`) |
| R6-P0-2 | Show the type of a given term or expression (equivalent to Coq's `Check`) |
| R6-P0-3 | Show metadata about a name, including its kind, defining module, and status (equivalent to Coq's `About`) |
| R6-P0-4 | Resolve a short or partial name to its fully qualified path (equivalent to Coq's `Locate`) |
| R6-P0-5 | Search for names matching a pattern or type constraint (equivalent to Coq's `Search`) |
| R6-P0-6 | Evaluate a term to its normal form (equivalent to Coq's `Compute`) |
| R6-P0-7 | Evaluate a term under a specified reduction strategy (equivalent to Coq's `Eval`) |
| R6-P0-8 | Bundle all introspection commands under a single MCP tool with a command parameter, to respect the tool count budget |
| R6-P0-9 | Return structured results including the command output and, where applicable, the fully qualified name of the inspected entity |
| R6-P0-10 | Return structured errors when a name is not found, a term is ill-typed, or a command is malformed |
| R6-P0-11 | Work both inside and outside an active proof session, using the ambient Coq environment in either case |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R6-P1-1 | Support `SearchPattern` and `SearchRewrite` variants in addition to basic `Search` |
| R6-P1-2 | Accept optional module or section scope qualifiers to restrict search and locate operations |
| R6-P1-3 | Support `Print Assumptions` to show the axioms a definition depends on |
| R6-P1-4 | Paginate or truncate large search results and indicate when results were truncated |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R6-P2-1 | Support `Print All` to show all declarations in a module |
| R6-P2-2 | Support `Inspect` for interactive exploration of large inductive types |
| R6-P2-3 | Cache recent introspection results to reduce redundant Coq round-trips |

---

## 5. Scope Boundaries

**In scope:**
- Wrapping Coq's existing vernacular introspection commands (`Print`, `Check`, `About`, `Locate`, `Search`, `Compute`, `Eval`) as a single MCP tool
- Operating within the existing Coq environment managed by the MCP server (loaded files, active proof sessions)
- Structured output formatting suitable for Claude's consumption
- Error handling for unknown names, ill-typed terms, and malformed commands

**Out of scope:**
- Modifying the Coq environment (no `Definition`, `Lemma`, `Require`, or tactic commands)
- Proof interaction (covered by the Proof Interaction Protocol initiative)
- Custom reduction strategies beyond those natively supported by `Eval`
- Natural language interpretation of introspection queries (Claude handles this upstream)
- Indexing or caching beyond single-session scope

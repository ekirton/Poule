# Universe Constraint Inspection — Product Requirements Document

Cross-reference: see [coq-ecosystem-opportunities.md](coq-ecosystem-opportunities.md) for ecosystem context.

## 1. Business Goals

Universe inconsistencies are among the most opaque errors in Coq. When `Universe inconsistency` appears, even experienced users face a multi-step debugging process: enabling universe printing, inspecting constraint graphs, identifying which definition introduced the conflicting constraint, and understanding why the constraint solver cannot find a satisfying assignment. The error messages provide almost no guidance — they name universe variables that bear no obvious relationship to the source-level definitions the user wrote.

This initiative wraps Coq's existing universe inspection commands (`Print Universes`, `Set Printing Universes`, and related vernacular) as MCP tools so that Claude can surface universe constraints on demand, explain inconsistency errors in context, and guide users through resolution. The underlying commands are mature and battle-tested; the value is making them discoverable, interpretable, and actionable through natural language.

**Success metrics:**
- Claude can retrieve and present universe constraints for any definition in a loaded Coq project
- Users report reduced time-to-resolution for universe inconsistency errors (target: > 50% reduction vs. manual debugging, measured via user study)
- Claude correctly identifies the conflicting constraint path in ≥ 80% of universe inconsistency errors drawn from a curated test set of ≥ 20 real-world examples
- Tool invocation latency < 3 seconds for constraint retrieval on standard library definitions

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Advanced Coq users and library authors | Diagnose and resolve universe inconsistency errors when composing large developments | Primary |
| Developers using universe-polymorphic definitions | Understand how universe levels are instantiated and constrained across module boundaries | Primary |
| Intermediate Coq users encountering universe errors for the first time | Get a plain-language explanation of what went wrong and how to fix it | Secondary |
| Educators teaching type theory or Coq internals | Demonstrate universe hierarchies and constraint propagation interactively | Tertiary |

---

## 3. Competitive Context

**Current state of universe debugging in Coq:**
- `Print Universes` dumps the entire universe constraint graph — often thousands of lines with no filtering or explanation
- `Set Printing Universes` annotates terms with universe levels, but the output is dense and hard to relate back to source definitions
- `Print Universes Subgraph` (Coq 8.16+) can filter to a subset but requires the user to know which universe variables to ask about
- No tooling exists to trace a universe inconsistency error back to the specific definitions and constraints that caused it

**Lean ecosystem:**
- Lean 4 uses a simpler universe system (universe variables with `max` and `+1` operations) that produces clearer error messages
- Universe errors in Lean are less frequent and more directly tied to source-level declarations
- No dedicated universe debugging tooling exists in Lean because the need is less acute

**Opportunity:**
- Coq's universe system is more complex than Lean's, making tooling more valuable
- The underlying Coq commands already exist — this is a low-cost wrapper with high user impact
- No existing tool (IDE, plugin, or standalone) provides contextual explanation of universe errors

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| RU-P0-1 | Print the universe constraints associated with a named definition, lemma, or inductive type |
| RU-P0-2 | Print the full universe constraint graph for the current environment |
| RU-P0-3 | Given a universe inconsistency error message, identify the conflicting constraints and the definitions that introduced them |
| RU-P0-4 | Explain a universe inconsistency error in plain language, including what the user can do to resolve it |
| RU-P0-5 | Show the universe level annotations on a term (equivalent to output under `Set Printing Universes`) |
| RU-P0-6 | Return structured output (not raw Coq text) so Claude can reason over constraints programmatically |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| RU-P1-1 | Show how a universe-polymorphic definition is instantiated at a specific use site, including the concrete universe levels substituted |
| RU-P1-2 | Filter the universe constraint graph to show only constraints reachable from a specified definition or universe variable |
| RU-P1-3 | Compare universe levels between two definitions to explain why one cannot be used where the other is expected |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| RU-P2-1 | Visualize the universe constraint subgraph as a directed graph (text-based or rendered) |
| RU-P2-2 | Suggest automatic fixes for common universe inconsistency patterns (e.g., adding universe polymorphism, adjusting universe declarations) |
| RU-P2-3 | Track universe constraint evolution across a proof session, showing how each tactic or command adds new constraints |

---

## 5. Scope Boundaries

**In scope:**
- MCP tool wrappers around Coq's existing universe inspection vernacular commands
- Structured parsing of universe constraint output for programmatic reasoning
- Plain-language explanation of universe inconsistency errors
- Inspection of universe-polymorphic instantiations

**Out of scope:**
- Modifying Coq's universe inference algorithm or constraint solver
- Automated universe polymorphism refactoring (beyond suggestion — actual code rewriting is deferred)
- Universe constraint visualization as interactive graphical widgets (deferred to Proof Visualization Widgets initiative)
- Support for custom universe hierarchy plugins or extensions

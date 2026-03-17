# Typeclass Instance Debugging — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Typeclass resolution failures are consistently cited as one of the top pain points for Coq users. When resolution fails, Coq produces cryptic error messages that give little indication of which instances were tried, why they were rejected, or what the resolution engine was searching for. Users — from newcomers to experienced library authors — waste significant time manually invoking `Set Typeclasses Debug`, parsing verbose unstructured traces, and cross-referencing `Print Instances` output to understand what went wrong. The debugging tools exist in Coq, but they are hard to discover, produce output that is difficult to interpret, and require expert knowledge to use effectively.

This initiative wraps `Set Typeclasses Debug`, `Print Instances`, `Print Typeclasses`, and related Coq vernacular commands as MCP tools so that Claude can trace typeclass instance resolution failures and explain — in plain language — why a particular instance was or was not selected. The development cost is low because the underlying Coq commands are mature and battle-tested; the value comes from making their output accessible through natural language.

**Success metrics:**
- Users can obtain a structured explanation of a typeclass resolution failure through a single natural-language request to Claude, without needing to know which Coq commands to run
- Time to diagnose a typeclass resolution failure is reduced by at least 50% compared to manual `Set Typeclasses Debug` usage (qualitative user evaluation)
- Claude correctly identifies the root cause of resolution failure (missing instance, ambiguous instances, or priority conflict) in at least 80% of cases in a test corpus of common typeclass errors
- All wrapped commands execute within 5 seconds for standard library-scale typeclass hierarchies

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq developers encountering typeclass errors | Understand why resolution failed and how to fix it, without learning the debug command interface | Primary |
| Library authors designing typeclass hierarchies | Inspect registered instances, detect conflicts and ambiguities, verify that new instances integrate correctly with existing hierarchies | Primary |
| Newcomers learning Coq | Get plain-language explanations of typeclass errors that would otherwise be impenetrable | Secondary |
| Educators and course instructors | Demonstrate typeclass resolution behavior to students in an accessible way | Secondary |

---

## 3. Competitive Context

**Coq's built-in debugging tools (current state):**
- `Set Typeclasses Debug` / `Set Typeclasses Debug Verbosity N`: Enables resolution tracing. Output is a raw, deeply nested, unstructured log dumped to the message pane. Users must manually parse indentation levels to reconstruct the search tree. No filtering, no summary, no explanation.
- `Print Instances <class>`: Lists registered instances for a typeclass. Output is a flat list with no priority information, no indication of which instances apply to a given goal, and no grouping.
- `Print Typeclasses`: Lists all registered typeclasses. Useful for discovery but provides no relational information.
- `Typeclasses eauto := debug`: Alternative debug flag for the resolution engine. Same unstructured output problem.

**Lean ecosystem:**
- Lean 4's typeclass resolution produces structured trace output and the language server provides hover-based instance information. The debugging experience is significantly more accessible than Coq's.

**IDE tooling:**
- Neither CoqIDE, VsCoq, nor Proof General provide any typeclass-specific debugging UI. Users interact with the raw Coq output.

**Gap:** No existing tool — IDE, CLI, or MCP — interprets Coq's typeclass debug output, structures it, or explains it. Claude, with access to the raw commands and the ability to reason about the output, fills this gap at minimal development cost.

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R-TC-P0-1 | Given a typeclass name, list all registered instances of that typeclass, including the instance name, type signature, and the module where it is defined |
| R-TC-P0-2 | Given a specific goal or proof state where typeclass resolution is needed, trace the resolution process and return a structured account of which instances were tried, in what order, and whether each succeeded or failed |
| R-TC-P0-3 | When resolution fails, identify and explain the root cause: no matching instance found, unification failure against a specific instance, or resolution depth exceeded |
| R-TC-P0-4 | Expose typeclass debugging capabilities as MCP tools compatible with Claude Code (stdio transport) |
| R-TC-P0-5 | Parse the output of `Set Typeclasses Debug` into a structured representation that Claude can reason about and present to the user |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R-TC-P1-1 | Show the resolution search tree for a given goal, including branching points where multiple instances were candidates and the engine's choice at each branch |
| R-TC-P1-2 | Identify ambiguous or conflicting instances: cases where two or more instances match a goal and resolution order or priority determines which is selected |
| R-TC-P1-3 | Given a specific instance, explain why it was or was not selected for a given goal (unification details, prerequisite constraints, priority) |
| R-TC-P1-4 | List all registered typeclasses in the current environment, with summary information (number of instances, whether they have default instances) |
| R-TC-P1-5 | Support configurable debug verbosity to control the level of detail in resolution traces |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R-TC-P2-1 | Suggest fixes for common resolution failures (e.g., "add an instance of X for type Y", "import module Z which provides the missing instance") |
| R-TC-P2-2 | Detect instance priority ordering issues and warn when a newly added instance may shadow an existing one |
| R-TC-P2-3 | Visualize the typeclass hierarchy and instance relationships for a given class (as structured data suitable for rendering) |

---

## 5. Scope Boundaries

**In scope:**
- MCP tool wrappers around `Set Typeclasses Debug`, `Print Instances`, `Print Typeclasses`, and related Coq vernacular commands
- Parsing and structuring the raw debug output into a representation Claude can reason about
- Tracing resolution for a specific goal and reporting structured results
- Instance listing and inspection
- Detection of ambiguous or conflicting instances

**Out of scope:**
- Modifying Coq's typeclass resolution engine or its behavior
- Building a standalone typeclass resolution visualizer or GUI
- Typeclass hierarchy design recommendations beyond what is directly observable from instance registrations
- IDE plugin development (VS Code, Emacs, etc.) — tools are accessed via Claude Code's MCP integration
- Automated instance synthesis or generation (suggesting code fixes is P2; generating and applying them is out of scope)

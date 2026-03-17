# Notation Inspection — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Notations are ubiquitous in Coq. Nearly every Coq development — from the standard library to large-scale verification projects — relies on custom notations to make terms readable: `_ + _`, `_ :: _`, `{ x : T | P }`, `_ =? _`, and hundreds more. Despite their prevalence, notations are one of the most opaque parts of the Coq ecosystem. When a user encounters an unfamiliar symbol, there is no straightforward way to answer the question "what does this notation mean?" The existing commands (`Locate Notation`, `Print Notation`, `Print Scope`) are poorly documented, require exact quoting conventions that differ from the notation's surface syntax, and return output that is dense and difficult to interpret without prior expertise.

This initiative wraps Coq's existing notation inspection commands as MCP tools so that Claude can look up what a notation expands to, find where it is defined, list the notations available in a given scope, explain notation syntax (precedence, associativity, format rules), and guide users in defining new notations. The underlying Coq commands are mature; the value is in making them discoverable, correctly invoked, and interpreted in natural language.

**Success metrics:**
- Claude can retrieve the expansion of any in-scope notation in a loaded Coq project and present it in plain language
- Users report reduced time to understand unfamiliar notations (target: > 60% reduction vs. manual lookup, measured via user study)
- Claude correctly identifies the defining module and scope for a notation in >= 90% of queries drawn from a curated test set of >= 30 notations across the standard library, MathComp, and Iris
- Tool invocation latency < 2 seconds for notation lookup on standard library notations

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq beginners learning from textbooks or tutorials | Understand what unfamiliar symbols mean when reading code examples or error messages | Primary |
| Intermediate Coq users working with third-party libraries | Discover notations introduced by libraries (MathComp, Iris, stdpp) and understand their precedence and scope | Primary |
| Advanced Coq users and library authors defining new notations | Get guidance on notation syntax, precedence levels, associativity, format rules, and reserved tokens | Secondary |
| Educators teaching Coq | Explain notation mechanics interactively and show students how to read and write notation declarations | Tertiary |

---

## 3. Competitive Context

**Current state of notation inspection in Coq:**
- `Locate Notation` can find where a notation is defined, but requires the user to quote the notation string in a specific way that is not always obvious from the surface syntax
- `Print Notation` (Coq 8.19+) prints the interpretation of a notation, but is new and not widely known
- `Print Scope` dumps all notations in a scope — often dozens or hundreds of entries with no filtering or explanation
- `Print Visibility` shows which scopes are open and in what order, but does not explain how scope stacking affects notation resolution
- No tooling connects a notation to its precedence, associativity, or format string in a single query

**Lean ecosystem:**
- Lean 4 notations are defined as ordinary macros with explicit syntax declarations; hovering over a notation in VS Code shows its definition directly
- Lean's `#check` command works on notation-bearing expressions and shows the desugared form
- The Lean infoview provides immediate feedback on notation expansion

**Opportunity:**
- Coq's notation system is significantly more complex than Lean's (scopes, precedence levels 0-200, left/right/no associativity, format strings, recursive notations, abbreviations, `only parsing`/`only printing` flags), making tooling more valuable
- The underlying Coq commands exist but are hard to use correctly — a natural-language wrapper removes the quoting and invocation barriers
- No existing tool (IDE, plugin, or standalone) provides contextual, plain-language explanation of notation mechanics

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| RN-P0-1 | Look up what a notation expands to, given the notation string or a term that uses it |
| RN-P0-2 | Find where a notation is defined (module, file, scope) |
| RN-P0-3 | List all notations registered in a given notation scope |
| RN-P0-4 | Show the precedence level, associativity, and format string for a notation |
| RN-P0-5 | Return structured output (not raw Coq text) so Claude can reason over notation metadata programmatically |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| RN-P1-1 | Explain notation syntax in plain language, including how precedence and associativity affect parsing |
| RN-P1-2 | Show which notation scopes are currently open and their stacking order, explaining how scope resolution determines which interpretation is selected when a notation is ambiguous |
| RN-P1-3 | Handle ambiguous notations by listing all interpretations across open scopes and identifying which one is currently active |
| RN-P1-4 | Given a user's intent (e.g., "infix operator for my custom addition at precedence 50, left-associative"), suggest a syntactically correct `Notation` or `Infix` command |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| RN-P2-1 | Explain the difference between `Notation`, `Infix`, and `Abbreviation` and recommend which to use for a given situation |
| RN-P2-2 | Detect potential notation conflicts (same symbol, overlapping precedence) before the user commits a definition |
| RN-P2-3 | Show notation evolution across Coq versions when a notation's definition has changed between releases |

---

## 5. Scope Boundaries

**In scope:**
- MCP tool wrappers around Coq's existing notation inspection vernacular commands (`Print Notation`, `Locate Notation`, `Print Scope`, `Print Scopes`, `Print Visibility`)
- Structured parsing of notation inspection output for programmatic reasoning
- Plain-language explanation of notation semantics, precedence, and associativity
- Guidance on defining new notations, including syntax suggestions

**Out of scope:**
- Modifying Coq's notation engine or parser
- Automated refactoring of existing notation declarations (beyond suggestion — actual code rewriting is deferred)
- Notation visualization as interactive graphical widgets (deferred to Proof Visualization Widgets initiative)
- Support for custom notation plugins or parser extensions outside Coq's standard notation mechanism
- Notations defined via Coq's `Declare Custom Entry` system (deferred to a future initiative once the standard notation tools are stable)

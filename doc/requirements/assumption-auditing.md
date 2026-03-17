# Assumption Auditing — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Every Coq theorem rests on a foundation of axioms. Developers routinely add axioms such as classical logic, functional extensionality, or proof irrelevance — sometimes deliberately, sometimes as transitive dependencies inherited from upstream libraries. When these assumptions go unexamined, three problems arise:

1. **Correctness assurance degrades.** An axiom that is inconsistent with the rest of a development silently renders every dependent theorem vacuously true. Developers need a fast, reliable way to audit what their theorems actually assume.
2. **Library compatibility breaks.** Two libraries that adopt incompatible axiom sets cannot be composed safely. Teams integrating third-party developments need to compare assumption profiles before committing to a dependency.
3. **Unintended classical reasoning creeps in.** Constructive developments that accidentally depend on the law of excluded middle or indefinite description lose their computational content. Developers working in constructive or extraction-oriented settings need early warning when classical axioms appear.

Coq's `Print Assumptions` command answers these questions, but it requires a live Coq session, operates on one theorem at a time, and produces raw output that demands manual interpretation. This initiative wraps that capability in MCP tools that Claude can invoke, adding classification, batch auditing, and explanatory context.

**Success metrics:**
- Correctly reports the full axiom set for any named theorem whose containing library is compiled and available
- Classifies every reported axiom into a recognized category (classical, extensionality, choice, proof irrelevance, custom) with ≥ 95% accuracy on standard library axioms
- Batch audit of a module with up to 200 theorems completes in under 30 seconds
- Zero false negatives: every axiom returned by `Print Assumptions` is surfaced to the user

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq formalization developers using Claude Code | Audit axiom dependencies of individual theorems during proof development, with classification and plain-language explanation | Primary |
| Library maintainers and integrators | Batch-audit an entire module or library to enforce axiom policies and verify compatibility before release | Primary |
| Constructive/extraction-oriented developers | Detect any classical or non-computational axioms that have leaked into a development intended to remain constructive | Secondary |
| Educators and students | Understand what axioms a textbook theorem depends on and why those axioms matter | Tertiary |

---

## 3. Competitive Context

**Coq ecosystem (current state):**
- `Print Assumptions` is built into Coq but requires a live session, operates on a single identifier, and returns unstructured output with no classification or explanation
- No existing tool provides batch auditing, axiom categorization, or assumption comparison across theorems
- CoqIDE and Proof General surface `Print Assumptions` output verbatim without further analysis

**Lean ecosystem (comparative baseline):**
- `#print axioms` provides similar per-declaration output; no batch or classification tooling exists in the standard ecosystem
- Some community linters check for `sorry` (Lean's equivalent of `admit`) but do not classify axiom usage

**Gap:** Neither ecosystem offers tooling that classifies axioms by category, explains their implications, audits at module granularity, or compares assumption profiles between theorems. This initiative fills that gap for Coq within the Claude Code workflow.

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R-P0-1 | List all axioms and opaque dependencies for a named theorem by invoking Coq's `Print Assumptions` command |
| R-P0-2 | List opaque dependencies (definitions admitted or ended with `Qed` that block reduction) separately from axioms |
| R-P0-3 | Classify each reported assumption into a recognized category: classical logic, functional extensionality, choice axioms, proof irrelevance, universe polymorphism axioms, or custom/user-defined axiom |
| R-P0-4 | Provide a short plain-language explanation for each recognized axiom describing what it asserts and its common implications |
| R-P0-5 | Expose assumption auditing as one or more MCP tools compatible with Claude Code (stdio transport) |
| R-P0-6 | Report when a theorem has no axiom dependencies beyond Coq's core (a "closed" theorem) |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R-P1-1 | Batch-audit all theorems in a given module, producing a summary of axiom usage across the module |
| R-P1-2 | Detect and flag theorems that depend on classical axioms within a development that is otherwise constructive |
| R-P1-3 | Compare the assumption profiles of two or more theorems, highlighting differences and shared axioms |
| R-P1-4 | Work from a pre-built index of compiled library files where possible, avoiding the need for a live Coq session for libraries already indexed |
| R-P1-5 | Expose batch auditing and comparison as MCP tools in addition to single-theorem auditing |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R-P2-1 | Suggest alternative formulations or library lemmas that avoid a flagged axiom when one exists |
| R-P2-2 | Produce a dependency graph visualization showing how axioms propagate through a chain of lemmas to the audited theorem |
| R-P2-3 | Track axiom profile changes over time so developers can detect assumption drift across versions of a development |

---

## 5. Scope Boundaries

**In scope:**
- MCP tool wrappers around Coq's `Print Assumptions` command for Claude Code integration
- Axiom classification and plain-language explanation for standard Coq axioms
- Single-theorem and batch-module auditing
- Assumption comparison between theorems
- Working from compiled `.vo` files and pre-built indexes where feasible

**Out of scope (this initiative):**
- Modifying or extending Coq's `Print Assumptions` command itself
- Axiom auditing for languages other than Coq/Rocq
- Automated axiom elimination or proof refactoring
- Web interface or IDE plugin deployment
- Neural or LLM-based axiom impact analysis

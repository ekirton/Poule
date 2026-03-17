# Proof Obligation Tracking

Large Coq developments accumulate incomplete proofs — `admit`, `Admitted`, and `Axiom` declarations that start as temporary scaffolding and quietly become permanent fixtures. Over time, no one remembers which axioms are intentional design decisions, which admits are forgotten TODOs, and which gaps pose real risk to the soundness of downstream theorems. Proof Obligation Tracking provides a `/proof-obligations` slash command that scans an entire project, classifies every obligation by intent and severity, and tracks progress toward completion across successive scans.

**Stories**: [Epic 1: Scanning and Detection](../requirements/stories/proof-obligation-tracking.md#epic-1-scanning-and-detection), [Epic 2: Classification](../requirements/stories/proof-obligation-tracking.md#epic-2-classification), [Epic 3: Reporting](../requirements/stories/proof-obligation-tracking.md#epic-3-reporting), [Epic 4: Progress Tracking](../requirements/stories/proof-obligation-tracking.md#epic-4-progress-tracking)

---

## Problem

Developers working on Coq formalizations routinely use `admit` and `Admitted` to defer proofs and `Axiom` to postulate facts. This is normal and necessary during incremental development. The problem is what happens next: there is no project-wide way to understand the state of all these obligations. A developer can grep for `admit`, but that tells them nothing about whether a given `Axiom functional_extensionality` is a deliberate foundation of the project or a shortcut someone took six months ago. It tells them nothing about which of twenty admits are most urgent to resolve, or whether the project is making progress toward completion.

Existing tools operate at the wrong granularity. `Print Assumptions` reports axioms for a single theorem, one at a time. IDE tooling highlights admits in individual files. Neither provides a project-wide inventory, and neither can answer the question that actually matters: "what is the intent behind this obligation?" Answering that question requires reading surrounding comments, understanding naming conventions, examining how the obligation fits into the dependency graph, and applying judgment — exactly the kind of contextual reasoning that static analysis cannot do.

## Solution

The `/proof-obligations` slash command gives users a complete picture of every incomplete proof obligation in their project, with each obligation classified by intent and ranked by severity.

### Project-Wide Scanning

A single invocation of `/proof-obligations` scans every `.v` file in the project and identifies all occurrences of `admit`, `Admitted`, and `Axiom`. Each obligation is reported with its file location, the enclosing definition or proof, and enough surrounding context to understand what it belongs to. Nothing is missed because the user forgot to check a subdirectory or a file they didn't know existed.

### Intent Classification

For each detected obligation, the command classifies its intent as one of three categories: an intentional axiom (a deliberate design decision that the project is built on), a TODO placeholder (something the developer intends to prove but hasn't yet), or unknown (insufficient context to determine intent). Classification draws on surrounding comments, naming conventions, the role of the obligation in the codebase, and any other contextual signals. This is where the feature provides value that no existing tool can match — turning a flat list of text matches into an annotated inventory that distinguishes finished architectural decisions from unfinished work.

### Severity Ranking

Each obligation receives a severity level — high, medium, or low — based on its classification, its position in the project's dependency graph, and contextual signals about urgency. A TODO admit in a theorem that dozens of other results depend on is more severe than an isolated admit in a leaf lemma. An intentional axiom that the entire project is built on is a known foundation, not an urgent problem. Severity ranking lets users focus their effort where it matters most.

### Progress Tracking

When the command is run repeatedly over the course of a development effort, it compares current results against previous scans and reports the delta: how many obligations were resolved, how many new ones were introduced, and whether the project is trending toward completion. This turns a point-in-time snapshot into a tool for managing long-running formalization efforts.

### Filtering

Users can narrow the report to a specific file, directory, severity level, or classification. A team member working on a particular module can see just the obligations relevant to their work. A reviewer preparing for a release can filter to high-severity TODOs to understand what still needs attention.

## Scope

Proof Obligation Tracking provides:

- Project-wide detection of all `admit`, `Admitted`, and `Axiom` declarations across `.v` files
- Classification of each obligation by intent: intentional axiom, TODO placeholder, or unknown
- Severity ranking based on classification, dependency impact, and contextual signals
- A structured summary report grouped by severity with counts and file locations
- Progress tracking across successive scans, with delta reporting
- Filtering by file, directory, severity, or classification
- Dependency reporting for axioms, showing which theorems transitively rely on each assumption

Proof Obligation Tracking does not provide:

- Automated resolution of proof obligations — it reports what is incomplete, it does not attempt to finish proofs (see [Hammer Automation](hammer-automation.md) and [Proof Search](proof-search.md) for automated proving)
- Modifications to Coq source files — the command is strictly read-only
- Real-time or continuous monitoring — scans are initiated by the user
- IDE integration or editor plugins
- Visualization of obligation data (see [Proof Visualization Widgets](proof-visualization-widgets.md) for visual representations)

---

## Design Rationale

### Why a slash command rather than an MCP tool

Proof obligation tracking is an inherently multi-step workflow: scan files, parse results, classify each obligation using contextual reasoning, rank by severity, compare against historical data, and produce a report. This is a conversation-level orchestration task, not a single tool invocation. Implementing it as a slash command lets Claude coordinate multiple MCP tools — file reading, vernacular introspection, assumption auditing — in a flexible sequence, applying natural language reasoning at each step. It also avoids adding to the MCP tool count, which matters because LLM accuracy degrades as the number of available tools grows.

### Why intent classification requires an LLM

A grep for `Axiom` finds every axiom declaration, but it cannot tell you whether `Axiom classical_logic : forall P, P \/ ~P` is a foundational assumption the project deliberately adopts or a placeholder someone used because they couldn't figure out the proof. That distinction lives in comments ("We assume classical logic here"), naming conventions (axioms prefixed with `Ax_` vs. lemmas named `todo_`), surrounding code structure, and implicit conventions that vary across projects. No static rule set can reliably make this judgment across diverse codebases. Natural language reasoning over the full context of each obligation is what makes classification accurate enough to be useful.

### Why severity ranking matters more than raw counts

A project with 50 admits is not necessarily in worse shape than a project with 10. What matters is the nature and impact of each obligation. A single admit in a core lemma that the entire development depends on is more urgent than a dozen admits in standalone examples. Severity ranking captures this by incorporating dependency information and classification: high-severity TODO obligations in high-impact positions surface first, while low-severity intentional axioms sink to the bottom. This lets users act on the report rather than being overwhelmed by a flat list.

### Why track progress over time

Formalization projects span months or years. Without progress tracking, each scan is an isolated snapshot that tells the user how much work remains but not whether the trend is positive. By persisting scan results and computing deltas, the command transforms from a diagnostic tool into a project management tool. Teams can see that they resolved 15 obligations this sprint, that 3 new ones were introduced, and that total obligation count is trending downward. This is especially valuable for formalization efforts with completion milestones or deadlines.

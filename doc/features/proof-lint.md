# Proof Style Linting and Refactoring

Large Coq formalizations accumulate stylistic debt as contributors come and go, Coq versions advance, and proof techniques evolve. Proof scripts end up with deprecated tactics that will break on the next upgrade, inconsistent bullet conventions that make proofs hard to follow, and unnecessarily complex tactic chains that obscure the proof's intent. Proof Style Linting and Refactoring gives users a `/proof-lint` slash command that scans proof scripts for these problems, explains what it found and why it matters, and — with the user's approval — applies safe, verified fixes.

**Stories**: [Epic 1: Deprecated Tactic Detection](../requirements/stories/proof-lint.md#epic-1-deprecated-tactic-detection), [Epic 2: Bullet Style Analysis](../requirements/stories/proof-lint.md#epic-2-bullet-style-analysis), [Epic 3: Tactic Chain Simplification](../requirements/stories/proof-lint.md#epic-3-tactic-chain-simplification), [Epic 4: Reporting](../requirements/stories/proof-lint.md#epic-4-reporting), [Epic 5: Automated Refactoring](../requirements/stories/proof-lint.md#epic-5-automated-refactoring), [Epic 6: Configuration](../requirements/stories/proof-lint.md#epic-6-configuration)

---

## Problem

Coq has no automated tool that understands both proof structure and stylistic conventions. The built-in deprecation mechanism emits warnings during compilation, but these warnings are scattered across compiler output, not aggregated or actionable. Bullet style — the way proof scripts mark subgoals with `-`, `+`, `*`, or braces — is entirely up to the author, and different contributors inevitably diverge. Tactic chains grow through incremental editing: a developer adds `simpl; reflexivity` where `auto` would suffice, or writes five manual `rewrite` steps that `autorewrite` could handle in one. Over time, these small inconsistencies compound into a maintenance burden that slows review, complicates onboarding, and makes version upgrades risky.

Existing tools do not help. The abandoned `coq-lint` project checked only superficial formatting. Lean 4's built-in linter handles syntax-level issues but does not reason about proof style or suggest refactorings. Mathlib's CI linting rules are hand-written for a single project. No tool combines the ability to understand why a tactic chain is unnecessarily complex with the ability to propose a simpler alternative and verify that the alternative still compiles.

## Solution

The `/proof-lint` slash command analyzes proof scripts for style issues and helps users fix them. It operates at three levels — individual files, directories, or entire projects — and addresses three categories of problems: deprecated tactics, inconsistent bullet style, and unnecessarily complex tactic chains.

### Deprecated Tactic Detection

When the user runs `/proof-lint`, the command scans proof scripts for tactics that have been deprecated in the target Coq version. Each deprecated tactic is reported with its location, an explanation of why it was deprecated, and the recommended replacement. At the project level, the summary shows the total scope of migration work, broken down by tactic name — giving formalization teams the information they need to plan a version upgrade.

### Bullet Style Analysis

Proof scripts use bullets and braces to structure subgoal navigation, but contributors rarely agree on which convention to use. `/proof-lint` detects inconsistencies both within a file (mixing bullet styles in different proofs) and across a project (files that deviate from the dominant convention). When scanning a project, it identifies the prevailing style and flags deviations, so team leads can enforce a uniform convention without reading every file.

### Tactic Chain Simplification

Some tactic sequences can be replaced by simpler alternatives without changing the proof's meaning. A chain of manual `rewrite` steps using lemmas from a known rewrite database can become a single `autorewrite`; a `simpl; reflexivity` can become `auto`. `/proof-lint` identifies these opportunities and suggests concrete replacements. Because simplification is inherently judgment-dependent, suggestions are presented for review rather than applied silently.

### Verified Refactoring

Detection alone is not enough — users need to act on what `/proof-lint` finds. When the user approves a suggested change, the command applies it and verifies that the modified proof still compiles. If the refactored proof fails, the change is reverted and the user is told that manual intervention is required. This guarantee — that no applied refactoring breaks a proof — is what makes automated style cleanup safe enough to use on production codebases.

### Reporting

Every scan produces a structured report: issues grouped by file, classified by category and severity, each with a human-readable explanation. A summary view shows issue counts by category and severity across the scanned scope, and lists the files with the most issues. The report gives formalization team leads the visibility they need to prioritize cleanup work and track progress over time.

### Configuration

Different teams have different conventions. A project can configure its preferred bullet style, mark certain deprecated tactics as intentionally retained, and define which patterns to ignore. When a configuration is present, `/proof-lint` uses it as the baseline; when it is absent, the command infers the dominant style from the codebase and uses sensible defaults.

## Scope

Proof Style Linting and Refactoring provides:

- Detection of deprecated tactics for the target Coq version, with recommended replacements
- Detection of inconsistent bullet style within files and across projects
- Detection of unnecessarily complex tactic chains with concrete simplification suggestions
- Structured lint reports with issue classification, severity, and human-readable explanations
- Automated application of approved refactorings with proof validity verification
- File-level, directory-level, and project-level scanning
- Configurable project-specific style preferences

Proof Style Linting and Refactoring does not provide:

- Enforcement of formatting rules unrelated to proof structure (indentation, line length, whitespace) — these are better served by a standalone formatter
- Proof rewriting that changes the mathematical argument — only style-preserving refactorings are in scope
- Modifications to Coq's built-in deprecation warning system
- Custom tactic development or tactic library creation
- IDE plugin integration or real-time keystroke-level linting — the command operates on saved files
- CI pipeline integration — though the reports it produces could be consumed by CI tooling in the future

---

## Design Rationale

### Why a slash command rather than an MCP tool

Proof style linting requires multi-step reasoning: parse proof structure, identify issues against stylistic conventions and deprecation knowledge, propose rewrites, and verify that rewrites compile. Each of these steps involves different MCP tools — vernacular introspection, proof interaction, tactic documentation — orchestrated in a sequence that depends on intermediate results. A single MCP tool cannot express this workflow; a slash command can orchestrate the tools agentic­ally, adapting its strategy based on what it finds.

### Why detection and refactoring are combined

A linter that only reports problems creates work without reducing it. Users who see a list of fifty deprecated tactics still need to fix each one by hand. By combining detection with verified refactoring, `/proof-lint` closes the loop: the user reviews the suggestion, approves it, and the change is applied and verified in one step. Separating detection from refactoring into different commands would force users to context-switch between "find the problem" and "fix the problem," losing the issue's context along the way.

### Why refactoring requires verification

Proof scripts are not ordinary source code. A syntactically valid replacement tactic may fail to close the same goal, or may close a different goal than intended. Replacing a deprecated tactic with its documented successor is usually safe, but tactic chain simplifications can change proof behavior in subtle ways. Verifying every applied change through the proof interaction protocol ensures that no refactoring is committed unless it produces a proof that Coq accepts. The cost of re-checking a proof is small compared to the cost of debugging a broken proof later.

### Why bullet style is inferred rather than prescribed

There is no universally agreed-upon bullet convention in the Coq community. Some projects prefer `-`/`+`/`*` nesting; others use braces for all subgoal structuring. Prescribing a single convention would make `/proof-lint` unusable for any project that disagrees with the prescription. Instead, the command infers the dominant convention from the codebase and flags deviations from it. Teams that want to enforce a specific style can do so through configuration; teams that have no preference get a reasonable default derived from their own code.

### Why project-level scanning matters

Style inconsistency is fundamentally a project-level problem. A single file may be internally consistent but use a different convention than every other file in the project. Deprecated tactics may be concentrated in a few files or spread thinly across hundreds. Without project-level scanning, a team lead would need to run `/proof-lint` on each file individually and aggregate the results manually. Project-level scanning provides the bird's-eye view that formalization teams need to manage style debt across large codebases.

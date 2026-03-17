# Proof Repair on Version Upgrade

Upgrading Coq versions is one of the most painful recurring tasks in the ecosystem. Between major releases, lemmas are renamed, tactics are deprecated, type inference changes, and implicit argument defaults shift — breaking dozens to hundreds of proofs across a project. Developers spend days to weeks on manual repair, and some projects simply stop upgrading. Proof Repair on Version Upgrade delivers a `/proof-repair` slash command that automates the core upgrade repair loop: build the project, diagnose what broke, find replacements, attempt fixes, and retry — iterating until all proofs compile or a clear report tells the user exactly where human judgment is needed.

**Stories**: [Epic 1: Build Error Detection and Classification](../requirements/stories/proof-repair.md#epic-1-build-error-detection-and-classification), [Epic 2: Renamed Lemma Search and Replacement](../requirements/stories/proof-repair.md#epic-2-renamed-lemma-search-and-replacement), [Epic 3: Deprecated Tactic and Migration Pattern Fixes](../requirements/stories/proof-repair.md#epic-3-deprecated-tactic-and-migration-pattern-fixes), [Epic 4: Hammer Fallback and Automated Re-Proving](../requirements/stories/proof-repair.md#epic-4-hammer-fallback-and-automated-re-proving), [Epic 5: Iterative Feedback Loop](../requirements/stories/proof-repair.md#epic-5-iterative-feedback-loop), [Epic 6: Reporting and User Review](../requirements/stories/proof-repair.md#epic-6-reporting-and-user-review), [Epic 7: Partial and Targeted Repair](../requirements/stories/proof-repair.md#epic-7-partial-and-targeted-repair)

---

## Problem

When a Coq project upgrades to a new version of the compiler, proofs break for reasons that are mechanical but tedious to fix. A lemma the proof relied on has been renamed. A tactic it used has been deprecated or removed. A type signature changed in a way that shifts implicit arguments. Each broken proof requires the developer to read the error, consult the changelog, search the standard library for the replacement name, try a fix, rebuild, and see if it worked — then repeat for the next proof. Multiply this across a large formalization and the cost becomes prohibitive.

No existing tool automates this process. The Coq changelog documents breaking changes, but applying them is entirely manual. CoqHammer can sometimes re-prove goals that broke due to minor changes, but someone must manually identify each broken goal and invoke it. Community migration guides provide rename maps but require manual application. The result is that version upgrades are a leading cause of project abandonment in the Coq ecosystem.

## Solution

The `/proof-repair` command takes a Coq project that fails to compile after a version upgrade and works through the breakages systematically. The user invokes the command, optionally specifying the target Coq version, and the workflow handles the rest — building the project, diagnosing each failure, attempting the appropriate fix, and repeating until it converges.

### Error Diagnosis

The workflow begins by building the project and capturing every compilation error along with its location and surrounding proof context. Each error is classified by its likely cause: a renamed lemma, a removed or deprecated tactic, a changed type signature, an implicit argument shift, or something else entirely. This classification determines which repair strategy is applied. When the user specifies the Coq version pair (e.g., 8.18 to 8.19), the workflow consults version-specific migration knowledge to make more precise diagnoses.

### Targeted Repair Strategies

Different categories of breakage call for different fixes. When a lemma has been renamed, the workflow searches for the replacement by name similarity and type signature, verifying that the candidate has a compatible type before substituting it. When a tactic has been deprecated, the workflow applies the known replacement (e.g., `omega` becomes `lia`). When implicit arguments have changed, the workflow inspects the old and new signatures and adjusts call sites accordingly. Each strategy is matched to the error category so that simple, high-confidence fixes are applied first.

### Automated Re-Proving as Fallback

Some proof breakages resist targeted fixes — the change is too subtle, the replacement is not a simple rename, or the proof strategy itself needs to change. For these cases, the workflow falls back to CoqHammer, attempting to re-prove the goal from scratch using automated theorem proving. If the goal is within reach of automation, the user gets a working proof without having to understand what changed.

### Iterative Feedback Loop

Proof repair is not a single pass. Fixing one file can resolve cascading errors in files that depend on it, and a fix attempt that seemed correct might introduce new problems. The workflow rebuilds the project after each batch of fixes, re-diagnoses remaining errors, and iterates. It processes files in dependency order so that upstream fixes eliminate downstream cascading failures naturally. The loop continues as long as progress is being made, and stops when all proofs compile or no further automatic fixes succeed.

### Repair Report

At the end of the process, the user receives a structured report. For each automatically repaired proof, the report shows what was broken, what fix was applied, and the diff. For each proof that could not be repaired, the report shows the current error, every strategy that was attempted, and why each failed. The user can focus manual effort precisely where it is needed rather than wading through hundreds of errors to find the ones that actually require human judgment.

## Scope

Proof Repair on Version Upgrade provides:

- A `/proof-repair` slash command that orchestrates the full repair loop
- Build error capture and classification by cause (renamed lemma, deprecated tactic, changed signature, implicit argument shift)
- Automated search for replacement lemmas by name and type signature
- Application of known tactic migrations across Coq version pairs
- CoqHammer fallback for goals that resist targeted fixes
- Iterative build-diagnose-fix-rebuild loop with convergence detection
- Dependency-ordered processing so upstream fixes resolve downstream cascading errors
- A structured report of repair outcomes with diffs for user review
- Support for `coq_makefile` and Dune build systems
- Partial repair mode for targeting a subset of files or directories
- Real-time progress display during the repair process

Proof Repair on Version Upgrade does not provide:

- Repair of errors unrelated to version upgrades (e.g., logic errors in new developments)
- Modifications to the Coq compiler or its error reporting
- A standalone tool outside the Claude Code environment
- Correctness guarantees beyond successful compilation — the user must review all changes
- Support for proof assistants other than Coq (Lean, Isabelle, Agda)
- Handling of OCaml plugin API changes or Coq plugin compatibility
- Automation of opam switch creation or Coq installation

---

## Design Rationale

### Why a slash command rather than individual tool calls

Version-upgrade repair is inherently a multi-step, multi-tool workflow: build the project, parse errors, search for replacements, interact with proofs, invoke hammer, rebuild. Asking the user to manually orchestrate these steps defeats the purpose — the whole point is to automate the tedious loop. A slash command lets the user express a single intent ("repair my project after this upgrade") and have the workflow manage the orchestration, tool selection, and iteration internally. The individual MCP tools remain available for users who want fine-grained control over a specific proof, but the common case of "fix everything that broke" should be a single action.

### Why classify errors before attempting repairs

Not all version-upgrade breakages are the same, and applying the wrong repair strategy wastes time and can introduce new errors. A renamed lemma calls for a search-and-replace. A deprecated tactic calls for a known substitution. A changed type signature might require adjusting implicit arguments. Attempting CoqHammer on a renamed-lemma error is wasteful when a simple name substitution would work in seconds. Classification lets the workflow apply the cheapest, highest-confidence fix first and reserve expensive strategies like automated re-proving for cases that genuinely need them.

### Why iterate rather than fix everything in one pass

Coq projects have deep dependency chains. An error in an early file can cause dozens of cascading errors in files that import it. Attempting to fix every error in a single pass would waste effort on errors that are mere symptoms rather than root causes. By rebuilding after each batch of fixes and re-diagnosing, the workflow discovers which errors were cascading consequences that resolved on their own, and which are independent breakages that need their own repairs. This also provides a natural convergence check: if an iteration makes no progress, the workflow knows to stop.

### Why process files in dependency order

When file B imports file A, errors in B may be caused by unfixed errors in A rather than by anything wrong in B itself. Processing files in dependency order — upstream first — ensures that cascading errors are eliminated at their source. This avoids wasted repair attempts on symptoms that disappear once the root cause is fixed, and reduces the total number of iterations the feedback loop needs to converge.

### Why fall back to CoqHammer

Some version-upgrade breakages are not simple renames or tactic substitutions. A proof strategy that worked in one version may fail in the next because of subtle changes to unification, type inference, or reduction behavior. In these cases, the most effective approach is often to re-prove the goal from scratch using automation. CoqHammer covers a large fraction of first-order goals and can frequently find alternative proofs that work under the new version's semantics, even when the original proof strategy no longer applies.

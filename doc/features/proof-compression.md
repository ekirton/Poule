# Proof Compression

Proof scripts accumulate tactical debt over time: chains of rewrites that a single lemma application could replace, sequences of introductions and destructions that hammer dispatches in one step, intermediate assertions that a more direct path renders unnecessary. Proof Compression provides a `/compress-proof` slash command that takes a working proof and systematically searches for shorter or cleaner alternatives — trying hammer tactics, searching for more direct lemmas, and simplifying tactic chains — then presents ranked options for the user to review. The original proof is always preserved; the user decides whether to adopt any alternative.

**Stories**: [Epic 1: Proof Analysis](../requirements/stories/proof-compression.md#epic-1-proof-analysis), [Epic 2: Alternative Strategy Attempts](../requirements/stories/proof-compression.md#epic-2-alternative-strategy-attempts), [Epic 3: Verification and Comparison](../requirements/stories/proof-compression.md#epic-3-verification-and-comparison), [Epic 4: Safe Replacement](../requirements/stories/proof-compression.md#epic-4-safe-replacement), [Epic 5: Reporting](../requirements/stories/proof-compression.md#epic-5-reporting)

---

## Problem

A proof that works is not necessarily a proof that is finished. In large formalizations, proof scripts grow verbose through natural development: the developer tries tactics until something works, builds up intermediate steps to navigate an unfamiliar goal, or pieces together rewrites without knowing a library lemma that handles the case directly. The result is proofs that are longer than they need to be — harder to read during review, harder to maintain when upstream definitions change, and harder for newcomers to learn from.

The tools to find shorter proofs already exist individually. CoqHammer can sometimes replace a multi-step proof with a single tactic call. Lemma search can surface library lemmas the developer did not know about. Tactic sequences can often be collapsed. But applying these tools to an existing proof is entirely manual: the developer must identify which proof might benefit, try each strategy by hand, verify the result, and compare alternatives. This is tedious enough that most developers skip it unless they are preparing a library for release.

What is missing is a way to say "this proof works — find me something shorter" and have the search happen automatically.

## Solution

The `/compress-proof` command takes a working proof and explores multiple compression strategies, presenting verified alternatives that the user can adopt or ignore.

### Multi-Strategy Exploration

When invoked on a proof, `/compress-proof` tries several approaches to find a shorter alternative. It attempts hammer tactics (`hammer`, `sauto`, `qauto`) as single-tactic replacements for the entire proof. It searches for library lemmas that close the goal directly, replacing multi-step reasoning with a single application. It looks for tactic chains that can be collapsed into fewer steps — consecutive introductions, redundant rewrites, sequences that a combined tactic handles. Each strategy runs independently, so a failure in one does not prevent the others from succeeding.

### Verified Alternatives Only

Every candidate alternative is checked by Coq before the user sees it. If a candidate does not compile, it is silently discarded. The user never has to wonder whether a suggested alternative actually works — if it appears in the results, it has been verified.

### Comparison and Ranking

When multiple alternatives are found, they are ranked and presented with a clear comparison against the original proof: how many tactic steps each uses, what strategy produced it, and the full proof script. The user can see at a glance whether the compressed version is worth adopting. When only one alternative is found, it is presented directly. When no compression is possible, the command says so and explains which strategies were tried.

### Safe by Default

The original proof is never modified without explicit user consent. `/compress-proof` is a read-only exploration — it analyzes, searches, and reports, but leaves the source file untouched until the user chooses to apply an alternative. If the user does select an alternative, it replaces the original proof in the source file, and standard editor undo or version control can restore the original at any time.

### Sub-Proof Targeting

Compression can target a specific proof step or subproof rather than the entire proof. This lets the user focus on the parts they know are verbose — a particular case in a case analysis, a long chain of rewrites in one branch — without waiting for the entire proof to be analyzed.

## Scope

Proof Compression provides:

- A `/compress-proof` slash command that orchestrates existing MCP tools
- Hammer-based compression: trying `hammer`, `sauto`, and `qauto` as single-tactic replacements
- Lemma-search-based compression: finding direct lemmas that close the goal without intermediate steps
- Tactic chain simplification: collapsing sequences of tactics into fewer steps
- Verification of every candidate alternative against the Coq kernel before presenting it
- Ranked comparison of alternatives against the original proof
- Safe replacement with explicit user consent
- Sub-proof and single-step targeting
- Batch mode for scanning all proofs in a file or module

Proof Compression does not provide:

- Modifications to any underlying MCP tools (hammer, proof interaction, lemma search) — it orchestrates them as-is
- Proof synthesis for unproven goals — this feature works only on proofs that already compile (see [Proof Search](proof-search.md) for proving open goals)
- Proof style enforcement beyond what informs compression ranking (see [Proof Style Linting](proof-style-linting.md) for style conventions)
- Semantic equivalence checking beyond Coq kernel acceptance
- Automated application without user review — the user always decides whether to adopt an alternative

---

## Design Rationale

### Why a slash command rather than an MCP tool

Proof compression is an inherently multi-step workflow: verify the original proof, extract the goal, try multiple strategies, verify candidates, compare results, and present options. This is orchestration over existing tools, not a single operation that belongs in the tool layer. A slash command lets Claude reason through the workflow, adapt to intermediate results (e.g., skip lemma search if hammer already found a one-tactic proof), and present results conversationally. Encoding this logic in a single MCP tool would make it rigid and opaque.

### Why try multiple strategies rather than picking one

No single compression strategy dominates. Hammer tactics excel at first-order goals but cannot simplify tactic chains. Lemma search finds direct library applications that hammer might miss because the lemma does not follow from first principles alone. Tactic chain simplification helps even when no fundamentally different proof exists. Trying all strategies and letting the user choose among verified alternatives produces better results than any single strategy could.

### Why verify before presenting

An unverified "shorter proof" is worse than no suggestion at all. If the user adopts an alternative that does not compile, they have lost the time spent reviewing it and must revert. By verifying every candidate against the Coq kernel, the command guarantees that any alternative the user sees is ready to use. The cost is additional Coq invocations, but this is far less expensive than the user's time debugging a broken proof.

### Why preserve the original proof by default

Proof compression is exploratory. The user may want to see what is possible without committing to any change. They may prefer the original proof for readability reasons even when a shorter alternative exists. They may want to review alternatives across multiple proofs before deciding which to adopt. Making the command read-only by default removes the risk of exploring compression and lets the user apply changes deliberately.

### Why shorter proofs matter

Shorter proofs are not just an aesthetic preference. A proof that uses fewer tactics has fewer points where an upstream change can cause breakage. A proof that applies a library lemma directly is more robust than one that re-derives the same result through intermediate steps — if the library changes its internal representation, the direct application still works while the re-derivation may not. Shorter proofs are also faster to review, easier for newcomers to understand, and quicker for Coq to check. In large formalizations, these advantages compound across hundreds or thousands of proofs.

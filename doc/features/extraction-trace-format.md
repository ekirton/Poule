# Extraction Trace Format

The structured output format for extracted proof traces: what each record contains, how records are organized, and what metadata accompanies the dataset.

**Stories**: [Epic 2: Proof Trace Record Structure](../requirements/stories/training-data-extraction.md#epic-2-proof-trace-record-structure), [Epic 3: Output Format and Schema](../requirements/stories/training-data-extraction.md#epic-3-output-format-and-schema)

---

## Problem

Existing Coq proof datasets (CoqGym) use ad hoc formats that conflate proof text with metadata, lack premise annotations, and provide no schema versioning. Downstream consumers must reverse-engineer the format from examples. When the format changes, tools break silently.

AI researchers need two things from the same dataset: linearized proof traces for tactic prediction (state → tactic → next_state) and premise annotation pairs for retrieval training (goal → premises_used). No existing format serves both consumers in a unified schema.

## Solution

Each proof produces one record containing:

- **Theorem identity** — fully qualified name and source file path
- **Per-step proof states** — goals, hypotheses, and local context at every tactic step (N+1 states for N tactics)
- **Per-step tactic text** — the tactic applied at each step
- **Per-step premise annotations** — which lemmas, hypotheses, constructors, and definitions each tactic used, with fully qualified names and kinds
- **Proof state diffs** (P1) — what changed between consecutive states, alongside full snapshots

The output uses JSON Lines format: one JSON object per line, one proof per record. Each record includes a schema version field. The dataset includes provenance metadata: Coq version, project commit hash, extraction tool version, and extraction timestamp.

## Design Rationale

### Why JSON Lines over alternatives

JSON Lines (one JSON object per line) enables streaming consumption — a consumer can process records one at a time without loading the entire dataset. This matters at scale: a 100K-theorem dataset in a single JSON array would require full deserialization before any record is accessible. JSON Lines also enables parallel processing (split by line), append-friendly writes (crash recovery loses at most one record), and simple concatenation of multi-project outputs.

Alternatives considered:
- **Parquet/Arrow**: better compression and columnar access, but requires specialized tooling and is harder to inspect manually. A P2 requirement covers ML framework export for this use case.
- **SQLite**: good for random access, but streaming writes are slower and the format is harder to diff in version control.
- **Protocol Buffers**: compact and fast, but adds a compilation step and reduces accessibility for researchers who want to inspect data with standard tools.

### Why per-step granularity rather than per-proof summaries

Tactic prediction models need the (state_k, tactic_k, state_{k+1}) triple at every step. Premise selection models need the (goal_k, premises_k) pair at every step. Per-proof summaries (e.g., "this proof used these 12 lemmas") lose step-level alignment, which is critical for training both model types. LeanDojo uses per-step granularity for the same reason.

### Why include both full states and diffs

Full proof states at every step are self-contained — a consumer can process any step independently without reading prior steps. Diffs capture the tactic's effect compactly — "this tactic split one goal into two and added a hypothesis." Both views are valuable: full states for training, diffs for analysis and visualization. Including both avoids forcing every consumer to compute diffs from full states.

### Why provenance metadata is P0

Without provenance, a dataset file is an opaque artifact. Researchers need to know: which Coq version compiled the project (behavior varies across versions), which commit of the project was extracted (proofs change over time), which version of the extraction tool produced the output (schema may evolve), and when extraction happened (for audit trails). This metadata enables exact reproduction of any dataset.

### Why schema versioning in every record

When the extraction format evolves, downstream tools must detect the change. A schema version field in each record (not just in file-level metadata) means that even concatenated or shuffled datasets remain self-describing. A consumer can handle mixed-version datasets by dispatching on the version field.

## Scope Boundaries

The extraction trace format provides:

- Per-step proof states, tactics, and premise annotations in a unified record
- JSON Lines output with schema versioning
- Provenance metadata for reproducibility
- Proof state diffs alongside full snapshots (P1)

It does **not** provide:

- ML-framework-specific formats (HuggingFace, PyTorch — separate P2 feature)
- Compressed or columnar formats (Parquet, Arrow)
- Tokenized or embedded representations of proof states
- Cross-proof or cross-project aggregation (that is a dataset-level concern)

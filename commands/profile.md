Profile Coq proof compilation time, identify bottlenecks, and suggest optimizations. This command is read-only — it measures performance and reports findings. It never modifies source files.

## Determine the profiling target

Parse the user's arguments:

- **A file path** (e.g., `src/Core.v`): profile all proofs in the file, ranked by compilation time.
- **A file path and lemma name** (e.g., `src/Core.v Nat.add_comm`): profile a specific proof in detail.
- **`--compare <baseline>`**: compare current timing against a previous profiling run.
- **`--ltac <lemma_name>`**: break down Ltac tactic execution time within a specific proof.
- **No arguments**: ask the user what to profile.

## Step 1: Run the profiler

### File-level profiling (default)

1. Call `profile_proof` with the `file_path` and `mode` set to `timing`.
2. The tool compiles the file with timing instrumentation and returns per-sentence timing, ranked from slowest to fastest.

### Single-proof profiling

1. Call `profile_proof` with `file_path`, `lemma_name`, and `mode` set to `timing`.
2. The tool returns per-tactic timing within that proof, plus the Qed time separately.

### Ltac profiling

1. Call `profile_proof` with `file_path`, `lemma_name`, and `mode` set to `ltac`.
2. The tool returns a call-tree breakdown of Ltac execution — which sub-tactics consumed the most time.

### Comparison profiling

1. Call `profile_proof` with `file_path`, `baseline_path`, and `mode` set to `compare`.
2. The tool returns a diff showing which proofs got faster, slower, or stayed the same.

## Step 2: Present the results

### File-level report

1. **Summary** — "Profiled N sentences in `file.v`: total compilation time X.Xs."
2. **Top bottlenecks** — List the 5-10 slowest sentences, each with:
   - The sentence text (truncated if long).
   - Time in seconds.
   - Bottleneck category (e.g., "slow Qed", "expensive typeclass search", "deep auto search", "simpl in *").
   - Concrete optimization suggestion.
3. **Qed vs tactic breakdown** — For proofs where Qed dominates, explain that Qed time is kernel proof-term re-checking, not tactic execution — and suggest `abstract` or `Defined` where appropriate.

### Single-proof report

1. **Proof overview** — Lemma name, total time, number of tactic steps.
2. **Per-tactic timing** — Each tactic step with its time, ranked slowest-first.
3. **Qed time** — Shown separately with explanation.
4. **Bottleneck analysis** — For each slow tactic:
   - Root cause explanation (e.g., "`simpl in *` unfolds aggressively across all hypotheses").
   - Concrete suggestion (e.g., "Replace `simpl in *` with `simpl in H1, H2` targeting specific hypotheses").
5. **Quick wins** — Highlight any changes that would save >50% of the proof's time.

### Ltac profiling report

1. **Call tree** — Show the Ltac call hierarchy with per-call timing.
2. **Hotspots** — Flag sub-tactics consuming >20% of total time.
3. **Explanation** — For each hotspot, explain why it is slow and suggest alternatives.

### Comparison report

1. **Regressions** — Proofs that got slower, sorted by absolute time increase.
2. **Improvements** — Proofs that got faster.
3. **Unchanged** — Proofs within 10% of baseline (collapsed).
4. **Net change** — Total compilation time difference.

## Edge cases

- **File does not compile**: The profiler requires a compilable file. If compilation fails, report the first error and suggest fixing it before profiling.
- **Very large files (>5000 lines)**: Set `timeout_seconds` to 600 (10 minutes). Warn the user that profiling may take a while.
- **Qed-dominated proofs**: When Qed time is >80% of total, focus the report on Qed optimization strategies (opaque sub-proofs via `abstract`, splitting into helper lemmas, `Defined` vs `Qed` trade-offs).
- **No slow proofs found**: If all sentences complete in <0.5s, say so and suggest that profiling is not a concern for this file.

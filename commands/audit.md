Audit axiom dependencies for Coq theorems, modules, or comparisons. This command is read-only — it reports what axioms are assumed, classifies them, and explains their implications. It never modifies source files.

## Determine the audit mode

Parse the user's arguments to determine which mode to use:

- **A single theorem name** (e.g., `Nat.add_comm`): single-theorem audit.
- **A module name or path** (e.g., `Coq.Arith.PeanoNat`, `src/Core.v`): module-wide audit.
- **Two or more theorem names** (e.g., `lem1 lem2 lem3`): comparison audit.
- **No arguments**: ask the user what to audit.

Optional flags:
- `--flag <category>`: in module mode, flag theorems using axioms in the given category (classical, extensionality, choice, proof_irrelevance, custom). Can be repeated.
- `--constructive`: shorthand for `--flag classical --flag choice` — flags anything that blocks extraction to constructive code.

## Step 1: Open a proof session

1. Determine the file containing the target theorem(s) or module. If the user gave a fully qualified name, use `search_by_name` to locate the file. If the user gave a file path, use that directly.
2. Call `open_proof_session` on the file.

If the file cannot be found, report the error and stop.

## Step 2: Run the appropriate audit

### Single-theorem mode

1. Call `audit_assumptions` with the theorem name and session ID.
2. The tool returns a classified list of axioms: each axiom is tagged with a category (classical, extensionality, choice, proof_irrelevance, custom) and a plain-language explanation of what it means.

### Module-wide mode

1. Call `audit_module` with the module name, session ID, and any `flag_categories` from the user's flags.
2. The tool returns per-theorem axiom summaries and flags theorems that use axioms in the flagged categories.

### Comparison mode

1. Call `compare_assumptions` with the list of theorem names and session ID.
2. The tool returns a comparison showing axioms unique to each theorem and axioms shared across all of them.

## Step 3: Present the report

### Single-theorem report

Structure the output as:

1. **Theorem name and statement** — one line.
2. **Axiom-free?** — If the theorem has no axiom dependencies, say so clearly: "This theorem is closed — it depends on no axioms." Stop here.
3. **Axiom list** — For each axiom:
   - Name and category tag.
   - One-sentence plain-language explanation (e.g., "Functional extensionality — two functions that agree on all inputs are considered equal").
4. **Implications** — Summarize what the axioms mean practically:
   - Is the theorem constructive? Can it be extracted to OCaml/Haskell?
   - Are any axioms potentially unintended (e.g., classical logic in a constructive development)?
5. **Suggestions** — If there are concerning axioms, suggest alternatives (e.g., "Consider using `Decidable` instead of `Classical_Prop` to avoid classical logic").

### Module-wide report

1. **Summary line** — "Audited N theorems in module M: X axiom-free, Y with classical, Z with choice."
2. **Flagged theorems** — List theorems using flagged axiom categories, grouped by category. For each, show the theorem name and which axioms it uses.
3. **Clean theorems** — Optionally list axiom-free theorems (collapse if there are many).
4. **Recommendations** — Note patterns (e.g., "All theorems in the `Decidable` section are axiom-free; classical axioms are concentrated in `Classical_Facts`").

### Comparison report

1. **Side-by-side table** — For each theorem, list its axioms.
2. **Shared axioms** — Axioms common to all theorems.
3. **Unique axioms** — Axioms appearing in only one theorem.
4. **Verdict** — Which theorem has the weakest assumptions, and whether the difference matters practically.

## Edge cases

- **Theorem not found**: Report the error with a suggestion to check the name or open the correct file. Do not guess.
- **Module with >200 theorems**: The tool handles batching internally. Present a summary rather than listing every theorem — focus on flagged ones.
- **Axioms from plugins or extraction**: Note these as "generated" if identifiable. They are usually intentional.
- **Missing session**: If the user doesn't specify a file and the theorem name is ambiguous, ask for clarification rather than guessing.

## Clean up

Call `close_proof_session` when finished, whether the audit succeeded or failed.

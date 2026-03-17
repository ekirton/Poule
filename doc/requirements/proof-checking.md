# Independent Proof Checking — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Coq's main compilation pipeline (`coqc`) type-checks proof scripts and produces compiled `.vo` files. The system trusts this pipeline end-to-end — if `coqc` accepts a proof, it is considered valid. But the type checker is a large, complex piece of software, and kernel bugs have occurred in practice. For high-assurance formalization work — certified compilers, cryptographic protocol proofs, safety-critical systems — a single point of trust is insufficient.

`coqchk` is Coq's independent proof checker. It re-verifies compiled `.vo` files against a minimal, standalone kernel implementation without trusting the main compiler pipeline. This provides defense in depth: even if a bug in `coqc` silently accepts an invalid proof, `coqchk` will catch the inconsistency. Running `coqchk` is considered best practice for any project where proof validity is critical, yet it remains underused because users must invoke it manually, understand its command-line interface, and interpret its output.

This initiative wraps `coqchk` as MCP-accessible functionality so that Claude can invoke independent proof checking on behalf of the user. The wrapper submits `.vo` files to `coqchk`, parses its output, and presents results in clear natural language. When checking succeeds, the user gains independent confirmation that their proofs are kernel-valid. When checking fails, Claude explains the inconsistency and its implications.

Because Poule already exposes 22 MCP tools and research suggests accuracy degrades past 20–30 tools, this initiative should expose proof checking as a mode of existing tools or as a minimal addition to the tool surface, rather than proliferating new top-level tools.

**Success metrics:**
- 100% of `coqchk` invocations through MCP return a result (success or structured failure) within a reasonable timeout
- When `coqchk` reports an inconsistency, the MCP response includes a clear, natural-language explanation of what failed and why it matters
- Users can invoke independent proof checking without any knowledge of `coqchk` command-line syntax or options
- Time from user intent ("check this proof independently") to result is < 2x the raw `coqchk` execution time (i.e., MCP overhead is minimal)
- ≥ 90% of users in high-assurance contexts report that independent checking increases their confidence in proof validity

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq developers working on high-assurance projects | Independent validation that compiled proofs are kernel-correct, without learning `coqchk` syntax | Primary |
| Formalization teams with CI pipelines | Automated proof re-checking as a CI gate to catch regressions and kernel-level inconsistencies before merging | Primary |
| Coq newcomers using Claude Code | Confidence that their proofs are truly valid, with clear explanations when the checker finds problems | Secondary |
| Security auditors reviewing formal proofs | An independent verification step that does not trust the main compiler, with auditable output | Secondary |

---

## 3. Competitive Context

Cross-references:
- [Coq ecosystem tooling survey](../background/coq-ecosystem-tooling.md)

**Lean ecosystem (comparative baseline):**
- Lean 4 uses a single type-checking pipeline with no equivalent of `coqchk`. Independent re-checking of compiled artifacts is not a standard practice in the Lean ecosystem.
- Some Lean projects export proofs to external verifiers, but there is no built-in independent checker analogous to `coqchk`.

**Coq ecosystem (current state):**
- `coqchk` ships with Coq and has been available for many years. It is a mature, well-tested tool that re-checks `.vo` files against a small, trusted kernel.
- Despite its value, `coqchk` is rarely integrated into everyday workflows. Most users run it only before major releases or audits, if at all.
- No existing tool wraps `coqchk` for LLM-driven invocation or interprets its output in natural language.

**Key insight:** `coqchk` already exists and is reliable. The gap is accessibility — making it easy to invoke, integrating it into development workflows, and explaining its results to users who may not understand kernel-level error messages. This is a high-value, low-effort opportunity.

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| RC-P0-1 | Check a single compiled `.vo` file using `coqchk` and return the result (success or failure with diagnostics) |
| RC-P0-2 | Check all compiled `.vo` files in a Coq project by discovering them from the project structure and invoking `coqchk` across the dependency graph |
| RC-P0-3 | When `coqchk` reports an inconsistency, return a structured diagnostic that includes the module name, the nature of the inconsistency, and a natural-language explanation |
| RC-P0-4 | Support a configurable timeout for `coqchk` invocations, with a sensible default |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| RC-P1-1 | Provide a summary report when checking multiple files: total files checked, files passed, files failed, with per-file status |
| RC-P1-2 | Detect when `.vo` files are stale (older than their corresponding `.v` source files) and warn the user before checking |
| RC-P1-3 | Support passing include paths and logical path mappings to `coqchk` so that projects with non-trivial directory layouts are handled correctly |
| RC-P1-4 | Produce output suitable for CI integration: structured exit codes, machine-readable result format, and a human-readable summary |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| RC-P2-1 | After a failed check, suggest corrective actions (e.g., recompile the file, check dependencies first, investigate specific axioms) |
| RC-P2-2 | Track checking history so the user can see which files were last checked and when |
| RC-P2-3 | Support checking only files that have changed since the last successful check, to minimize re-checking time on large projects |

---

## 5. Scope Boundaries

**In scope:**
- MCP wrapper around `coqchk` for single-file and project-wide independent proof checking
- Discovery of `.vo` files from Coq project structure
- Result parsing and natural-language explanation of checker output
- Timeout configuration
- Batch checking with summary reporting
- CI-friendly output format

**Out of scope:**
- Installation or management of Coq or `coqchk` (assumed to be available in the user's environment)
- Modifications to `coqchk` itself
- Proof repair or automatic fixing of inconsistencies found by the checker
- Compilation of `.v` files to `.vo` (that is the responsibility of the build system)
- IDE plugin development
- Proof visualization (covered by Proof Visualization Widgets initiative)

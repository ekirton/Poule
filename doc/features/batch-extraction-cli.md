# Batch Extraction CLI

A CLI command that processes one or more Coq project directories and extracts proof traces for all provable theorems, with deterministic output and graceful degradation on failure.

**Stories**: [Epic 1: Project-Level Extraction](../requirements/stories/training-data-extraction.md#epic-1-project-level-extraction), [Epic 4: Determinism and Reproducibility](../requirements/stories/training-data-extraction.md#epic-4-determinism-and-reproducibility), [Epic 5: Graceful Degradation and Reporting](../requirements/stories/training-data-extraction.md#epic-5-graceful-degradation-and-reporting)

---

## Problem

AI researchers who want to train models on Coq proof data must currently write custom extraction scripts per project. There is no standard tool that walks a Coq project, extracts proof traces with premise annotations, and handles the inevitable failures that occur at scale (timeouts, unsupported tactics, backend crashes). Each research group solves this independently, producing incompatible datasets that cannot be compared or reproduced.

## Solution

A CLI command that accepts one or more Coq project directories and produces a structured dataset of proof traces. The command:

- Processes each project's .v files, extracting proof traces for every provable theorem
- Produces one structured record per proof in a streaming output format
- Skips failed proofs with a structured error record and continues extraction
- Reports summary statistics after each run (total found, extracted, failed, skipped, per-file breakdown)
- Produces byte-identical output for identical inputs across runs

For multi-project campaigns, the output includes project-level metadata so records can be attributed to their source project.

## Design Rationale

### Why CLI-first, not MCP

Batch extraction is a pipeline operation — process a directory, emit a dataset, exit. There is no conversational state, no interactive feedback loop, and no benefit from LLM mediation. A CLI command integrates naturally with shell scripts, CI pipelines, and job schedulers. MCP exposure would add protocol overhead without value.

### Why graceful degradation is P0

At extraction scale (tens of thousands of proofs across multiple projects), some proofs will fail — timeouts, unsupported tactic extensions, version-specific kernel behavior. If one failure aborts the entire run, extraction becomes impractical. CoqGym handled this with per-proof isolation; LeanDojo does the same. Structured error records let researchers analyze failure patterns and improve coverage iteratively.

### Why byte-identical determinism

ML experiment reproducibility requires exact dataset reproducibility. If extraction produces different output on repeated runs (due to nondeterministic ordering, floating timestamps in the output, or hash-map iteration order), researchers cannot verify that a dataset was produced from claimed inputs. Byte-identical output also enables simple integrity checking via checksums.

### Why multi-project campaigns in a single invocation

Researchers building large datasets (100K+ theorems) combine proofs from stdlib, MathComp, and additional projects. A single-invocation campaign avoids manual output merging, ensures consistent provenance metadata, and enables cross-project deduplication in later phases.

### Why no GPU, API keys, or network access

Extraction must run in constrained environments — university compute clusters, CI runners, air-gapped machines. The only external dependency is Coq itself and whatever Coq needs to build the project (typically opam packages). This constraint ensures the tool is accessible to any researcher with a Coq installation.

## Scope Boundaries

The batch extraction CLI provides:

- Project-level extraction across one or more directories
- Deterministic, reproducible output
- Graceful skip-and-continue on per-proof failures
- Summary statistics with per-file and per-project breakdowns

It does **not** provide:

- Interactive proof exploration (that is MCP-mediated, Phase 2)
- Single-proof extraction (use Phase 2's `replay-proof` CLI)
- Dataset post-processing (quality reports, benchmarks, export — separate features)
- Real-time extraction during editing

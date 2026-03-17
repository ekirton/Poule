# Proof Trace Serialization

Version-stable JSON serialization of proof traces and proof state diffs, enabling reliable downstream consumption across tool versions.

**Stories**: [Epic 5: Proof Trace Serialization](../requirements/stories/proof-interaction-protocol.md#epic-5-proof-trace-serialization)

---

## Problem

Proof traces are the primary data product of the Proof Interaction Protocol. Downstream tools — ML training pipelines, analysis scripts, benchmark generators — must parse these traces reliably. If the serialization format changes silently between tool versions, downstream tools break without warning. If the format is non-deterministic, the same proof produces different output on each extraction, making caching and deduplication impossible.

## Solution

All proof trace output uses a JSON format with two guarantees:

1. **Version-stable schema** — every serialized trace includes a top-level schema version field. Downstream tools can check this field to detect incompatible format changes.
2. **Deterministic output** — identical input produces identical output. The same proof, extracted by the same tool version, always yields byte-identical JSON.

## Schema Versioning

The schema version is a field in the top-level JSON object of every trace output. It identifies the structure of the data — field names, nesting, types, and semantics.

When the schema changes in a backward-incompatible way, the version is incremented. Downstream tools that encounter an unexpected version can fail fast with a clear error rather than silently misinterpreting data.

This follows the same principle as the [index schema version](library-indexing.md#index-versioning) used for the search database — derived artifacts carry their format version so consumers can detect incompatibility.

## Proof State Diff

Beyond full state snapshots, the protocol supports computing a diff between consecutive proof states. A diff shows:

- Goals added (new subgoals created by a tactic)
- Goals removed (subgoals closed by a tactic)
- Goals changed (same goal index, modified type)
- Hypotheses added, removed, or changed

Diffs are useful for understanding what a tactic *did* — a full state snapshot shows the result, but a diff highlights the delta. For ML applications, diffs may provide a more informative training signal than raw states, since they capture the tactic's effect directly.

## Design Rationale

### Why JSON rather than a binary format

JSON is human-readable, universally parseable, and trivially diffable with standard tools. The traces are not large enough to benefit from binary compression — a typical proof trace is kilobytes, not megabytes. Optimizing for developer ergonomics and tooling compatibility outweighs the modest size savings of a binary format.

### Why deterministic serialization matters

Non-deterministic output (e.g., hash-map iteration order, floating-point formatting) makes it impossible to cache traces, detect duplicates, or verify that a re-extraction produces the same data. Determinism is a correctness property for any data pipeline that depends on stable identifiers or content hashing.

### Why diff is P1 rather than P0

Full proof states are sufficient for all training data use cases — diffs are a convenience that can be computed client-side from consecutive states. Promoting diff to P1 reflects its value for tool builders who want efficient UI updates (show only what changed) without burdening the P0 deliverable.

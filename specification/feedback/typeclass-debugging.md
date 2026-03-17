# Specification Feedback: Typeclass Debugging

**Source:** [specification/typeclass-debugging.md](../typeclass-debugging.md)
**Date:** 2026-03-17
**Reviewer:** TDD test authoring

---

## Issue 1: Ambiguous classification authority in explain_failure

**Severity:** medium
**Location:** Section 4.4 (Failure Explanation), Section 5 (ResolutionTrace data model)

**Problem:** The `ResolutionTrace` data model (Section 5) includes a `failure_mode` field that is set on the trace itself. Section 4.4 specifies that `explain_failure(resolution_trace)` classifies the failure into one of three modes based on the trace structure (zero children, unification errors, depth-limit nodes). It is unclear whether `explain_failure` should use `trace.failure_mode` as a hint or independently derive the classification from the tree structure. The `failure_mode` field on `ResolutionTrace` appears to be set during trace construction, but `explain_failure` is described as performing its own classification -- these could disagree.

**Impact:** Implementers must decide whether `explain_failure` trusts `trace.failure_mode` or re-derives it. If the two sources disagree, behavior is undefined. Tests cannot unambiguously assert which source of truth prevails.

**Suggested resolution:** Clarify whether `explain_failure` uses `trace.failure_mode` as the authoritative classification or independently classifies from tree structure. If independent, specify that `trace.failure_mode` is informational and `explain_failure` may override it.

---

## Issue 2: No-instance vs. unclassified distinction for empty root_nodes

**Severity:** low
**Location:** Section 4.4 (Failure Explanation, "No Matching Instance" and "Fallback")

**Problem:** The "No Matching Instance" mode is defined as: "When a root node or sub-goal node has zero children." The "Fallback" mode is defined as: "When the trace does not match any of the three modes (empty or malformed)." A trace with an empty `root_nodes` list has no root nodes at all -- it is unclear whether this is "a root node with zero children" (triggering `no_instance`) or "empty" (triggering `unclassified`). The spec example for `no_instance` shows `root_nodes` as empty in Section 9, but the behavioral text in Section 4.4 says "a root node ... has zero children" which implies a root node must exist.

**Impact:** Test assertions for empty `root_nodes` traces cannot be written deterministically. The boundary between `no_instance` and `unclassified` is ambiguous for this edge case.

**Suggested resolution:** Specify that an empty `root_nodes` list (no root node exists) is classified as `no_instance` when `trace.failure_mode == "no_instance"`, and `unclassified` otherwise. Alternatively, require that trace construction always produces at least one root node for a valid typeclass goal.

---

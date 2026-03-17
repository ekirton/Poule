# Specification Feedback: Hammer Automation

**Source:** [specification/hammer-automation.md](../hammer-automation.md)
**Date:** 2026-03-17
**Reviewer:** TDD test author

---

## Issue 1: Ambiguous return type for interpret_result

**Severity:** medium
**Location:** Section 4.7 (Result Interpreter) vs Section 10 (Language-Specific Notes)

**Problem:** Section 10 declares `interpret_result` as a pure function with signature `def interpret_result(coq_output, proof_state) -> HammerResult`. However, Section 4.7 describes the function as returning a "classified result" per a mapping table that yields only a classification string (`success`, `timeout`, `no_proof_found`, `reconstruction_failed`, `tactic_error`) plus optional `partial_progress` text. A `HammerResult` contains additional fields (`proof_script`, `atp_proof`, `strategy_used`, `diagnostics`, `wall_time_ms`) that `interpret_result` cannot populate from its inputs alone (it has no strategy name, no wall-clock timer, no diagnostics list).

**Impact:** Implementers must choose between returning a partial `HammerResult` (with nulls for fields the interpreter cannot know) or returning a smaller classification type that the caller assembles into a `HammerResult`. Test assertions depend on this choice.

**Suggested resolution:** Define a separate `ClassifiedOutput` type with fields `classification`, `detail`, and `partial_progress`, and have `interpret_result` return that. The caller (`execute_hammer`) then assembles the full `HammerResult`. Alternatively, clarify in Section 4.7 that `interpret_result` returns a partial `HammerResult` with only the classification-relevant fields populated.

---

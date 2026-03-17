# Specification Feedback: Build System Integration

**Source:** [specification/build-system-integration.md](../build-system-integration.md)
**Date:** 2026-03-17
**Reviewer:** TDD test author

---

## Issue 1: parse_build_errors missing from Section 10 entry points

**Severity:** low
**Location:** Section 10 (Language-Specific Notes), entry points list

**Problem:** Section 4.7 defines `parse_build_errors(stdout, stderr, build_system)` as a public function with full behavioral specification, but Section 10 does not list it among the entry points. All other functions specified in Section 4 have corresponding entries in Section 10.

**Impact:** Implementers may omit `parse_build_errors` as a public API, or may be uncertain about its intended import path within `src/poule/build/`.

**Suggested resolution:** Add `def parse_build_errors(stdout: str, stderr: str, build_system: BuildSystem) -> list[BuildError]` to the Section 10 entry points list.

---

## Issue 2: update_coq_project missing from Section 10 entry points

**Severity:** low
**Location:** Section 10 (Language-Specific Notes), entry points list

**Problem:** Section 4.2 defines `update_coq_project(project_dir)` with REQUIRES/ENSURES contracts, but Section 10 does not list it among the entry points.

**Impact:** Same as Issue 1 -- implementers may omit or misplace the function.

**Suggested resolution:** Add `def update_coq_project(project_dir: Path) -> Path` to the Section 10 entry points list.

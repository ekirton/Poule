# Specification Feedback: Code Extraction Management

**Source:** [specification/code-extraction-management.md](../code-extraction-management.md)
**Date:** 2026-03-17
**Reviewer:** TDD test author

---

## Issue 1: ExtractionError name collision with existing types

**Severity:** high
**Location:** Section 5, Data Model — ExtractionError

**Problem:** The specification defines an `ExtractionError` dataclass with fields `definition_name`, `language`, `category`, `raw_error`, `explanation`, `suggestions`. However, two existing types already use the name `ExtractionError`:

1. `src/poule/extraction/types.py` defines `ExtractionError` as a frozen dataclass with fields `schema_version`, `record_type`, `theorem_name`, `source_file`, `project_id`, `error_kind`, `error_message` — used for training data extraction pipeline errors.
2. `src/poule/extraction/errors.py` defines `ExtractionError` as an exception base class for extraction pipeline errors.

Both existing types serve the training data extraction pipeline, not the code extraction management handler described in this specification. Using the same name `ExtractionError` for the code extraction management data model creates an import collision within the `poule.extraction` package.

**Impact:** Implementers cannot place the spec's `ExtractionError` in `src/poule/extraction/` (as Section 10 directs) without shadowing or conflicting with the existing types. Tests must use a disambiguated name (e.g., `CodeExtractionError`) to avoid import ambiguity. The implementation module path is unclear.

**Suggested resolution:** Rename the code extraction management error type to `CodeExtractionError` in the specification, or specify a distinct module path (e.g., `poule.extraction.code_types`) that avoids collision. Alternatively, clarify in Section 10 that the new types should use a submodule that does not conflict with existing extraction pipeline types.

---

## Issue 2: Spec says ExtractionHandler class but extract_code signature takes session_manager as first argument

**Severity:** low
**Location:** Section 10, Language-Specific Notes

**Problem:** Section 10 states "The `ExtractionHandler` class encapsulates command construction, result parsing, error classification, and file writing." However, the entry point signature is defined as a standalone async function: `async def extract_code(session_manager, session_id, ...)`. The `build_command` is also described as a standalone pure function. It is ambiguous whether `extract_code` and `build_command` are methods on `ExtractionHandler` or module-level functions, and whether `ExtractionHandler` is instantiated with a session_manager or receives it per-call.

**Impact:** Implementers must make a judgment call about whether to use a class with methods or module-level functions.

**Suggested resolution:** Clarify whether `extract_code` is a method on `ExtractionHandler` (and if so, specify the constructor signature) or a module-level function (and if so, remove the `ExtractionHandler` class reference or describe it as an internal implementation detail).

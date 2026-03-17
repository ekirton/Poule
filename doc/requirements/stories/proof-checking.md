# User Stories: Independent Proof Checking

Derived from [doc/requirements/proof-checking.md](../proof-checking.md).

---

## Epic 1: Single-File Proof Checking

### 1.1 Check a Single Compiled File

**As a** Coq developer using Claude Code,
**I want to** ask Claude to independently verify a single compiled `.vo` file using `coqchk`,
**so that** I can confirm that a specific proof is kernel-valid without trusting the main compiler pipeline.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a compiled `.vo` file WHEN independent checking is invoked for that file THEN `coqchk` is executed against the file and the result (pass or fail) is returned
- GIVEN a `.vo` file that passes `coqchk` WHEN the result is returned THEN it confirms that the proofs in the module are independently verified as kernel-valid
- GIVEN a `.vo` file path that does not exist WHEN checking is invoked THEN a clear error is returned indicating the file was not found

**Traces to:** RC-P0-1

### 1.2 Interpret Checker Output

**As a** Coq developer who is not an expert in Coq internals,
**I want** Claude to explain `coqchk` output in natural language,
**so that** I understand what the checker verified and can act on any problems without reading raw error messages.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a successful `coqchk` run WHEN the result is presented THEN it includes a plain-language confirmation of what was verified (e.g., which module, how many definitions checked)
- GIVEN a `coqchk` failure WHEN the result is presented THEN it includes the module name, the nature of the inconsistency, and a plain-language explanation of what it means and why it matters
- GIVEN a `coqchk` failure involving an axiom inconsistency WHEN the result is presented THEN the explanation distinguishes between an axiom mismatch and a proof-level error

**Traces to:** RC-P0-3

---

## Epic 2: Project-Wide Proof Checking

### 2.1 Check an Entire Project

**As a** formalization developer,
**I want to** ask Claude to independently check all compiled `.vo` files in my Coq project,
**so that** I can verify the entire proof development in one step rather than checking files individually.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project directory containing compiled `.vo` files WHEN project-wide checking is invoked THEN `coqchk` is executed across all `.vo` files respecting the dependency graph
- GIVEN a project with a `_CoqProject` file WHEN project-wide checking is invoked THEN include paths and logical path mappings are derived from the project configuration
- GIVEN a project-wide check WHEN it completes THEN every `.vo` file in the project has been checked

**Traces to:** RC-P0-2, RC-P1-3

### 2.2 Batch Checking with Summary Report

**As a** formalization team lead,
**I want** a summary report after checking multiple files that shows total files checked, passed, and failed with per-file status,
**so that** I can quickly assess the overall health of the proof development.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project-wide check that completes WHEN the summary is returned THEN it includes the total number of files checked, the number that passed, and the number that failed
- GIVEN a project-wide check with failures WHEN the summary is returned THEN each failed file is listed with its specific failure reason
- GIVEN a project-wide check where all files pass WHEN the summary is returned THEN it confirms that the entire project is independently verified

**Traces to:** RC-P1-1

---

## Epic 3: Failure Handling and Recovery

### 3.1 Handle Checker Failures

**As a** Coq developer whose proof fails independent checking,
**I want** Claude to explain why the check failed and suggest what to do next,
**so that** I can resolve the problem without deep knowledge of Coq kernel internals.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `coqchk` run that reports an inconsistency WHEN the failure is presented THEN the response includes the specific module and definition where the inconsistency was detected
- GIVEN a `coqchk` failure due to a missing dependency WHEN the failure is presented THEN the response identifies the missing dependency and suggests compiling or checking it first
- GIVEN a `coqchk` timeout WHEN the failure is presented THEN the response indicates the timeout was reached and suggests increasing the timeout or checking fewer files

**Traces to:** RC-P0-3, RC-P0-4, RC-P2-1

### 3.2 Detect Stale Compiled Files

**As a** Coq developer who has edited source files since last compilation,
**I want** the checker to warn me when `.vo` files are older than their corresponding `.v` source files,
**so that** I do not waste time checking outdated artifacts or draw false conclusions from stale results.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `.vo` file whose modification time is older than its corresponding `.v` file WHEN checking is invoked THEN a warning is returned indicating the compiled file may be stale
- GIVEN stale files detected during a project-wide check WHEN the summary is returned THEN the stale files are listed separately from pass/fail results
- GIVEN a stale file warning WHEN it is presented THEN the response suggests recompiling the source file before checking

**Traces to:** RC-P1-2

---

## Epic 4: CI Integration

### 4.1 CI-Friendly Output

**As a** formalization team integrating proof checking into CI,
**I want** the checking results to include structured exit codes and a machine-readable format alongside the human-readable summary,
**so that** CI pipelines can gate merges on independent proof validity.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a project-wide check invoked in a CI context WHEN it completes THEN the result includes a structured JSON payload with per-file status, overall pass/fail, and timing information
- GIVEN a project-wide check where any file fails WHEN the result is inspected programmatically THEN the overall status is "fail" and the failing files are enumerable
- GIVEN a project-wide check where all files pass WHEN the result is inspected programmatically THEN the overall status is "pass"

**Traces to:** RC-P1-4

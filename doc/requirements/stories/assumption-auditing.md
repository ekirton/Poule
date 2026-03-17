# User Stories: Assumption Auditing

Derived from [doc/requirements/assumption-auditing.md](../assumption-auditing.md).

---

## Epic 1: Single-Theorem Assumption Auditing

### 1.1 Check Assumptions of a Named Theorem

**As a** Coq formalization developer using Claude Code,
**I want to** ask Claude what axioms a specific theorem depends on,
**so that** I can verify that my theorem rests on acceptable foundations before relying on it.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a compiled Coq library containing theorem `T` WHEN assumption auditing is invoked for `T` THEN it returns the complete list of axioms and opaque dependencies that `T` relies on
- GIVEN a theorem with no axiom dependencies beyond Coq's core WHEN assumption auditing is invoked THEN it reports that the theorem is closed (axiom-free)
- GIVEN a theorem that depends on `Classical_Prop.classic` WHEN assumption auditing is invoked THEN `Classic` appears in the results with its type

**Traces to:** R-P0-1, R-P0-2, R-P0-6

### 1.2 Classify Axiom Types

**As a** Coq formalization developer,
**I want** each reported axiom to be classified by category and accompanied by a plain-language explanation,
**so that** I can quickly understand what each axiom means without looking it up manually.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a theorem that depends on `Coq.Logic.FunctionalExtensionality.functional_extensionality_dep` WHEN assumption auditing is invoked THEN the axiom is classified under the "extensionality" category
- GIVEN a theorem that depends on `Classical_Prop.classic` WHEN assumption auditing is invoked THEN the axiom is classified under the "classical logic" category
- GIVEN a theorem that depends on a user-defined axiom not in the standard library WHEN assumption auditing is invoked THEN the axiom is classified as "custom/user-defined"
- GIVEN any classified axiom WHEN the result is inspected THEN it includes a short plain-language explanation of what the axiom asserts and its common implications

**Traces to:** R-P0-3, R-P0-4

### 1.3 Assumption Auditing MCP Tool

**As a** Coq developer using Claude Code,
**I want** assumption auditing exposed as an MCP tool,
**so that** Claude can invoke it during our conversational workflow when I ask about a theorem's foundations.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a running MCP server WHEN its tool list is inspected THEN an assumption auditing tool is present with a documented schema
- GIVEN the assumption auditing MCP tool WHEN it is invoked with a fully qualified theorem name THEN it returns the classified assumption list
- GIVEN the assumption auditing MCP tool WHEN it is invoked with an identifier that does not exist in the loaded environment THEN it returns a clear error message

**Traces to:** R-P0-5

---

## Epic 2: Batch Auditing

### 2.1 Batch Audit of a Module

**As a** Coq library maintainer,
**I want to** audit all theorems in a module at once,
**so that** I can get a complete picture of the axiom footprint of my library without checking theorems one by one.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a compiled Coq module `M` containing 50 theorems WHEN batch auditing is invoked for `M` THEN it returns the assumption list for every theorem in the module
- GIVEN a batch audit result WHEN it is inspected THEN it includes a summary showing which axioms appear, how many theorems depend on each axiom, and which theorems are axiom-free
- GIVEN a module with up to 200 theorems WHEN batch auditing is invoked THEN it completes within 30 seconds

**Traces to:** R-P1-1, R-P1-5

### 2.2 Detect Unintended Axiom Use

**As a** developer maintaining a constructive Coq development,
**I want** the batch audit to flag any theorem that depends on classical axioms,
**so that** I can catch accidental classical dependencies before they compromise the constructive nature of my project.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a module where all theorems are intended to be constructive WHEN batch auditing is invoked THEN any theorem depending on classical logic, choice, or proof irrelevance axioms is explicitly flagged
- GIVEN a flagged theorem WHEN the flag is inspected THEN it identifies the specific axiom and the category that triggered the flag
- GIVEN a module where no theorem uses classical axioms WHEN batch auditing is invoked THEN the summary confirms that the module is fully constructive

**Traces to:** R-P1-2

---

## Epic 3: Assumption Comparison

### 3.1 Compare Assumption Profiles Between Theorems

**As a** Coq developer choosing between alternative formulations of a result,
**I want to** compare the axiom dependencies of two or more theorems side by side,
**so that** I can select the formulation with the weakest assumptions.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN two theorems `A` and `B` WHEN assumption comparison is invoked THEN it returns the axioms unique to `A`, the axioms unique to `B`, and the axioms shared by both
- GIVEN three or more theorems WHEN assumption comparison is invoked THEN it returns a matrix showing which axioms each theorem depends on
- GIVEN two theorems where one has strictly fewer axiom dependencies than the other WHEN comparison is invoked THEN the result clearly indicates which theorem has the weaker assumption set

**Traces to:** R-P1-3, R-P1-5

---

## Epic 4: Index-Based Auditing

### 4.1 Audit from Pre-Built Index

**As a** Coq developer who does not have a live Coq session running,
**I want** assumption auditing to work from pre-compiled library files and indexes where possible,
**so that** I can check axiom dependencies without launching Coq interactively.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a compiled `.vo` file for a Coq library WHEN assumption auditing is invoked for a theorem in that library THEN it returns results without requiring an active `coqtop` session, if the necessary information is available in the compiled files
- GIVEN a library that has been indexed by the semantic lemma search infrastructure WHEN assumption auditing is invoked THEN it leverages the existing index to resolve identifiers
- GIVEN a theorem whose assumptions cannot be determined from compiled files alone WHEN assumption auditing is invoked THEN it falls back to a live Coq session or returns a clear message explaining the limitation

**Traces to:** R-P1-4

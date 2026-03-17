# User Stories: Code Extraction Management

Derived from [doc/requirements/code-extraction.md](../code-extraction.md).

---

## Epic 1: Basic Extraction

### 1.1 Extract a Single Definition

**As a** verified software developer,
**I want to** extract a single named Coq definition to a target language and see the resulting code,
**so that** I can obtain executable code from my verified specification without manually writing extraction commands.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq environment with a defined term `my_function` WHEN I request extraction of `my_function` to OCaml THEN the tool returns valid OCaml code corresponding to that definition
- GIVEN a Coq environment with a defined term `my_function` WHEN I request extraction to Haskell THEN the tool returns valid Haskell code corresponding to that definition
- GIVEN a Coq environment with a defined term `my_function` WHEN I request extraction to Scheme THEN the tool returns valid Scheme code corresponding to that definition
- GIVEN a definition name that does not exist in the current environment WHEN I request extraction THEN the tool returns an error identifying the unknown name

**Traces to:** R-CE-P0-1, R-CE-P0-3

### 1.2 Recursive Extraction

**As a** verified software developer,
**I want to** recursively extract a Coq definition along with all its transitive dependencies,
**so that** I get a self-contained extracted module that compiles independently in the target language.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a definition `serialize` that depends on `encode` and `to_bytes` WHEN I request recursive extraction of `serialize` to OCaml THEN the tool returns extracted code for `serialize`, `encode`, and `to_bytes`
- GIVEN a recursive extraction request WHEN the result is returned THEN all transitive dependencies are included in the output
- GIVEN a definition with no dependencies beyond Coq's built-in types WHEN I request recursive extraction THEN the output contains only the extracted definition itself

**Traces to:** R-CE-P0-2, R-CE-P0-3

---

## Epic 2: Target Language Selection

### 2.1 Choose Target Language

**As a** verified software developer,
**I want to** specify which target language (OCaml, Haskell, or Scheme) to extract to,
**so that** I can produce code in the language that matches my project's technology stack.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid extraction request WHEN I specify OCaml as the target THEN the tool produces OCaml syntax
- GIVEN a valid extraction request WHEN I specify Haskell as the target THEN the tool produces Haskell syntax
- GIVEN a valid extraction request WHEN I specify Scheme as the target THEN the tool produces Scheme syntax
- GIVEN a valid extraction request WHEN I specify an unsupported language (e.g., Python) THEN the tool returns an error listing the supported languages

**Traces to:** R-CE-P0-3

---

## Epic 3: Extraction Failure Handling

### 3.1 Explain Extraction Failures

**As a** Coq learner,
**I want to** receive a plain-language explanation when extraction fails, along with suggested fixes,
**so that** I can resolve extraction errors without deep knowledge of Coq's extraction internals.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a definition that references an opaque term WHEN extraction fails THEN the tool explains that the term is opaque and suggests using `Transparent` or providing an extraction directive
- GIVEN a definition that depends on an axiom without a realizer WHEN extraction fails THEN the tool identifies the axiom and suggests providing an `Extract Constant` directive
- GIVEN a definition with a universe inconsistency during extraction WHEN extraction fails THEN the tool explains the universe issue and suggests potential restructurings
- GIVEN any extraction failure WHEN the error is returned THEN the response includes both the raw Coq error and a plain-language explanation with at least one suggested fix

**Traces to:** R-CE-P0-4

---

## Epic 4: Extraction Preview

### 4.1 Preview Extracted Code Before Writing

**As a** verified software developer,
**I want to** preview the extracted code in the tool response without it being written to a file,
**so that** I can review the output and decide whether to save it, adjust extraction options, or try a different target language.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a successful extraction request WHEN the result is returned THEN the extracted code is displayed in the response and no file is written to disk
- GIVEN a previewed extraction WHEN I am satisfied with the output THEN I can request the tool to write the code to a specified file path
- GIVEN a previewed extraction WHEN I am not satisfied THEN I can request extraction again with different options without any file having been created

**Traces to:** R-CE-P0-5, R-CE-P1-2

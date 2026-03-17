# User Stories: Literate Documentation Generation

Derived from [doc/requirements/literate-documentation.md](../literate-documentation.md).

---

## Epic 1: Single-File Documentation Generation

### 1.1 Generate Interactive Documentation for a Coq Source File

**As an** educator teaching formal verification,
**I want to** generate interactive HTML documentation from a `.v` file that shows proof states inline alongside the proof script,
**so that** I can provide students with a browsable document they can study without installing Coq.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `.v` file that compiles without errors WHEN the documentation generation MCP tool is called with the file path THEN it returns self-contained HTML with interactive proof state display for every Coq sentence
- GIVEN the generated HTML file WHEN it is opened in a modern browser with no additional setup THEN all proof states are accessible via hover or click interactions and all CSS/JavaScript is embedded
- GIVEN a `.v` file containing 3 theorem proofs and 5 definitions WHEN documentation is generated THEN all 3 proofs show inline proof states and all 5 definitions are included in the output

**Traces to:** R-LD-P0-1, R-LD-P0-2, R-LD-P0-6

### 1.2 Write Documentation Output to a Specified Path

**As a** Coq library author,
**I want to** specify where the generated HTML file is written,
**so that** I can place documentation directly into my project's doc directory for publication.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `.v` file and an output path WHEN the documentation tool is called with both parameters THEN the HTML file is written to the specified output path
- GIVEN an output path whose parent directory does not exist WHEN the tool is called THEN it returns an error indicating the directory does not exist, rather than silently failing

**Traces to:** R-LD-P0-6

---

## Epic 2: Proof-Scoped Documentation

### 2.1 Generate Documentation for a Specific Proof

**As a** proof reviewer,
**I want to** generate documentation scoped to a single named proof within a `.v` file,
**so that** I can read the proof under review with full proof state context without wading through the entire file.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `.v` file containing proofs for `lemma_A`, `theorem_B`, and `lemma_C` WHEN the proof-scoped documentation tool is called with the file path and the name `theorem_B` THEN the output contains interactive documentation for `theorem_B` and its immediately surrounding context (e.g., the statement and any local definitions it depends on)
- GIVEN a `.v` file and a proof name that does not exist in the file WHEN the tool is called THEN it returns an error listing the available proof names in the file
- GIVEN a proof that uses `Proof. ... Qed.` spanning 15 tactic steps WHEN proof-scoped documentation is generated THEN every tactic step shows its resulting proof state

**Traces to:** R-LD-P0-3

---

## Epic 3: Batch Documentation Generation

### 3.1 Generate Documentation for an Entire Project

**As a** Coq library maintainer,
**I want to** generate documentation for all `.v` files in my project directory,
**so that** I can publish browsable documentation for the entire library alongside a source release.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project directory containing 10 `.v` files across 3 subdirectories WHEN the batch documentation tool is called with the project root THEN HTML documentation is generated for all 10 files, preserving the directory structure in the output
- GIVEN batch-generated documentation WHEN a user opens any generated page THEN navigation links to other documented files in the project are present and functional
- GIVEN a batch run where 9 of 10 files compile successfully and 1 file has a compilation error THEN documentation is generated for the 9 successful files and the error for the failing file is reported without aborting the entire batch

**Traces to:** R-LD-P1-1, R-LD-P1-4

### 3.2 Generate an Index Page for Batch Output

**As a** Coq library maintainer,
**I want** batch documentation to include an index page listing all documented files,
**so that** readers have an entry point for browsing the project documentation.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN batch documentation generated for 10 files WHEN the index page is opened in a browser THEN it lists all 10 documented files with working links to each
- GIVEN that 1 of 10 files failed during batch generation WHEN the index page is rendered THEN the failing file is listed with a note indicating documentation was not generated, and the 9 successful files link correctly

**Traces to:** R-LD-P1-1, R-LD-P1-4

---

## Epic 4: Output Customization

### 4.1 Select Output Format

**As an** educator preparing materials for different contexts,
**I want to** choose between standalone HTML, embeddable HTML fragment, or LaTeX output,
**so that** I can integrate proof documentation into course websites, slide decks, or printed handouts.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a `.v` file WHEN the documentation tool is called with format set to "html" THEN the output is a complete standalone HTML page with embedded styles and scripts
- GIVEN a `.v` file WHEN the documentation tool is called with format set to "html-fragment" THEN the output is an HTML fragment without `<html>`, `<head>`, or `<body>` wrapper tags, suitable for embedding in an existing page
- GIVEN a `.v` file WHEN the documentation tool is called with format set to "latex" THEN the output is a LaTeX document using Alectryon's LaTeX backend

**Traces to:** R-LD-P1-2

### 4.2 Pass Custom Alectryon Flags

**As a** Coq library author with specific formatting preferences,
**I want to** pass custom Alectryon flags through the MCP tool,
**so that** I can control line wrapping thresholds, caching behavior, and other Alectryon options without workarounds.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN the flag `--long-line-threshold 80` passed to the documentation tool WHEN documentation is generated THEN Alectryon applies the 80-character line wrapping threshold to the output
- GIVEN the flag `--cache-directory /tmp/alectryon-cache` passed to the tool WHEN documentation is generated THEN Alectryon uses the specified cache directory for compilation artifacts

**Traces to:** R-LD-P1-3

---

## Epic 5: Error Handling and Dependency Detection

### 5.1 Report Missing Alectryon Installation

**As a** user who has not yet installed Alectryon,
**I want** the tool to tell me that Alectryon is not installed and how to install it,
**so that** I can resolve the issue without searching for installation instructions myself.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN that Alectryon is not installed or not on the system PATH WHEN any documentation generation MCP tool is called THEN it returns an error message stating that Alectryon was not found, along with installation instructions (e.g., `pip install alectryon`)
- GIVEN that Alectryon is installed but the version is older than the minimum supported version WHEN the tool is called THEN it returns a warning identifying the installed version and the minimum required version

**Traces to:** R-LD-P0-5

### 5.2 Report Coq Compilation Errors

**As a** formalization developer,
**I want** the tool to report Coq compilation errors with file location and Coq's error message,
**so that** I can fix the source file before regenerating documentation.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a `.v` file with a type error on line 42 WHEN the documentation tool is called THEN it returns an error that includes the line number (42), the Coq error message, and the fragment of source code where the error occurs
- GIVEN a `.v` file that requires a library not in the current load path WHEN the documentation tool is called THEN the error message includes Coq's "Cannot find a physical path" message and the name of the missing dependency

**Traces to:** R-LD-P0-4

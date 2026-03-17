# User Stories: Universe Constraint Inspection

Derived from [doc/requirements/universe-inspection.md](../universe-inspection.md).

---

## Epic 1: Universe Constraint Retrieval

### 1.1 View Universe Constraints of a Definition

**As a** library author working with universe-polymorphic code,
**I want to** view the universe constraints associated with a specific definition,
**so that** I can understand what universe relationships Coq inferred for my code.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a loaded Coq environment and a valid fully qualified name WHEN the universe-constraints tool is called with that name THEN it returns the universe variables and constraints associated with that definition in structured form
- GIVEN a name that does not exist in the current environment WHEN the universe-constraints tool is called THEN a structured error is returned indicating the name was not found
- GIVEN a definition with no universe constraints (e.g., a concrete, non-polymorphic definition at Set level) WHEN the universe-constraints tool is called THEN it returns an empty constraint set with an explanatory note

### 1.2 View the Full Universe Constraint Graph

**As an** advanced Coq user debugging a complex universe issue,
**I want to** retrieve the full universe constraint graph for the current environment,
**so that** I can inspect all active universe relationships.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a loaded Coq environment WHEN the universe-graph tool is called THEN it returns the complete set of universe variables and constraints in structured form
- GIVEN the returned constraint graph WHEN it is inspected THEN each constraint includes the two universe expressions and the relationship (less-than, less-than-or-equal, or equal)
- GIVEN a large constraint graph WHEN the tool is called THEN the response completes within 3 seconds for environments up to the size of the Coq standard library

### 1.3 View Universe-Annotated Terms

**As a** Coq developer trying to understand universe levels in a type,
**I want to** see a term printed with explicit universe annotations,
**so that** I can see which universe levels Coq assigned to each occurrence of Type or Sort.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid term or definition name WHEN the print-with-universes tool is called THEN it returns the term with universe level annotations on every Type and Sort occurrence
- GIVEN a term that involves universe polymorphism WHEN the annotated term is returned THEN each polymorphic universe variable is labeled consistently across the output

---

## Epic 2: Universe Inconsistency Diagnosis

### 2.1 Diagnose a Universe Inconsistency Error

**As a** Coq user who has encountered a `Universe inconsistency` error,
**I want to** submit the error message and receive an explanation of what caused it,
**so that** I can understand the conflict without manually tracing universe variables.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a universe inconsistency error message and the current Coq environment WHEN the diagnose-universe-error tool is called THEN it identifies the specific constraints that form the inconsistent cycle
- GIVEN the identified conflicting constraints WHEN the diagnosis is returned THEN each constraint is traced back to the definition or command that introduced it
- GIVEN a diagnosis WHEN it is presented THEN it includes a plain-language explanation of why the constraints are contradictory and at least one suggested resolution strategy
- GIVEN an error message that is not a universe inconsistency error WHEN the tool is called THEN a structured error is returned indicating the error type is not supported

### 2.2 Explain a Universe Inconsistency in Context

**As an** intermediate Coq user encountering a universe error for the first time,
**I want to** receive a contextual explanation that relates the error to my source code,
**so that** I can understand the problem without deep knowledge of Coq's universe system.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a universe inconsistency error and the source file where it occurred WHEN the explanation tool is called THEN the explanation references specific lines or definitions in the user's source code, not just abstract universe variable names
- GIVEN the explanation WHEN a user with intermediate Coq knowledge reads it THEN it describes what universe levels are, why the conflict arose, and what concrete change to the source code would resolve it

---

## Epic 3: Universe-Polymorphic Instantiation Inspection

### 3.1 View Universe-Polymorphic Instances

**As a** developer using universe-polymorphic libraries,
**I want to** see how a universe-polymorphic definition is instantiated at a specific use site,
**so that** I can verify that the universe levels are what I expect.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a universe-polymorphic definition and a use site (identified by definition name or location) WHEN the inspect-instantiation tool is called THEN it returns the concrete universe levels substituted for each polymorphic universe variable at that use site
- GIVEN a definition that is not universe-polymorphic WHEN the tool is called THEN a structured response is returned indicating the definition is monomorphic and has no universe parameters to instantiate

### 3.2 Compare Universe Levels Between Definitions

**As a** library author composing definitions across modules,
**I want to** compare the universe levels of two definitions,
**so that** I can understand why one cannot be used where the other is expected.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN two valid definition names WHEN the compare-universes tool is called THEN it returns the universe constraints of each definition and identifies any constraints that would be violated if one were substituted for the other
- GIVEN two definitions with compatible universe levels WHEN the comparison is returned THEN it confirms compatibility and shows the constraint alignment
- GIVEN two definitions with incompatible universe levels WHEN the comparison is returned THEN it identifies the specific constraint conflict and explains which definition's constraint is more restrictive

---

## Epic 4: Filtered Constraint Graph

### 4.1 Filter Universe Constraint Graph by Definition

**As an** advanced user debugging a specific universe issue,
**I want to** filter the constraint graph to show only constraints reachable from a given definition,
**so that** I can focus on the relevant subset without wading through thousands of unrelated constraints.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid definition name WHEN the filtered-universe-graph tool is called THEN it returns only the universe variables and constraints transitively reachable from that definition's universe variables
- GIVEN a definition with no universe variables WHEN the tool is called THEN it returns an empty graph with an explanatory note
- GIVEN a definition whose reachable subgraph contains N constraints WHEN the full graph contains M >> N constraints THEN the filtered result contains exactly N constraints

---

## Epic 5: Structured Output and MCP Integration

### 5.1 Structured Universe Constraint Output

**As a** tool builder integrating with the MCP server,
**I want** universe constraint data to be returned in a structured format,
**so that** Claude can reason over constraints programmatically rather than parsing free text.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN any universe inspection tool WHEN the response is returned THEN constraint data is structured with fields for universe variables, constraint expressions, relationship type, and source definition
- GIVEN structured constraint output WHEN it is serialized as JSON THEN it conforms to a declared schema
- GIVEN raw Coq output from `Print Universes` or `Set Printing Universes` WHEN it is processed by the tool THEN the structured output preserves all information present in the raw output without loss

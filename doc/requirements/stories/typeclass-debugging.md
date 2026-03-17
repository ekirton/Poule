# User Stories: Typeclass Instance Debugging

Derived from [doc/requirements/typeclass-debugging.md](../typeclass-debugging.md).

---

## Epic 1: Instance Inspection

### 1.1 List Instances of a Typeclass

**As a** Coq developer debugging a typeclass error,
**I want** Claude to list all registered instances of a given typeclass,
**so that** I can see what instances are available and identify whether the one I need is missing.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid typeclass name WHEN instance listing is invoked THEN it returns all registered instances including instance name, type signature, and defining module
- GIVEN a typeclass with no registered instances WHEN instance listing is invoked THEN it returns an empty list with a clear indication that no instances exist
- GIVEN a name that is not a typeclass WHEN instance listing is invoked THEN it returns an informative error indicating the name does not refer to a typeclass

**Traces to:** R-TC-P0-1

### 1.2 List All Typeclasses

**As a** Coq library author designing a typeclass hierarchy,
**I want** Claude to list all registered typeclasses in the current environment,
**so that** I can understand what typeclasses exist and how many instances each has.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq environment with loaded libraries WHEN typeclass listing is invoked THEN it returns all registered typeclasses with summary information
- GIVEN the typeclass list WHEN it is inspected THEN each entry includes at minimum the typeclass name and the number of registered instances

**Traces to:** R-TC-P1-4

---

## Epic 2: Resolution Tracing

### 2.1 Trace Resolution for a Goal

**As a** Coq developer encountering a typeclass resolution failure,
**I want** Claude to trace the resolution process for a specific goal and present a structured account of what happened,
**so that** I can understand which instances were tried and why resolution failed without manually parsing debug output.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a proof state with an unresolved typeclass goal WHEN resolution tracing is invoked THEN it returns a structured trace showing which instances were tried, in what order, and whether each succeeded or failed
- GIVEN a resolution trace WHEN it is inspected THEN each step includes the instance name, the goal it was applied to, and the outcome (success, unification failure, or sub-goal failure)
- GIVEN the raw output of `Set Typeclasses Debug` WHEN it is processed THEN it is parsed into a structured representation rather than returned as raw text

**Traces to:** R-TC-P0-2, R-TC-P0-5

### 2.2 Explain Resolution Failure

**As a** Coq developer who has received a typeclass error,
**I want** Claude to identify and explain the root cause of the resolution failure,
**so that** I know whether I am missing an instance, have a unification problem, or have exceeded the resolution depth.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a resolution failure caused by no matching instance WHEN the explanation is returned THEN it states that no instance was found and identifies the specific typeclass and type arguments that lack an instance
- GIVEN a resolution failure caused by unification failure against a specific instance WHEN the explanation is returned THEN it identifies the instance and explains which type arguments failed to unify
- GIVEN a resolution failure caused by exceeding the maximum resolution depth WHEN the explanation is returned THEN it states that depth was exceeded and shows the resolution path that led to the loop or deep chain

**Traces to:** R-TC-P0-3

### 2.3 Show Resolution Search Tree

**As a** Coq developer debugging a complex typeclass resolution,
**I want** Claude to show the full resolution search tree for a given goal,
**so that** I can see all branching points where multiple instances were candidates and understand the engine's choices.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a goal requiring typeclass resolution WHEN the search tree is requested THEN it returns a tree structure showing each resolution step, branching points, and outcomes
- GIVEN a branching point in the search tree WHEN it is inspected THEN it shows all candidate instances at that point and indicates which was selected and why alternatives were rejected
- GIVEN a search tree WHEN it is presented THEN the depth and branching structure are clearly communicated (e.g., via indentation or explicit parent-child relationships)

**Traces to:** R-TC-P1-1

---

## Epic 3: Instance Conflict Detection

### 3.1 Identify Ambiguous or Conflicting Instances

**As a** Coq library author adding a new instance,
**I want** Claude to identify cases where two or more instances match the same goal,
**so that** I can detect ambiguities and understand which instance wins and why.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a goal for which multiple instances match WHEN conflict detection is invoked THEN it identifies all matching instances and indicates which one resolution selects
- GIVEN conflicting instances WHEN the result is inspected THEN it explains the basis for selection (declaration order, priority hint, or specificity)
- GIVEN a single matching instance for a goal WHEN conflict detection is invoked THEN it confirms that resolution is unambiguous

**Traces to:** R-TC-P1-2

### 3.2 Explain Instance Selection for a Goal

**As a** Coq developer who is surprised by which instance was selected,
**I want** Claude to explain why a specific instance was or was not chosen for a given goal,
**so that** I can understand the resolution engine's decision and adjust my instances or priorities if needed.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a specific instance and a goal WHEN instance explanation is requested THEN it explains whether the instance matches the goal, and if so, with what unification
- GIVEN an instance that was not selected despite matching WHEN the explanation is returned THEN it identifies the instance that was selected instead and explains the priority or ordering reason
- GIVEN an instance that does not match the goal WHEN the explanation is returned THEN it identifies which type arguments or prerequisite constraints prevented matching

**Traces to:** R-TC-P1-3

---

## Epic 4: MCP Tool Integration

### 4.1 Typeclass Debugging MCP Tools

**As a** Coq developer using Claude Code,
**I want** typeclass debugging capabilities exposed as MCP tools,
**so that** Claude can invoke them during our conversational workflow without requiring me to run Coq commands manually.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a running MCP server WHEN its tool list is inspected THEN typeclass debugging tools are present with documented schemas
- GIVEN a typeclass debugging tool WHEN it is invoked with valid parameters THEN it returns structured results within 5 seconds for standard library-scale typeclass hierarchies
- GIVEN a typeclass debugging tool WHEN it is invoked with invalid parameters THEN it returns a clear error message indicating the problem

**Traces to:** R-TC-P0-4

---

## Epic 5: Resolution Fix Suggestions

### 5.1 Suggest Fixes for Resolution Failures

**As a** Coq developer who has identified a missing instance,
**I want** Claude to suggest how to fix the resolution failure,
**so that** I can resolve the error without searching documentation or source code for the correct instance to add or import.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a resolution failure caused by a missing instance WHEN a fix suggestion is requested THEN it suggests adding an instance declaration with the appropriate type signature
- GIVEN a resolution failure caused by a missing import WHEN a fix suggestion is requested THEN it identifies the module that provides the needed instance and suggests importing it
- GIVEN a resolution failure with no straightforward fix WHEN a fix suggestion is requested THEN it explains why no simple fix is available and describes what would be needed

**Traces to:** R-TC-P2-1

### 5.2 Detect Instance Priority Issues

**As a** Coq library author maintaining a typeclass hierarchy,
**I want** Claude to warn me when a newly added instance may shadow an existing one,
**so that** I can avoid introducing subtle breakage for downstream users.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a newly registered instance WHEN priority analysis is performed THEN it identifies any existing instances that the new instance would shadow for common goal patterns
- GIVEN a shadowing relationship WHEN it is reported THEN it includes the specific goal pattern affected and both the shadowing and shadowed instance names

**Traces to:** R-TC-P2-2

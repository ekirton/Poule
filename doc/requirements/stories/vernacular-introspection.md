# User Stories: Vernacular Introspection

Derived from [doc/requirements/vernacular-introspection.md](../vernacular-introspection.md).

---

## Epic 1: Definition Inspection

### 1.1 Print a Definition

**As a** Coq developer using Claude Code,
**I want to** ask Claude to show the full body of a Coq definition,
**so that** I can understand what a constant, inductive type, or fixpoint expands to without switching to a Coq toplevel.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid fully qualified name of a defined constant WHEN the introspection tool is called with command `Print` and that name THEN the response includes the complete definition body as Coq would display it
- GIVEN a valid name of an inductive type WHEN the introspection tool is called with command `Print` THEN the response includes the inductive definition with all constructors
- GIVEN a name that does not exist in the current environment WHEN the introspection tool is called with command `Print` THEN a structured error is returned indicating the name was not found

### 1.2 Print Assumptions

**As a** Coq developer reviewing a proof's foundations,
**I want to** see which axioms a definition depends on,
**so that** I can assess the trustworthiness of a result.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid name of a defined constant or theorem WHEN the introspection tool is called with command `Print` and the `assumptions` option THEN the response lists all axioms the definition transitively depends on
- GIVEN a definition with no axiom dependencies WHEN the command is executed THEN the response indicates the definition is axiom-free

---

## Epic 2: Type Checking

### 2.1 Check the Type of a Term

**As a** Coq developer using Claude Code,
**I want to** ask Claude to show the type of a Coq term or expression,
**so that** I can verify type signatures and understand what a term produces without manually running `Check`.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a well-typed Coq expression WHEN the introspection tool is called with command `Check` and that expression THEN the response includes the inferred type of the expression
- GIVEN a simple name of a lemma or constant WHEN the introspection tool is called with command `Check` THEN the response includes the type (statement) of that lemma or constant
- GIVEN an ill-typed expression WHEN the introspection tool is called with command `Check` THEN a structured error is returned including the Coq type error message

### 2.2 Check Type Inside a Proof

**As a** Coq developer in the middle of a proof,
**I want to** check the type of a term using hypotheses from the current proof context,
**so that** I can understand how local assumptions affect types.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active proof session with hypotheses in context WHEN the introspection tool is called with command `Check` and a term referencing a local hypothesis THEN the response includes the type of that term resolved against the proof context
- GIVEN an active proof session WHEN the introspection tool is called with command `Check` and a term that does not reference local hypotheses THEN the response includes the type resolved against the global environment as usual

---

## Epic 3: Metadata and Name Resolution

### 3.1 Show Metadata About a Name

**As a** Coq developer using Claude Code,
**I want to** ask Claude for metadata about a Coq name — its kind, defining module, and status,
**so that** I can orient myself in an unfamiliar codebase without manually running `About`.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid name WHEN the introspection tool is called with command `About` THEN the response includes the kind (e.g., Theorem, Definition, Inductive, Constructor), the defining module, and whether it is opaque or transparent
- GIVEN a name that does not exist in the current environment WHEN the introspection tool is called with command `About` THEN a structured error is returned indicating the name was not found

### 3.2 Locate a Fully Qualified Name

**As a** Coq developer using Claude Code,
**I want to** resolve a short or partial name to its fully qualified path,
**so that** I can disambiguate names and use the correct qualified reference.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a short name that resolves to a unique fully qualified path WHEN the introspection tool is called with command `Locate` THEN the response includes the fully qualified name and its kind
- GIVEN a short name that resolves to multiple qualified paths WHEN the introspection tool is called with command `Locate` THEN the response includes all matching qualified names and their kinds
- GIVEN a name that cannot be located WHEN the introspection tool is called with command `Locate` THEN a structured error is returned indicating the name was not found
- GIVEN a notation string WHEN the introspection tool is called with command `Locate` THEN the response includes the notation's defining scope and interpretation

### 3.3 Search by Pattern

**As a** Coq developer looking for relevant lemmas,
**I want to** search for names matching a type pattern or constraint,
**so that** I can discover lemmas without knowing their exact names.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid search pattern (e.g., a type fragment) WHEN the introspection tool is called with command `Search` and that pattern THEN the response includes a list of matching names with their types
- GIVEN a search pattern that matches no names WHEN the introspection tool is called with command `Search` THEN the response indicates no results were found
- GIVEN a search pattern that produces a large number of results WHEN the introspection tool is called THEN results are truncated at a reasonable limit and the response indicates truncation occurred

### 3.4 Search with Scope Restriction

**As a** Coq developer working within a specific module,
**I want to** restrict search results to a particular module or section,
**so that** I can narrow results to the most relevant context.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a search pattern and a module scope qualifier WHEN the introspection tool is called with command `Search` and the scope restriction THEN only names within the specified module are returned
- GIVEN a scope qualifier that names a nonexistent module WHEN the introspection tool is called THEN a structured error is returned indicating the module was not found

---

## Epic 4: Expression Evaluation

### 4.1 Compute a Term

**As a** Coq developer using Claude Code,
**I want to** evaluate a Coq expression to its normal form,
**so that** I can see what a term reduces to without switching to a Coq toplevel.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a well-typed Coq expression WHEN the introspection tool is called with command `Compute` and that expression THEN the response includes the fully reduced normal form of the expression
- GIVEN an ill-typed expression WHEN the introspection tool is called with command `Compute` THEN a structured error is returned including the Coq error message
- GIVEN a term whose reduction does not terminate within a reasonable time WHEN the introspection tool is called with command `Compute` THEN a structured error is returned indicating the computation timed out

### 4.2 Evaluate Under a Specific Strategy

**As a** Coq developer using Claude Code,
**I want to** evaluate a term under a specified reduction strategy (cbv, lazy, cbn, simpl, hnf, unfold),
**so that** I can control how far a term is reduced and inspect intermediate forms.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a well-typed expression and a valid reduction strategy name WHEN the introspection tool is called with command `Eval` and the strategy and expression THEN the response includes the term reduced under that strategy
- GIVEN an invalid or unsupported strategy name WHEN the introspection tool is called with command `Eval` THEN a structured error is returned indicating the strategy is not recognized
- GIVEN the `unfold` strategy and a list of names to unfold WHEN the introspection tool is called THEN only the specified names are unfolded in the result

### 4.3 Evaluate Inside a Proof

**As a** Coq developer in the middle of a proof,
**I want to** evaluate an expression that references hypotheses from the current proof context,
**so that** I can understand how local definitions and assumptions simplify.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active proof session with let-bound hypotheses WHEN the introspection tool is called with command `Compute` and a term referencing those hypotheses THEN the response includes the reduced form using the hypothesis values
- GIVEN an active proof session WHEN the introspection tool is called with command `Eval` with a strategy and a term referencing proof context THEN the response includes the term reduced under that strategy using the proof context

---

## Epic 5: Unified Tool Interface and Error Handling

### 5.1 Single MCP Tool with Command Parameter

**As a** developer of the MCP server,
**I want** all vernacular introspection commands to be exposed under a single MCP tool with a command parameter,
**so that** the tool count budget is respected and the interface remains consistent.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN the MCP server is running WHEN the tool list is requested THEN there is exactly one new tool for vernacular introspection (not one per command)
- GIVEN the introspection tool WHEN it is called with a `command` parameter set to any of `Print`, `Check`, `About`, `Locate`, `Search`, `Compute`, or `Eval` THEN the corresponding Coq vernacular command is executed
- GIVEN the introspection tool WHEN it is called with an unrecognized command parameter THEN a structured error is returned listing the valid command values

### 5.2 Structured Error Responses

**As a** Coq developer using Claude Code,
**I want** errors from introspection commands to be returned as structured data,
**so that** Claude can interpret failures and suggest corrections.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN any introspection command that fails WHEN the error is returned THEN the MCP response includes a structured error with the original command, the input that caused the error, and the Coq error message
- GIVEN a name-not-found error WHEN the error is returned THEN the error type is distinguishable from a type error or a malformed-command error
- GIVEN a malformed input (e.g., unparseable expression) WHEN the introspection tool is called THEN a structured error is returned indicating a parse failure with the Coq error message

### 5.3 Proof Session Context Awareness

**As a** Coq developer using Claude Code,
**I want** introspection commands to automatically use the active proof session's context when one exists,
**so that** I do not need to manually specify that I want local hypotheses included.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN no active proof session WHEN an introspection command is executed THEN it runs against the global Coq environment
- GIVEN an active proof session WHEN an introspection command is executed THEN it runs in the context of the current proof state, with access to local hypotheses and let-bindings
- GIVEN an active proof session WHEN the introspection tool is called with a term that references a local hypothesis by name THEN the command succeeds and uses the hypothesis from the proof context

# User Stories: Notation Inspection

Derived from [doc/requirements/notation-inspection.md](../notation-inspection.md).

---

## Epic 1: Notation Lookup

### 1.1 Look Up What a Notation Means

**As a** Coq user reading unfamiliar code,
**I want to** ask what a notation expands to by providing the symbol or a term that uses it,
**so that** I can understand what the notation means without searching through source files manually.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a loaded Coq project and a notation string (e.g., `_ ++ _`) WHEN the lookup tool is called THEN it returns the notation's expansion showing the underlying Coq term it desugars to
- GIVEN a term that uses a notation (e.g., `[1; 2; 3]`) WHEN the lookup tool is called THEN it returns the notation's expansion and the scope it was resolved from
- GIVEN a notation string that does not match any in-scope notation WHEN the lookup tool is called THEN a structured error is returned indicating the notation was not found
- GIVEN a valid notation WHEN the result is returned THEN it includes the notation string, the expanded term, the defining scope, and the defining module

### 1.2 Find Where a Notation Is Defined

**As a** Coq developer investigating a library's notation conventions,
**I want to** find the source location where a notation is defined,
**so that** I can read the original declaration and understand its intent.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a notation string WHEN the locate tool is called THEN it returns the fully qualified module path where the notation is defined
- GIVEN a notation that is defined in multiple scopes WHEN the locate tool is called THEN it returns all defining locations, one per scope, with the currently active interpretation marked
- GIVEN a notation string that requires non-obvious quoting (e.g., containing single quotes or underscores) WHEN the user provides the notation in its surface syntax THEN the tool handles quoting internally and returns the correct result

---

## Epic 2: Scope Inspection

### 2.1 List Notations in a Scope

**As a** Coq user exploring a library's notation surface,
**I want to** list all notations registered in a given scope,
**so that** I can discover available notations without reading source code.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a valid scope name (e.g., `list_scope`, `nat_scope`) WHEN the list-scope tool is called THEN it returns all notations registered in that scope, each with its notation string and expansion
- GIVEN an invalid or nonexistent scope name WHEN the list-scope tool is called THEN a structured error is returned indicating the scope was not found
- GIVEN a scope with more than 20 notations WHEN the result is returned THEN all notations are included (no truncation)

### 2.2 Show Active Scopes and Resolution Order

**As a** Coq user confused by which interpretation of a notation is being selected,
**I want to** see which notation scopes are currently open and in what order,
**so that** I can understand how Coq resolves notation ambiguity.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a loaded Coq environment WHEN the show-visibility tool is called THEN it returns the list of open scopes in priority order (most recently opened first)
- GIVEN the scope list WHEN it is returned THEN each entry includes the scope name and, if applicable, the type it is bound to
- GIVEN a notation that appears in multiple open scopes WHEN the show-visibility tool is called with that notation THEN the result indicates which scope's interpretation is active and why

---

## Epic 3: Notation Precedence and Associativity

### 3.1 Explain Notation Precedence and Associativity

**As a** Coq user struggling with unexpected parse results,
**I want to** query the precedence level and associativity of a notation,
**so that** I can understand why an expression parses the way it does.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a notation string WHEN the precedence tool is called THEN it returns the notation's precedence level (0-200), associativity (left, right, or none), and format string if one is defined
- GIVEN two notation strings WHEN both are queried THEN the user can compare their precedence levels to understand parsing order
- GIVEN a notation with `only parsing` or `only printing` flags WHEN the result is returned THEN those flags are included in the metadata

### 3.2 Explain How a Compound Expression Is Parsed

**As a** Coq user who wrote `a + b * c` and is unsure how it parsed,
**I want to** see the fully parenthesized form of an expression,
**so that** I can verify that the notation precedence produced the intended parse tree.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a Coq expression using multiple notations WHEN the explain-parse tool is called THEN it returns the fully parenthesized form showing how precedence and associativity resolved the expression
- GIVEN an expression that is ambiguous or ill-formed due to notation conflicts WHEN the tool is called THEN a structured error is returned explaining the ambiguity

---

## Epic 4: Ambiguous Notation Handling

### 4.1 List All Interpretations of an Ambiguous Notation

**As a** Coq user who received a "notation is ambiguous" warning or unexpected behavior,
**I want to** see all possible interpretations of a notation across open scopes,
**so that** I can determine which interpretation I want and how to select it.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a notation string that has interpretations in multiple open scopes WHEN the disambiguate tool is called THEN it returns all interpretations, each with the scope name, expansion, and whether it is the currently active interpretation
- GIVEN the list of interpretations WHEN one is the active interpretation THEN it is clearly marked and the reason for its selection (scope priority order) is included
- GIVEN a notation with only one interpretation in scope WHEN the disambiguate tool is called THEN it returns that single interpretation with a note that there is no ambiguity

### 4.2 Suggest How to Select a Specific Interpretation

**As a** Coq user who wants a non-default interpretation of an ambiguous notation,
**I want to** receive guidance on how to select the interpretation I want,
**so that** I can use `%scope` delimiters or `Open Scope` commands correctly.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an ambiguous notation and a user-selected target interpretation WHEN the tool is asked for guidance THEN it suggests the appropriate `%scope_key` delimiter to apply inline
- GIVEN an ambiguous notation WHEN the tool provides guidance THEN it also explains how `Open Scope` and `Close Scope` commands can change the default resolution

---

## Epic 5: Notation Authoring Guidance

### 5.1 Suggest a Notation Definition

**As a** Coq developer defining a new notation for a custom operator,
**I want to** describe my intent in natural language and receive a syntactically correct notation command,
**so that** I can avoid the trial-and-error process of getting notation syntax right.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a description of the desired notation (symbol, arity, precedence, associativity) WHEN the suggest-notation tool is called THEN it returns a syntactically correct `Notation` or `Infix` command
- GIVEN the suggested command WHEN it is evaluated in Coq THEN it is accepted without syntax errors
- GIVEN a request that would conflict with an existing notation in scope WHEN the suggestion is generated THEN a warning is included noting the potential conflict

# Type Error Explanation

Coq type errors are notoriously opaque. They report expected and actual types in fully expanded form, often spanning dozens of lines, with no indication of where the types diverge, what coercions were attempted, or what the user likely intended. Resolving a type error today requires manually running `Check`, `Print`, `About`, and `Print Coercions` to reconstruct the context the error message omits — a process that demands expert knowledge of Coq's type system. Type Error Explanation provides an `/explain-error` slash command that automates this entire diagnostic workflow: it parses the error, inspects the relevant types and coercions in the user's environment, and delivers a plain-language explanation of what went wrong and how to fix it.

**Stories**: [Epic 1: Error Parsing and Type Inspection](../requirements/stories/type-error-explanation.md#epic-1-error-parsing-and-type-inspection), [Epic 2: Plain-Language Explanation](../requirements/stories/type-error-explanation.md#epic-2-plain-language-explanation), [Epic 3: Coercion Analysis](../requirements/stories/type-error-explanation.md#epic-3-coercion-analysis), [Epic 4: Fix Suggestions](../requirements/stories/type-error-explanation.md#epic-4-fix-suggestions), [Epic 5: Notation and Scope Confusion](../requirements/stories/type-error-explanation.md#epic-5-notation-and-scope-confusion), [Epic 6: Advanced Diagnostics](../requirements/stories/type-error-explanation.md#epic-6-advanced-diagnostics), [Epic 7: Slash Command Integration](../requirements/stories/type-error-explanation.md#epic-7-slash-command-integration)

---

## Problem

When a Coq user encounters a type error, the error message itself is rarely sufficient to understand or resolve the problem. Coq prints the expected type and the actual type, but for types involving nested inductive families, universe polymorphism, implicit arguments, or coercions, these printouts are walls of text with no highlighting of where the divergence occurs. The user must then embark on a manual investigation: run `Print` to see what a type alias expands to, run `About` to check how many arguments a function expects, query `Print Coercions` to find out why an expected coercion was not applied, and mentally diff two large type expressions to locate the mismatch. Newcomers rarely know which commands to run. Experienced users know but spend significant time on what is ultimately mechanical detective work.

No existing tool addresses this gap. CoqIDE, VsCoq, and Proof General display Coq's raw error messages without interpretation. No IDE inspects the relevant type definitions, analyzes coercion paths, or explains the error in plain language. The diagnosis of a type error is an inherently multi-step, contextual reasoning task — exactly the kind of task that benefits from an agentic workflow combining structured inspection with natural language explanation.

## Solution

The `/explain-error` slash command gives users a single action that replaces the entire manual diagnostic workflow. When a user encounters a type error and invokes `/explain-error`, the command orchestrates multiple MCP tools to parse the error, inspect the types involved, analyze relevant coercions, and produce a complete diagnostic in plain language.

### Plain-Language Explanation

The core of every diagnostic is an explanation that a user can actually read. Rather than presenting raw type expressions for the user to decode, the command identifies what went wrong — which argument has the wrong type, where two types diverge, why a unification failed — and states it in terms the user can understand. Technical terms like "inductive type" or "universe" are defined when they cannot be avoided. The explanation pinpoints the specific sub-expression where types diverge rather than asking the user to visually diff two large type expressions.

### Contextual Type Inspection

The error message alone rarely tells the whole story. The command fetches the definitions of the types involved — expanding aliases, revealing parameters, and showing the actual structure behind opaque names. When the expected and actual types have the same name but come from different modules, the command identifies the ambiguity. When implicit arguments were inferred to unexpected types, the command shows what was inferred and why it conflicts with the rest of the term.

### Coercion and Scope Analysis

Many type errors arise not from genuinely wrong types but from coercions that were not applied or notations interpreted in the wrong scope. The command inspects available coercion paths between the expected and actual types, explains whether a coercion exists and why Coq did not apply it, and identifies when a notation like `+` or `::` was interpreted in a scope different from what the user intended. These are the errors that frustrate users most because the code "looks right" — the explanation reveals the hidden mismatch.

### Fix Suggestions

Understanding what went wrong is only half the problem; users also need to know what to do about it. The command suggests concrete fixes: explicit type annotations, coercion declarations, `@`-notation to override implicit arguments, `%scope` annotations to select the right notation scope, or alternative definitions that would make the term well-typed. When no clear fix can be determined, the command says so rather than producing a misleading suggestion.

## Scope

Type Error Explanation provides:

- A single `/explain-error` slash command that completes the full diagnostic workflow in one invocation
- Parsing of Coq type error messages to extract structured information (expected type, actual type, location, environment)
- Contextual inspection of type definitions, coercion paths, implicit arguments, and notation scopes
- Plain-language explanation of the root cause, accessible to users who do not fluently read Coq type expressions
- Concrete fix suggestions for common type error patterns
- Diagnosis of universe inconsistency errors and canonical structure projection failures for advanced users

Type Error Explanation does not provide:

- Modifications to Coq's error reporting or type checker
- New MCP tools — it consumes tools built by other initiatives (vernacular introspection, universe inspection, notation inspection)
- IDE plugins — the slash command runs within Claude Code
- Automated error correction — fixes are suggested, not applied without user approval
- Diagnosis of non-type errors such as tactic failures or syntax errors

---

## Design Rationale

### Why a slash command rather than automatic invocation

Type error diagnosis requires orchestrating multiple inspection steps and reasoning about the combined results — a workflow that benefits from being explicitly triggered rather than running on every error. Not every type error needs a detailed explanation; experienced users often recognize the problem at a glance. Making the diagnosis opt-in via `/explain-error` keeps the interaction lightweight when the user does not need help while providing deep analysis when they do.

### Why combine error parsing with contextual inspection

Coq's error messages are incomplete by design: they report the type mismatch but not the definitions behind the types, the coercion landscape, or the implicit argument decisions that led to the mismatch. Parsing the error alone would produce a reformatted version of the same opaque message. The value comes from combining the error with contextual inspection — fetching type definitions, checking coercion paths, examining implicit argument inference — to produce an explanation that contains information the error message itself does not. This is why no static tool has solved the problem: it requires multi-step, context-dependent reasoning.

### Why suggest fixes rather than apply them

Type errors often have multiple valid resolutions, and the best choice depends on the user's intent — something the tool cannot always determine. Applying a fix automatically risks "resolving" the type error in a way that changes the meaning of the user's code. Suggesting fixes preserves user agency: the user sees the options, understands the tradeoffs through the accompanying explanation, and chooses the resolution that matches their intent.

### Why build on existing MCP tools rather than new ones

The inspection capabilities this feature needs — querying type definitions, checking coercions, examining universe constraints, inspecting notations — are general-purpose operations that other features also require. Building them as standalone MCP tools in separate initiatives (vernacular introspection, universe inspection, notation inspection) and consuming them here avoids duplication, keeps the tool count manageable, and ensures that improvements to the underlying inspection tools automatically benefit type error diagnosis.

# Code Extraction Management — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Code extraction is the bridge between formally verified Coq/Rocq specifications and executable programs. Coq's `Extraction` and `Recursive Extraction` commands translate verified definitions into OCaml, Haskell, or Scheme, enabling verified software to run in production. Without extraction, verified code remains a mathematical artifact with no practical deployment path.

Extraction errors are common and hard to diagnose. Opaque types, axioms without realizers, universe inconsistencies, and unsupported term constructs all produce failures that require deep knowledge of Coq's extraction machinery. Users frequently abandon extraction attempts or produce subtly incorrect extracted code because they lack guidance on configuring extraction options, choosing the right target language, or interpreting error messages.

This initiative wraps Coq's extraction commands as MCP tools so that Claude can manage the extraction workflow end-to-end: extracting definitions, choosing target languages, explaining failures, suggesting fixes, and previewing extracted code before writing it to disk.

**Success metrics:**
- Successfully extract verified definitions to OCaml, Haskell, and Scheme for standard library types and user-defined inductive types
- Extraction failure diagnosis covers the five most common failure categories (opaque terms, axioms without realizers, universe inconsistencies, unsupported match patterns, and module type mismatches)
- Users can preview extracted code before committing it to a file
- Time from "user asks to extract" to "extracted code reviewed" is under 30 seconds for single-definition extraction

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Verified software developers | Extract proven-correct Coq definitions to executable OCaml, Haskell, or Scheme for integration into production systems | Primary |
| Coq learners | Understand what extraction produces, why it fails, and how to fix extraction errors without deep knowledge of Coq internals | Primary |
| Research engineers | Rapidly iterate on extraction configurations (inlining, optimizations, type mappings) to produce clean extracted code for benchmarks and prototypes | Secondary |
| Library authors | Validate that library definitions extract cleanly to all supported target languages before publishing | Tertiary |

---

## 3. Competitive Context

**Current Coq extraction workflow:**
- Users manually write `Extraction` or `Recursive Extraction` commands in `.v` files or at the Coq toplevel
- Extraction errors are reported as raw Coq error messages with no suggested fixes
- No preview mechanism: extracted code is written directly to a file or printed to the console
- Configuring extraction options (inlining, custom type mappings, axiom realizers) requires reading the Coq reference manual and trial-and-error
- No IDE or tool provides guided extraction workflow

**Gaps this initiative addresses:**
- No existing MCP server or AI tool wraps Coq extraction commands
- No tool explains extraction failures in plain language or suggests fixes
- No tool provides interactive preview of extracted code before writing to disk
- No tool helps users choose between OCaml, Haskell, and Scheme based on their use case and the characteristics of the definitions being extracted

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R-CE-P0-1 | Extract a single named Coq definition to a specified target language (OCaml, Haskell, or Scheme) and return the extracted code |
| R-CE-P0-2 | Recursively extract a Coq definition and all its transitive dependencies to a specified target language and return the extracted code |
| R-CE-P0-3 | Support OCaml, Haskell, and Scheme as extraction target languages, selectable per extraction request |
| R-CE-P0-4 | When extraction fails, return a plain-language explanation of the failure cause and one or more suggested fixes |
| R-CE-P0-5 | Preview extracted code in the tool response without writing it to a file, so the user can review before committing |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R-CE-P1-1 | Configure extraction options per request: inlining directives, optimization level, and custom type mappings between Coq types and target language types |
| R-CE-P1-2 | Write previewed extraction output to a specified file path upon user confirmation |
| R-CE-P1-3 | List all extractable definitions in the current Coq document or loaded modules |
| R-CE-P1-4 | Warn when extracting definitions that depend on axioms without realizers, identifying which axioms lack realizers |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R-CE-P2-1 | Compare extraction output across target languages for the same definition, highlighting structural differences |
| R-CE-P2-2 | Suggest the most appropriate target language based on the characteristics of the definition being extracted (e.g., heavy use of dependent types favors OCaml, monadic code may suit Haskell) |
| R-CE-P2-3 | Batch extraction of multiple definitions in a single request |

---

## 5. Scope Boundaries

**In scope:**
- MCP tool wrappers around Coq's `Extraction` and `Recursive Extraction` commands
- Target language selection (OCaml, Haskell, Scheme)
- Extraction failure explanation and fix suggestions
- Extracted code preview before writing to file
- Extraction option configuration (inlining, optimizations, type mappings)
- Axiom realizer warnings

**Out of scope:**
- Compilation or type-checking of the extracted output in the target language
- Runtime execution of extracted code
- Extraction to languages not supported by Coq's extraction mechanism (e.g., Python, Rust)
- Modification of Coq source code to make definitions extractable
- Custom extraction plugins or patches to Coq's extraction machinery
- Training data generation from extracted code
- Performance benchmarking of extracted code

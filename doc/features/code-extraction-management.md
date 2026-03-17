# Code Extraction Management

Managed extraction of verified Coq/Rocq definitions to executable OCaml, Haskell, or Scheme. Claude Code invokes extraction as a tool to bridge the gap between formally verified specifications and runnable programs — handling target language selection, dependency resolution, failure diagnosis, and output preview so the user never has to write raw extraction commands or decipher opaque error messages.

**Stories:** [Epic 1: Basic Extraction](../requirements/stories/code-extraction.md#epic-1-basic-extraction), [Epic 2: Target Language Selection](../requirements/stories/code-extraction.md#epic-2-target-language-selection), [Epic 3: Extraction Failure Handling](../requirements/stories/code-extraction.md#epic-3-extraction-failure-handling), [Epic 4: Extraction Preview](../requirements/stories/code-extraction.md#epic-4-extraction-preview)

---

## Problem

Extraction is the only path from a verified Coq proof to code that actually runs. A theorem proven correct in Coq has no practical deployment value until its computational content is extracted to a general-purpose language. Yet extraction is where verified software projects most often stall.

The errors are common and opaque. An axiom missing a realizer, an opaque term that blocks reduction, a universe inconsistency deep in a dependency chain, an unsupported match pattern, a module type mismatch — each produces a terse Coq error that assumes the user already understands extraction internals. Learners abandon extraction attempts entirely. Experienced users resort to trial-and-error, toggling transparency flags and extraction directives until something compiles, with no confidence that the resulting code is what they intended.

Even when extraction succeeds, the workflow is clumsy. Users write extraction commands by hand, wait for output, inspect it manually, and repeat if the target language or options were wrong. There is no way to preview what extraction will produce before committing it to a file, no guidance on which target language suits a given definition, and no explanation of why a particular extraction looks the way it does.

## Solution

Claude Code manages the full extraction workflow through a single tool interface. The user names a definition and a target language; the tool handles the rest.

### Single Definition Extraction

Extracting a single named definition produces the corresponding code in the target language and returns it directly. If the definition does not exist in the current environment, the tool reports the unknown name. The extracted code is returned as-is — one definition, one output, no side effects.

### Recursive Extraction

When a definition depends on other definitions, recursive extraction pulls in the entire transitive dependency tree and returns a self-contained module. The user gets everything needed to compile the extracted code independently in the target language, without manually tracking which helpers, types, and sub-definitions are required. If the definition has no dependencies beyond Coq's built-in types, recursive extraction produces the same output as single extraction.

### Target Language Selection

Every extraction request specifies a target language: OCaml, Haskell, or Scheme. These are the three languages Coq's extraction mechanism supports. If a user requests an unsupported language, the tool responds with the list of supported options rather than failing silently. The choice of language is per-request — the user can extract the same definition to multiple languages in sequence to compare results.

### Failure Explanation

When extraction fails, the tool returns both the raw Coq error and a plain-language explanation of what went wrong, along with at least one suggested fix. The five most common failure categories are covered: opaque terms that need transparency directives, axioms that lack realizers and need `Extract Constant` bindings, universe inconsistencies that require restructuring, unsupported match patterns, and module type mismatches. The user sees what broke, why it broke, and what to try next — without needing to consult the Coq reference manual.

### Preview Before Write

Extraction never writes to disk by default. Every extraction request returns the generated code in the tool response so the user can review it first. If the output looks correct, the user can then request that it be written to a specified file path. If something is wrong — the target language was a poor fit, an extraction option needs adjustment, the output is unexpectedly large — the user iterates without any file having been created. This preview-then-commit workflow prevents the common mistake of overwriting a file with extraction output that turns out to be incorrect.

## Design Rationale

### Why extraction is essential for verified software

A Coq proof is a mathematical artifact. It establishes that a property holds for all inputs, that an algorithm meets its specification, that a protocol preserves an invariant. But a Coq proof does not run. Extraction is what turns the computational content of a proof into a program that executes — an OCaml function, a Haskell module, a Scheme procedure. Without extraction, formal verification is an academic exercise disconnected from production software. Every verified software project that ships real code depends on extraction working correctly.

### Relationship to assumption auditing

Extraction quality is directly tied to the logical health of the definitions being extracted. A definition that depends on axioms without realizers will either fail to extract or produce code with holes — `assert false` stubs where the axiom's computational content should be. This is where extraction management connects to assumption auditing: axiom-free proofs extract cleanly, while axiom-dependent proofs require explicit realizer bindings. By surfacing axiom warnings during extraction, the tool closes the loop between proof hygiene and code generation — users discover at extraction time, not at runtime, that their verified code rests on unimplemented assumptions.

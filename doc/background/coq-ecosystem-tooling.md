# Coq/Rocq Ecosystem Tooling: State of the Art (March 2026)

A survey of the Coq/Rocq tooling ecosystem across IDE support, documentation, package management, CI/CD, proof visualization, and cross-system translation. This document covers what exists today and how it compares with the Lean 4 ecosystem, which serves as the primary point of reference given its rapid tooling investment since 2023.

---

## 1. IDE Tooling and Language Servers

### Current Coq/Rocq Landscape

The Coq IDE landscape is fragmented across five interfaces with different capabilities and maintenance status:

| Tool | Description | Status |
|------|-------------|--------|
| **coq-lsp (rocq-lsp)** | Modern language server with continuous incremental checking, real-time interruption, error recovery, literate Markdown/LaTeX support, multiple workspaces, positional goals, performance data, jump-to-definition, and completion. Supports Rocq 9.0/9.1. | Actively developed. |
| **VsRocq (VSCoq 2)** | Official VS Code extension built on native LSP. | Active. |
| **VSCoq Legacy (VSCoq 1)** | Legacy extension using XML-based coqidetop protocol. | Maintenance mode. |
| **CoqIDE** | Standalone GTK-based IDE distributed with Coq. Used by 52% of respondents in the 2022 Coq Community Survey. | Stable; mature. |
| **Proof General (Emacs)** | Most popular editor among experienced Coq users (61% in the 2022 survey). Long-established; deep Emacs integration. | Mature; maintained. |

### Lean 4 Comparison

Lean has a single official LSP built into the compiler, a single official VS Code extension with an Infoview panel (proof states, messages, user widgets), and community-maintained Emacs/Neovim integrations using the same LSP. The unified story reduces newcomer confusion and concentrates development effort.

### Assessment

Coq's IDE fragmentation is a significant pain point. The 2022 Coq Community Survey (466 respondents, JAR 2025) showed strong editor lock-in correlating with experience level. coq-lsp is technically strong and narrowing the gap, but ecosystem fragmentation persists. Lean's Infoview with user widgets has no Coq equivalent -- Coq proof state display is not extensible by library authors.

---

## 2. Documentation Generation

| Tool | Description | Status |
|------|-------------|--------|
| **coqdoc** | Standard documentation generator producing LaTeX or HTML from Coq source files. | Mature but limited. |
| **Alectryon** | Literate programming toolkit that captures Coq output and interleaves it with proof scripts to produce interactive webpages. Also supports Lean 4. Addresses the fundamental problem that proof scripts are opaque without an interactive IDE. | Active; cross-system. |
| **Rocqnavi** | HTML documentation generator for Coq source files. | Maintained; niche. |
| **Coq Platform Docs** | Community project for practical interactive tutorials and how-to guides. | In development. |

Lean has doc-gen4 (official, generates HTML from .lean files) and the Mathlib4 docs website with fuzzy search. The gap here is narrow; Alectryon is arguably more sophisticated for literate technical writing and works across both ecosystems.

---

## 3. Proof Visualization

### Current Coq/Rocq Landscape

| Tool | Description | Status |
|------|-------------|--------|
| **Alectryon** | Produces interactive HTML showing proof states alongside scripts. | Active. |
| **coq-dpdgraph** | Plugin extracting dependency graphs between Coq objects; outputs .dpd files for Graphviz visualization. | Maintained; niche. |

### Lean 4 Comparison

Lean's ProofWidgets4 allows library authors to embed arbitrary interactive React components in the Lean Infoview -- diagrams, plots, custom visualizations of mathematical structures. The User Widgets API is a first-class Lean feature. Library authors can register custom visualizations that render when specific types, tactics, or proof states are active.

### Assessment

This is a major differentiator. Coq has nothing comparable to ProofWidgets4. Visualization is limited to static dependency graphs and Alectryon's linear proof state interleaving. There is no mechanism for Coq library authors to extend IDE display with custom visualizations.

---

## 4. Library Search and Lemma Discovery

### Current Coq/Rocq Landscape

| Tool | Description | Status |
|------|-------------|--------|
| **`Search` command** | Built-in pattern search for constants in scope. Supports wildcards and notation patterns. | Mature; basic. |
| **`SearchPattern`, `SearchRewrite`** | Specialized search variants for pattern and rewrite rule discovery. | Mature; basic. |
| **coq-dpdgraph** | Dependency graph extraction (not search per se, but aids navigation). | Maintained; niche. |

### Lean 4 Comparison

Lean has at least six actively maintained search tools:

| Tool | Type | Status |
|------|------|--------|
| **Loogle** | Formal pattern-based search (constant names, subexpression patterns) | Mature; widely used |
| **Moogle** | LLM-based natural language search over Mathlib | Community standard |
| **LeanSearch** | Alternative natural language / semantic search | Active |
| **LeanExplore** | Search engine for Lean 4 declarations; web, CLI, IDE | Active |
| **Lean Finder** | AI semantic search aligned with mathematician intents (ICML 2025) | Published 2025 |
| **`exact?`** | Tactic that searches locally available lemmas closing the goal | Built-in; mature |

### Assessment

This is one of the starkest gaps in the Coq ecosystem. Coq has only the built-in `Search` command family, which is purely syntactic -- users must already know the approximate shape of what they are looking for. There is no natural language search, no semantic similarity search, no fuzzy matching, and no Coq equivalent to any of Lean's six search tools. The 2022 Coq Community Survey identified lemma discoverability as a significant pain point, especially for users working with large libraries like MathComp.

---

## 5. Package Management and Discovery

### Current Coq/Rocq Landscape

| Tool | Description | Status |
|------|-------------|--------|
| **opam** | OCaml package manager, also used for Coq packages. Flexible, Git-friendly, multi-compiler support. | Mature; ecosystem standard. |
| **Rocq Platform** | Curated distribution of Rocq with selected libraries and tools. Regular releases. | Active. |
| **Nix** | Alternative package management via nixpkgs Coq overlay. | Community-maintained. |
| **awesome-coq** | Manually maintained curated list of Coq resources. | Community-maintained. |

### Lean 4 Comparison

Lean has Lake (official build system and package manager, written in Lean, merged into Lean 4 core) and Reservoir (centralized, searchable package registry with automated build testing and browsable web interface).

### Assessment

Both ecosystems have functional package management, but with different trade-offs. Opam is powerful and general but not Coq-specific. Lean's Reservoir provides Coq-absent discoverability: a centralized, searchable registry with Lean-specific metadata and automated CI. The Rocq Platform fills a different niche (curated stability vs. broad discoverability). New Coq users struggle to find relevant libraries beyond the curated platform.

---

## 6. CI/CD Infrastructure

### Current Coq/Rocq Landscape

| Tool | Description | Status |
|------|-------------|--------|
| **Coq Docker images** | Official Docker images for CI pipelines. | Maintained. |
| **opam CI** | Standard opam-based CI using .opam files. | Mature. |
| **Rocq Platform testing** | Integration testing across the curated platform. | Active. |

### Lean 4 Comparison

Lean has `lean-action` (official GitHub Action with smart caching using composite keys), Mathlib's compiled olean caching (`lake exe cache get`), and Reservoir's automated cross-package CI testing.

### Assessment

Lean's CI infrastructure is more purpose-built. Most active Coq projects have working CI configurations, but setup requires more manual effort. There is no Coq equivalent to Lean's compiled artifact caching for large proof developments, meaning recompilation is expensive for projects at the MathComp scale.

---

## 7. Proof State Serialization

### Current Coq/Rocq Landscape

| Tool | Description | Status |
|------|-------------|--------|
| **SerAPI (coq-serapi)** | Machine-to-machine interface serializing Coq internal OCaml datatypes to JSON/S-expressions. Three programs: sertok (tokens), sercomp (syntax trees), sername (kernel trees). | Mature but version-locked. |
| **coq-lsp** | Exposes proof state information via LSP protocol extensions. | Active. |

### Assessment

SerAPI provides deep serialization of Coq internals and is the most thorough serialization available for any proof assistant. However, it requires pinning to specific Coq/OCaml versions and has no stable, documented protocol for programmatic proof interaction suitable for ML pipeline integration. coq-lsp exposes proof states via LSP but these are designed for IDE communication, not ML pipeline integration. There is no standardized, version-stable protocol for external tools to observe and interact with Coq proof states.

---

## 8. Cross-System Translation

| Project | Description | Status |
|---------|-------------|--------|
| **Babel-formal** | LLM-based source-to-source translation between Lean and Rocq. | Research; 2025. |
| **coq_lean_translation** | Atlas Computing project for definition/proof translation between Coq and Lean. Available on Lean Reservoir. | Early-stage. |
| **PROOFWALA** | Unified framework for interacting with and collecting data from both Coq and Lean 4. | Research; 2025. |

Cross-system translation is nascent in both directions. No production-quality tool exists. The underlying type-theoretic similarity (both based on CIC variants) makes Coq-Lean translation more tractable than translation between more distant systems (e.g., Lean and Isabelle/HOL).

---

## 9. Proof Refactoring

Neither Coq nor Lean has mature, dedicated proof refactoring tools comparable to mainstream programming language IDEs. Coq has built-in `rename` for hypotheses and `rewrite`/`setoid_rewrite` for term rewriting, but no automated rename-across-project, extract-lemma, or inline-proof tools. Lean's metaprogramming architecture is better positioned to support such tools, and a VS Code Code Actions extension provides basic refactoring snippets. This is an underserved area in both ecosystems.

---

## 10. Metaprogramming

Coq offers two metaprogramming systems:

- **Ltac/Ltac2**: Tactic scripting languages. Ltac is established but has known design limitations. Ltac2 is a modern replacement with better typing and error handling but lower adoption.
- **OCaml plugin system**: Full access to Coq internals via OCaml. Powerful but requires OCaml expertise and knowledge of Coq's internal API, which is unstable across versions.

Lean 4's metaprogramming is written in Lean itself -- tactics, commands, and macros are all Lean programs. This single-language approach lowers the barrier to entry and enables richer tool development by library authors.

The metaprogramming accessibility gap has downstream effects: it is easier for the Lean community to build custom IDE extensions, proof automation, and tooling because the barrier to entry is lower.

---

## Coq Community Pain Points (2022 Survey)

The Coq Community Survey 2022 (466 respondents, published JAR 2025) is the largest ITP user survey conducted. Key findings relevant to tooling:

1. **IDE fragmentation**: Five competing interfaces with different capabilities split development effort and confuse newcomers.
2. **Steep learning curve**: "Programming skills" identified as a barrier disproportionately affecting newcomers. Lack of internal documentation hinders contributions.
3. **Lemma discoverability**: Built-in `Search` is purely syntactic. Users must already know approximate lemma shapes.
4. **AI tooling lag**: Interest in AI assistance but lack of mature, integrated tooling.
5. **Build times and caching**: No compiled artifact caching for large developments.
6. **Name disruption**: The Coq-to-Rocq rename (2023-2025) caused community friction and concerns about breaking existing tooling and documentation.
7. **Metaprogramming accessibility**: Higher barrier to entry than Lean's single-language approach.

### Areas Where Coq Retains Advantages

- **Industrial verification track record**: CompCert, Fiat-Crypto, Iris, and other major verified systems.
- **Mature hammer**: CoqHammer has years of refinement.
- **Alectryon**: Literate proof documentation (cross-system).
- **Ecosystem breadth**: More total verified code and more diverse application domains.
- **Dependent pattern matching and universe polymorphism**: More mature handling in certain edge cases.

---

## References

Coq Community Survey 2022. "Lessons for ITP Researchers from a Survey of Coq Users." JAR 2025.

Gallego Arias, E. "coq-lsp: A Language Server for the Coq/Rocq Prover." 2023.

Gallego Arias, E. "SerAPI: Machine-Friendly Coq API." 2016.

Pitclaudel, C. "Alectryon: A collection of tools for writing technical documents." GitHub.

Leanprover Community. "ProofWidgets4." GitHub, 2023--present.

Buzzard, K. et al. "Searching for Theorems in Mathlib." Lean community blog.

Lu, Y. et al. "Lean Finder: Semantic Search for Mathlib." ICML 2025.

Babel-formal. "Translation between Lean and Rocq." HAL, 2025.

PROOFWALA. "Unified Framework for Coq and Lean 4." arXiv:2502.04671, 2025.

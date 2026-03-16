# Coq/Rocq Ecosystem Gaps and Opportunities (March 2026)

An analysis of unmet needs in the Coq/Rocq ecosystem, synthesized from the 2022 Coq Community Survey (466 respondents, JAR 2025), comparative analysis with Lean 4 tooling, and the current AI theorem proving research landscape. This document identifies opportunities for open-source tools that would benefit the Coq community.

Cross-references:
- [coq-ecosystem-tooling.md](coq-ecosystem-tooling.md)
- [coq-ai-theorem-proving.md](coq-ai-theorem-proving.md)
- [coq-premise-retrieval.md](coq-premise-retrieval.md)

---

## 1. Semantic Lemma Search

**Gap severity**: High -- one of the starkest user-facing gaps

**Problem**: Coq's built-in `Search` command is purely syntactic. Users must already know the approximate shape of the lemma they seek. There is no natural language search, no embedding-based semantic retrieval, no fuzzy matching. Lean has at least six actively maintained search tools spanning formal pattern matching (Loogle), natural language search (Moogle), and AI-powered intent understanding (Lean Finder). Coq has none.

**Opportunity**: A semantic search engine for Coq/Rocq libraries providing:

- **Pattern search** (Loogle-equivalent): Type signature patterns, constant names, subexpression patterns. More expressive than the built-in `Search`. Exposed as a web interface and IDE integration.
- **Natural language search** (Moogle-equivalent): Describe what you need in plain language and retrieve matching lemmas using embedding-based retrieval over lemma statements, names, and docstrings.
- **Type-directed search**: Given a goal type, find lemmas whose conclusion unifies with or relates to the goal. Subsumes `exact?`-style search with semantic ranking rather than brute-force enumeration.

**Index scope**: Coq standard library, MathComp, and any opam-installed Coq library. Extensible to user projects.

**Deployment modes**: Web interface (searchable without installation), coq-lsp plugin (in-editor), CLI (scriptable).

**Why this matters**: Lemma discoverability directly impacts every Coq user's daily workflow. It is the most frequently cited user-facing frustration in community discussions. Unlike AI tooling (which primarily benefits researchers), semantic search benefits everyone from students to industrial verification engineers.

---

## 2. Modern Training Data Extraction Pipeline

**Gap severity**: High -- the starkest infrastructure gap between Coq and Lean

**Problem**: Coq's training data infrastructure is aging. CoqGym (2019) is pinned to Coq 8.9+ and has not been fundamentally updated. SerAPI provides deep serialization but requires version-locked OCaml bindings and has no equivalent of LeanDojo's incremental tracing, premise annotations, or gym-like interactive environment. Every Coq-focused AI theorem proving project must independently solve the data extraction problem, leading to duplicated effort and incompatible datasets.

LeanDojo (NeurIPS MathAI 2025) provides end-to-end extraction-training-deployment with 122K+ theorems, premise provenance annotations, and RL-style interaction. It has become the standard substrate for AI theorem proving research on Lean. No comparable substrate exists for Coq.

**Opportunity**: A modern extraction pipeline providing:

1. **Proof state extraction**: Capture goals, hypotheses, local context, and available lemmas at every tactic step, serialized to a standard format (JSON or S-expressions). Build on coq-lsp or SerAPI internals but expose a clean, version-stable API.
2. **Premise annotations**: For each tactic application, record which lemmas, definitions, and hypotheses were actually used (not just what was in scope). This is the key data enabling retrieval-augmented proving.
3. **Incremental tracing**: Trace changes to a proof development without reprocessing the entire project. Track file-level dependencies and re-extract only affected proofs.
4. **Gym-like interaction**: A programmatic observe-submit-feedback loop for RL-style training. Submit a tactic, observe the resulting proof state, decide the next action.
5. **Dataset management**: Versioned datasets with metadata (Coq version, library version, extraction date). Support for continuous dataset updates as libraries evolve.

**Extraction targets**: Coq standard library and MathComp initially. Stretch target: full Rocq Platform.

**Building on**: SerAPI (serialization), coq-lsp (incremental checking), CoqGym (proof state format, needs modernization), PROOFWALA (unified Coq/Lean interaction framework, 2025).

**Why this matters**: This is foundational infrastructure. Every other AI-for-Coq tool depends on training data. Without a modern extraction pipeline, Coq-focused AI research is hobbled at the data layer.

---

## 3. Proof State Interaction Protocol

**Gap severity**: Medium-High

**Problem**: There is no standardized, version-stable protocol for external tools to observe and interact with Coq proof states. SerAPI is version-locked and requires OCaml expertise. coq-lsp's LSP extensions are designed for IDE communication, not ML pipeline integration. The Pantograph project (2024) demonstrates the value of structured proof state APIs for Lean.

**Opportunity**: A standardized proof interaction protocol providing:

1. **Stable serialization format**: A documented JSON schema for proof states (goals, hypotheses, types, environments) that is version-stable across Coq releases. Insulate downstream tools from internal Coq representation changes.
2. **Interaction protocol**: A request-response protocol for submitting tactics, observing proof states, querying the environment, and managing proof sessions. Implementable over multiple transports (stdio, HTTP, LSP).
3. **Client libraries**: Reference implementations in Python (for ML pipelines) and OCaml (for Coq-native tools).

**Relationship to training data extraction**: This protocol is the communication substrate on which the training data extraction pipeline's gym-like interaction would be built. It is separated because it has standalone value: any tool that needs to interact programmatically with Coq benefits from a stable interface.

**Building on**: coq-lsp already provides substantial proof state information. This opportunity extends and stabilizes that into a documented, ML-pipeline-friendly protocol.

---

## 4. LLM-Integrated Copilot

**Gap severity**: High

**Problem**: Lean has LeanCopilot (native integration with suggest_tactics, search_proof, select_premises, all verified by the Lean kernel before display) and llmstep (model-agnostic tactic suggestion). Coq has only CoqPilot (JetBrains, 2024), which is early-stage, VS Code-only, and limited in scope.

**Opportunity**: An LLM-integrated copilot providing:

1. **Tactic suggestion**: Given the current proof state, suggest candidate next tactics. Rank by likelihood and verify each candidate against Coq before presenting.
2. **Proof search**: Combine LLM-generated tactics with existing automation (CoqHammer sauto, Tactician) in a best-first search tree. Return complete proof scripts when found.
3. **Premise selection**: Given a goal, suggest relevant lemmas from the library. Use a semantic search index as the retrieval backend.
4. **Model-agnostic architecture**: Support multiple LLM backends (local models, API-based). Users choose their model; the tool provides the Coq-specific extraction, verification, and presentation layer.

**IDE integration**: coq-lsp and VsRocq as primary targets; Proof General/Emacs as secondary.

**Dependencies**: Benefits from training data extraction (for fine-tuned models) and semantic search (for premise retrieval), but can function with off-the-shelf LLMs initially.

---

## 5. Neural Premise Selection for CoqHammer

**Gap severity**: Medium

**Problem**: CoqHammer is mature and effective but its premise selection uses traditional ML features (term frequency, symbol overlap). Neural premise selection has been shown to dramatically outperform symbolic methods: LeanHammer's neural selector achieves 72.7% Recall@32 versus MePo's 42.1%. Research also shows that neural+symbolic unions outperform either alone by 21%.

**Opportunity**: A neural premise selection module for CoqHammer:

1. **Embedding model**: Train a premise embedding model on Coq proof data. Encode lemma statements and proof goals into a shared vector space using contrastive learning.
2. **Retrieval**: Given a goal, retrieve the top-K most relevant premises using approximate nearest neighbor search.
3. **Integration**: Plug into CoqHammer's existing premise selection pipeline as an additional selector. CoqHammer already supports multiple selection strategies; a neural selector should be architecturally straightforward to add.
4. **Hybrid union**: Following the LeanHammer finding, combine neural and symbolic selectors via union for maximum recall.

**Dependencies**: Requires training data (premise annotations from the extraction pipeline) for the embedding model training corpus.

**Research findings informing this opportunity**:
- LeanHammer: 72.7% R@32 with 82M-parameter encoder, 1-second latency
- Graph-augmented retrieval: +26% R@10 from adding dependency graph structure
- Formal-language tokenizers: Significant improvement from domain-specific WordPiece tokenization
- Graph2Tac: Online adaptation to new definitions is highly valuable for Coq's interactive workflow

---

## 6. Interactive Proof Visualization Widgets

**Gap severity**: High (no Coq equivalent exists)

**Problem**: Lean's ProofWidgets4 allows library authors to embed arbitrary interactive React components in the Lean Infoview -- diagrams, plots, custom visualizations. Coq has no equivalent: proof states are displayed as text in IDE panels, and library authors cannot extend the display.

**Opportunity**: A widget framework for Coq/Rocq proof development:

1. **Widget API**: Allow library authors to register custom visualizations that render when specific types, tactics, or proof states are active (e.g., commutative diagrams for category theory, state machines for protocol proofs).
2. **Rendering target**: HTML/JavaScript widgets in the IDE (coq-lsp's VS Code integration is the natural host). Alectryon compatibility for static export.
3. **Proof state visualization**: A built-in widget providing richer display than plain text -- type annotations on hover, collapsible hypotheses, visual distinction between computational and propositional content.

---

## 7. CI/CD Tooling

**Gap severity**: Medium

**Problem**: Coq projects must configure CI manually using opam and Docker images. There is no equivalent of Lean's lean-action GitHub Action (one-line setup, smart caching) or Mathlib's compiled olean caching that eliminates redundant recompilation for large developments.

**Opportunity**: A GitHub Action and CI toolkit:

1. **GitHub Action**: `rocq-action` providing one-line CI setup. Automatic detection of Coq version, opam dependencies, and build system. Smart caching of compiled .vo files using project-specific cache keys.
2. **Compiled artifact caching**: For large proof developments (MathComp scale), cache compiled artifacts and serve them to developers.
3. **Cross-version testing**: Easy testing against multiple Coq/Rocq versions in the CI matrix.

---

## 8. Package Discovery and Registry

**Gap severity**: Medium

**Problem**: Coq packages are distributed via opam (a general OCaml package manager) with no Coq-specific discoverability layer. The awesome-coq list is manually maintained. Lean's Reservoir provides a centralized, searchable registry with automated build testing.

**Opportunity**: A Coq-specific package registry:

1. **Registry**: Index all Coq packages from opam with Coq-specific metadata (compatible versions, library dependencies, documentation links, build status).
2. **Search**: Searchable by topic, dependency, and compatibility. Natural language search for "what package provides X."
3. **Build status**: Automated build testing against current Rocq versions with status badges.
4. **Web interface**: Browsable without installing anything.

---

## 9. Sequencing and Dependencies

```
Phase 1 (Foundation -- standalone value, immediate community impact):
  Semantic Lemma Search          -- no dependencies; solves daily pain
  Proof Interaction Protocol     -- standalone value; enables Phases 2 and 3

Phase 2 (AI Infrastructure):
  Training Data Extraction       -- depends on Interaction Protocol; enables Phase 3
  CI/CD Tooling                  -- independent; enables Package Registry

Phase 3 (AI Applications):
  LLM Copilot                   -- depends on Extraction and Semantic Search
  Neural Premise Selection       -- depends on Extraction

Phase 4 (Ecosystem Polish):
  Proof Visualization Widgets    -- independent
  Package Registry               -- benefits from CI/CD Tooling
```

Phase 1 projects have immediate standalone value and solve problems that Coq users feel daily. They are natural starting points for community engagement, building goodwill and credibility before the more ambitious AI infrastructure work.

---

## 10. Relevance of Research Findings

Several research findings from the broader AI theorem proving community inform the prioritization and design of these opportunities:

### The Retrieval Bottleneck

Across multiple systems, generating useful lemmas is easier than ensuring they are retrieved and applied when relevant. LEGO-Prover generated 20,000+ lemmas but exactly one was reused. This suggests that making existing Coq libraries more discoverable (Opportunities 1 and 5) is more impactful than systems that generate new lemmas.

### Complementarity of Neural and Symbolic

LeanHammer's 21% improvement from neural+symbolic union, and Graph2Tac's finding that GNN and k-NN approaches are highly complementary, argue for hybrid approaches rather than pure neural or pure symbolic tools.

### Structure Matters

The +26% Recall@10 from adding graph structure and the competitive performance of training-free tree-based methods suggest that Coq's dependency graph and expression structure are underexploited. Tools should leverage Coq's kernel-level dependency tracking.

### User Intent Alignment

Lean Finder's 81.6% upvote rate (vs. 56.9% for LeanSearch) demonstrates that aligning search with how users actually look for lemmas -- not just formal similarity -- is a major opportunity. No equivalent study exists for Coq users.

### Formal-Specific Tokenization

Domain-specific tokenizers trained on formal language corpora significantly improve embedding quality for retrieval. Coq-specific tokenizers handling Coq notation conventions, MathComp idioms, and Ltac patterns could yield similar gains.

---

## Summary Table

| Opportunity | Gap Severity | Dependencies | Primary Beneficiary |
|-------------|-------------|-------------|-------------------|
| Semantic Lemma Search | High | None | All Coq users |
| Training Data Extraction | High | Interaction Protocol | AI researchers, tool builders |
| Proof Interaction Protocol | Medium-High | None | Tool builders, AI researchers |
| LLM Copilot | High | Extraction, Search | All Coq users |
| Neural Premise Selection | Medium | Extraction | CoqHammer users, researchers |
| Proof Visualization | High | None | Educators, complex formalization developers |
| CI/CD Tooling | Medium | None | All Coq project maintainers |
| Package Registry | Medium | None (benefits from CI/CD) | All Coq users, especially newcomers |

# AI-Assisted Theorem Proving and the Coq/Rocq Ecosystem (March 2026)

A survey of AI-assisted theorem proving as it relates to the Coq/Rocq proof assistant, covering Coq-specific tools, training data infrastructure, the broader AI proving landscape, and the growing gap between Coq and Lean in AI tooling.

---

## 1. The AI Proving Landscape (2024-2026)

AI-assisted theorem proving has undergone rapid advancement. On the FrontierMath benchmark, leading AI models improved from under 2% (November 2024) to over 40% (January 2026). Multiple systems achieved gold-medal performance at IMO 2025. The miniF2F benchmark is effectively saturated at 95%+.

Key architectural patterns across successful systems:

- **Sketch-then-prove**: An LLM generates a natural-language proof plan, converts it to a formal sketch with intermediate lemmas as stubs, then fills each independently.
- **Neuro-symbolic hybridization**: LLM-generated tactics interleaved with symbolic automation (SMT solvers, hammers). LLMs provide high-level strategy; solvers handle mechanical discharge.
- **RL from verifier feedback**: The proof checker serves as a perfect reward signal, enabling reinforcement learning with unusually clean supervision.
- **Subgoal decomposition**: Complex goals decomposed into sequences of subgoals, creating cheap checkpoints for early termination of unpromising searches.

### Ecosystem Concentration on Lean 4

Nearly all frontier AI proving systems target Lean 4, driven by Mathlib's size (210,000+ theorems), LeanDojo's extraction infrastructure, and the self-reinforcing cycle of more training data producing better models, attracting more users, generating more data. The systems achieving headline results -- AlphaProof, Seed-Prover, Aristotle, DeepSeek-Prover, Goedel-Prover, BFS-Prover -- all operate on Lean 4.

This concentration means improvements in AI proof search disproportionately benefit Lean-based workflows.

---

## 2. Coq-Specific AI Tools

### CoqHammer

CoqHammer (Czajka and Kaliszyk, JAR 2018) is a mature hammer combining premise selection, translation to external ATPs (Vampire, E, Z3), and proof reconstruction. Its `sauto` tactic provides general proof search based on a CIC inhabitation procedure. CoqHammer is practically effective for first-order reasoning and simple inductive types but never attempts induction by design.

CoqHammer's premise selection uses traditional ML features (term frequency, symbol overlap) rather than neural models. This contrasts with LeanHammer (2025), which integrates neural premise selection achieving 72.7% Recall@32 on Mathlib versus MePo's 42.1%.

**Status**: Mature and widely used, but its architecture predates the neural revolution in premise selection.

### Tactician (Graph2Tac)

Tactician (Blaauwbroek et al., ICLR 2024) is a tactic learner and prover for Coq using a graph neural network architecture (Graph2Tac):

- Builds hierarchical graph representations of formal mathematical concepts
- Assigns embeddings to new definitions in an online manner during interactive proof development
- Achieves 26.1% of theorems proved fully automatically; combined with CoqHammer, 56.7%
- The GNN's online learning and the k-NN solver's exploitation of proof-level locality are highly complementary

Graph2Tac is notable for operating natively on Coq's dependency structure rather than treating proof states as flat text. It is the most architecturally sophisticated AI tool built specifically for Coq.

**Status**: Strong research tool with niche adoption in the community.

### CoqPilot

CoqPilot (JetBrains, 2024) is a VS Code plugin for LLM-based proof generation:

- Collects `admit` holes in the proof script
- Generates candidate completions via LLMs and non-ML methods
- Checks candidates against Coq before presenting

**Status**: Early-stage. Limited scope compared to LeanCopilot's tighter integration (suggest_tactics, search_proof, select_premises all verified in-IDE).

### AutoRocq

AutoRocq (2025) is an LLM agent for Rocq that performs autonomous proving, including context analysis and query generation. It demonstrates the viability of agentic approaches where the LLM interacts with the proof assistant iteratively.

**Status**: Research prototype.

### Proverbot9001

Proverbot9001 is an RNN-based tactic prediction system using engineered proof state features.

**Status**: Research prototype; limited adoption.

---

## 3. Training Data Infrastructure for Coq

### SerAPI

SerAPI (Gallego Arias, 2016) is a machine-to-machine interface for Coq that serializes internal OCaml datatypes to JSON/S-expressions. It provides the deepest serialization available for any proof assistant but has significant practical limitations:

- **Version locking**: Requires specific Coq and OCaml version combinations. Each new Coq release may require SerAPI updates.
- **OCaml expertise**: Using SerAPI effectively requires knowledge of Coq's internal representation and OCaml ecosystem tooling.
- **No incremental tracing**: Cannot trace changes to a proof development without reprocessing the entire project.
- **No premise annotations**: Does not record which lemmas, definitions, and hypotheses were actually used by each tactic application.

### CoqGym

CoqGym (Yang and Deng, ICML 2019) is a learning environment with 71,000 proofs from 123 Coq projects:

- Uses SerAPI for feature extraction
- Extracts environment, local context, goals, tactics, and proof trees
- Provides a structured JSON format for proof states

**Limitations**: Pinned to Coq 8.9+; has not been fundamentally updated since 2019. No equivalent of LeanDojo's continuously updated benchmarks, incremental tracing, or gym-like interactive environment for RL-style training.

### coq-lsp

coq-lsp exposes proof state information via LSP protocol extensions, designed for IDE communication. It provides some of the building blocks for training data extraction (proof states, incremental checking) but is not designed as an ML pipeline tool.

### Comparison with Lean 4

Lean's training data infrastructure is substantially more mature:

| Capability | Lean 4 (LeanDojo) | Coq/Rocq |
|------------|-------------------|----------|
| Proof state extraction at every tactic step | Yes (v2, NeurIPS MathAI 2025) | SerAPI (version-locked, manual) |
| Fine-grained premise annotations | Yes (per-tactic) | Not available |
| Incremental tracing | Yes | Not available |
| Gym-like interactive environment | Yes (observe-submit-feedback loop) | Not available |
| Continuously updated benchmarks | 122K+ theorems, actively maintained | CoqGym (71K, frozen at 2019) |
| Dataset management and versioning | Built-in | Manual |
| Additional extraction tools | lean-training-data, LEAN-GitHub | None beyond SerAPI |

This infrastructure gap is the root cause of Coq's AI tooling lag: without modern training data extraction, every Coq-focused AI project must independently solve the data problem, leading to duplicated effort and incompatible datasets.

---

## 4. Premise Selection and Retrieval for Coq

### Current State

Coq's premise selection capabilities are limited:

- **CoqHammer**: Uses traditional ML features (term frequency, symbol overlap). Effective but predates neural methods.
- **Tactician (Graph2Tac)**: Uses graph neural networks for online premise representation. Architecturally sophisticated but niche.
- **Built-in `Search`**: Purely syntactic pattern matching. No semantic or embedding-based retrieval.

### Lean 4 Comparison

Lean has multiple neural premise selection systems:

- **ReProver**: ByT5 dual-encoder contrastive retrieval over Mathlib (NeurIPS 2023).
- **LeanHammer premise selector**: Encoder-only transformer, 72.7% Recall@32 (2025). Outperforms both MePo (42.1%) and ReProver (38.7%).
- **REAL-Prover (LeanSearch-PS)**: Fine-tuned E5-mistral-7b-instruct with hard negative mining. Shows +12pp on FATE-M with retrieval.
- **Lean Finder**: Semantic search aligned with user intents, 81.6% upvote rate in arena testing (ICML 2025).
- **Graph-augmented selection**: RGCN over dependency graphs, +26% Recall@10 over ReProver baseline.
- **Tree-based methods**: Training-free structural approaches competitive with neural methods.

### Key Research Finding: The Retrieval Bottleneck

Research on library learning (LEGO-Prover, NeurIPS 2024; follow-up 2025) found that AI-generated lemmas are almost never reused across problems. Of 20,000+ generated lemmas, exactly one was reused, and only once. This suggests that retrieval from existing curated libraries (like MathComp) is more critical than retrieval from dynamically generated libraries.

The implication for Coq: building effective retrieval over Coq's existing library ecosystem (standard library, MathComp, Iris, CompCert support libraries) is likely more impactful than systems that generate and attempt to reuse new lemmas.

---

## 5. Proof Search Strategies Relevant to Coq

### Best-First Search

BFS-Prover (ACL 2025) demonstrated that best-first search with a well-trained policy model can outperform MCTS variants without requiring a separate value model. This insight is relevant for Coq tool development: a strong policy model shifts the pruning burden from explicit value functions to implicit ones embedded in the policy, simplifying the overall architecture.

### Aesop's Rule Classification (Lean-specific but instructive)

Aesop (CPP 2023) classifies tactics into safe, unsafe, and normalization categories, providing deterministic pruning layered over heuristic pruning. Coq lacks an equivalent configurable proof search framework -- its built-in `auto` and `eauto` are less extensible than Aesop's user-registered rule sets with priorities.

### Value Functions and Progress Estimation

LeanProgress (ICLR 2025) predicts remaining proof steps, enabling early termination of unpromising searches. This technique is proof-assistant-agnostic in principle but requires proof state extraction infrastructure to train on -- infrastructure that Coq currently lacks.

### Diversity-Based Search

CARTS (ICLR 2025) and 3D-Prover (NeurIPS 2025) demonstrate that diversity-aware tactic selection significantly improves search efficiency by avoiding near-duplicate exploration. These techniques could benefit Coq proof search but require integration points that do not currently exist.

---

## 6. Cross-System Translation Involving Coq

The type-theoretic similarity between Coq (CIC) and Lean 4 (a CIC variant) makes cross-system translation more tractable than between more distant foundations. Active projects:

- **Babel-formal** (2025): LLM-based source-to-source translation between Lean and Rocq.
- **coq_lean_translation** (Atlas Computing): Definition and proof translation. Available on Lean Reservoir.
- **PROOFWALA** (2025): Unified framework for interacting with and collecting data from both Coq and Lean 4.

All are early-stage or research-only. No production-quality translation tool exists.

---

## 7. The Coq AI Tooling Gap: Summary

| Dimension | Lean 4 | Coq/Rocq | Gap Severity |
|-----------|--------|----------|-------------|
| Training data extraction | LeanDojo v2 (mature, incremental, premise annotations) | SerAPI + CoqGym (aging, manual, version-locked) | High |
| Gym-like interactive environment | LeanDojo (observe-submit-feedback) | None | High |
| Copilot / tactic suggestion | LeanCopilot, llmstep (multiple, integrated) | CoqPilot (early-stage) | High |
| Neural premise selection | LeanHammer (72.7% R@32), ReProver, REAL-Prover | CoqHammer (traditional ML only) | High |
| Semantic library search | Moogle, Loogle, Lean Finder, LeanSearch, LeanExplore, exact? | Built-in `Search` (syntactic only) | High |
| Proof progress estimation | LeanProgress (ICLR 2025) | None | Medium-High |
| Extensible proof search | Aesop (user-registered rules, priorities) | auto/eauto (limited configurability) | Medium |
| Proof visualization widgets | ProofWidgets4 (React, arbitrary UIs) | None | High |

The root cause is infrastructure: without modern extraction, premise annotation, and interaction protocols, downstream AI tools for Coq cannot be built at the same level of integration that Lean enjoys.

---

## References

Blaauwbroek, L. et al. "Graph2Tac: Learning to Prove with GNNs." ICLR 2024.

Cao, H. et al. "Library Learning Doesn't: The Curious Case of the Single-Use Library." NeurIPS 2024.

Czajka, L. and Kaliszyk, C. "Hammer for Coq: Automation for Dependent Type Theory." JAR 2018.

Gallego Arias, E. "SerAPI: Machine-Friendly Coq API." 2016.

Gallego Arias, E. "coq-lsp: A Language Server for the Coq/Rocq Prover." 2023.

Limperg, J. and From, A.H. "Aesop: White-Box Best-First Proof Search for Lean." CPP 2023.

Lu, Y. et al. "Lean Finder: Semantic Search for Mathlib." ICML 2025.

Mikula, M. et al. "Premise Selection for a Lean Hammer." 2025.

Song, P. et al. "Towards Large Language Models as Copilots for Theorem Proving in Lean." NeuS 2025.

Yang, K. and Deng, J. "Learning to Prove Theorems via Interacting with Proof Assistants." ICML 2019.

Yang, K. et al. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." NeurIPS 2023.

Yang, K. et al. "LeanDojo v2: Theorem Proving in the Wild." NeurIPS MathAI 2025.

Xin, H. et al. "BFS-Prover: Scalable Best-First Tree Search." ACL 2025.

"CARTS: Advancing Theorem Proving with Diversity-Driven Tactic Selection." ICLR 2025.

"3D-Prover: Diversity Driven Document-Level Proof Generation." NeurIPS 2025.

"LeanProgress: Guiding Search via Distance Estimation." ICLR 2025.

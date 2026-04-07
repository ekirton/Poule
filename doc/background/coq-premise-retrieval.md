# Premise Selection and Lemma Retrieval for Coq/Rocq (March 2026)

A survey of premise selection and lemma retrieval methods as they apply to the Coq/Rocq proof assistant, covering what exists for Coq today, the state of the art in Lean and Isabelle, and the research findings that inform future tool development.

---

## 1. The Premise Selection Problem

Given a proof state (or theorem statement), premise selection ranks all available premises in a formal library by their relevance for proving the current goal, returning the top-k candidates. Key challenges:

- **Scale**: Lean's Mathlib exceeds 210,000 theorems; Isabelle's AFP contains 433,000+ unique premises. Coq's libraries are smaller but still contain tens of thousands of definitions across the standard library, MathComp, Iris, and domain-specific packages.
- **Distributional shift**: User-defined local lemmas and newly added library content may not appear in training data, requiring generalization to unseen premises.
- **Structural vs. semantic gap**: Formal expressions encode both syntactic structure and mathematical semantics; effective retrieval must capture both.
- **Dependent type theory complications**: In CIC-based systems like Coq, definitional equality means relevant premises may not appear syntactically in a proof.
- **Interactive latency**: Practical tools must return results within seconds.

---

## 2. What Exists for Coq Today

### Built-in Search Commands

Coq provides `Search`, `SearchPattern`, and `SearchRewrite` commands for syntactic pattern matching over definitions in scope. These are useful for exact name or type pattern lookups but have no semantic understanding, no natural language interface, and no ranking beyond syntactic relevance.

### CoqHammer Premise Selection

CoqHammer's premise selection uses traditional ML features:
- Symbol overlap between goal and candidate premises
- Term frequency weighting
- Transitive relevance (premises sharing symbols with already-selected premises)

This approach is fast and deterministic but does not capture semantic relationships that lack surface-level syntactic overlap. It predates the neural revolution in premise selection.

### Graph2Tac (Tactician)

Graph2Tac (ICLR 2024) builds hierarchical graph representations of Coq mathematical concepts:
- Assigns embeddings to definitions (including theorems) in an online manner
- GNN architecture captures structural relationships in the dependency graph
- Combined with a k-NN solver exploiting proof-level locality, achieves 1.27x improvement over individual performance
- Both the GNN and k-NN approaches outperform CoqHammer, Proverbot9001, and a transformer baseline by at least 1.48x

Graph2Tac's key insight is that k-NN (exploiting proof-level locality) and GNN (exploiting definition-level structure) are highly complementary. This is the most architecturally sophisticated premise selection system built for Coq.

**Limitation**: Niche adoption. Requires Tactician's infrastructure to run.

---

## 3. State of the Art in Other Systems

### Neural Contrastive Retrieval

The dominant paradigm for premise selection is dense contrastive retrieval: encode proof states and premises into a shared embedding space, then retrieve by cosine similarity.

**ReProver** (LeanDojo, NeurIPS 2023): ByT5 dual-encoder for Lean 4. Established the core paradigm for the field. 38.7% Recall@32 on Mathlib.

**Magnushammer** (ICLR 2024, Isabelle): Two-stage retrieve-then-rerank. Contrastive select (top 1,024 from 433K premises) followed by cross-attention rerank. 59.5% on PISA, substantially outperforming Sledgehammer's symbolic selection (38.3%).

**LeanHammer premise selector** (2025): Encoder-only transformer with masked contrastive loss. 72.7% Recall@32 on Mathlib, dramatically outperforming both MePo (42.1%) and ReProver (38.7%). Handles dependent type theory complications by extracting explicit premises from `rw` and `simp` calls. Approximately 1-second latency.

**Custom BERT retriever** (2025): WordPiece tokenizer trained specifically on formal language corpora. 38.20% Recall@5 vs. ReProver's 28.78%. Key insight: formal-language-specific tokenization significantly improves embedding quality.

### Graph-Augmented Selection

**RGCN-augmented retrieval** (NeurIPS 2025 submission): Combines ReProver's text encoder with a Relational Graph Convolutional Network over a heterogeneous dependency graph. +26% Recall@10, +34% Recall@1 over ReProver baseline. Confirms that dependency graph structure encodes important signal that pure text-based embeddings miss.

### Structural Methods

**Tree-based premise selection** (NeurIPS 2025): Training-free approach using Common Subexpression Elimination, Weisfeiler-Lehman kernel for coarse screening, and Tree Edit Distance for fine ranking. Competitive with neural methods without requiring training data or GPU compute. Demonstrates that structural information in formal expressions contains rich retrieval signal.

### Symbolic Baselines

**MePo** (Meng-Paulson): Symbol-overlap heuristic used in Sledgehammer. Achieves 42.1% Recall@32 on Mathlib -- better than ReProver (38.7%) at the same cutoff. Remains a strong baseline.

**SInE** (Hoder-Voronkov): Trigger-based axiom selection via transitive symbol-overlap closure. Fast, deterministic, competitive despite simplicity.

### Hybrid Approaches

LeanHammer achieves its best results by taking the union of neural and MePo selections, capturing a 21% improvement over neural-only. The insight: neural and syntactic selectors make complementary errors. Neural methods miss syntactically obvious premises; syntactic methods miss semantically related but syntactically dissimilar premises.

---

## 4. Retrieval-Augmented Proving

Several systems integrate retrieval directly into the proving pipeline:

**REAL-Prover** (2025): Fine-tuned E5-mistral-7b-instruct for Lean 4 premise retrieval. Ablation shows +12pp on college-level mathematics (FATE-M) with retrieval, suggesting retrieval is most valuable when problems require obscure library lemmas rather than common tactics.

**Lean Finder** (ICML 2025): Semantic search aligned with how mathematicians actually search. Fine-tuned on synthesized user queries, informalized statements, proof states, and formal statements (1.4M+ query-code pairs). 81.6% upvote rate in arena testing vs. 56.9% for LeanSearch. Demonstrates the importance of aligning retrieval with user intent.

**Seed-Prover 1.5** (ByteDance, 2025): Maintains per-problem lemma pools with dynamic scoring (proof-rate, semantic relevance, proof length). RL training progressively internalizes retrieval knowledge -- later checkpoints make fewer search calls while maintaining performance.

**ProofFusion** (accepted FSE 2026): Adaptive retrieval-augmented reasoning for theorem proving. The system dynamically adjusts its retrieval strategy based on the difficulty and type of the current proof goal, using more aggressive retrieval for harder goals and lighter-weight retrieval for goals that are likely to yield to direct tactic application. The key insight is that retrieval is not free: each call adds latency and context window consumption to proof search. An adaptive system that retrieves more when the proof is stuck and less when it is making progress allocates the retrieval budget more efficiently.

---

## 5. Library Learning: The Reuse Problem

A critical research finding for anyone building premise retrieval systems:

**LEGO-Prover** (ICLR 2024) proposed growing a reusable lemma library during proving. Over the course of solving miniF2F, it generated 20,000+ lemmas.

**"Library Learning Doesn't"** (NeurIPS 2024) found that of those 20,000+ lemmas, exactly one was reused across problems, and only once. Disabling cross-problem sharing reduced performance by only one problem on a validation subset. A follow-up study (2025) found no evidence of even "soft reuse" (reuse by modifying relevant examples).

This finding indicates that retrieval from curated, human-authored libraries (standard library, MathComp, Iris) is more valuable than retrieval from dynamically generated lemma stores. AI-generated lemmas exhibit negligible cross-problem reuse, while existing library coverage remains the dominant factor in retrieval-augmented proving.

---

## 6. Retrieval vs. Internalization

The most powerful proving systems of 2025-2026 (AlphaProof, DeepSeek-Prover-V2, Goedel-Prover-V2) achieve their best results without explicit retrieval modules, instead internalizing library knowledge through massive pretraining and RL.

However, evidence for continued relevance of explicit retrieval:
- REAL-Prover ablations: +12pp on FATE-M with retrieval
- LeanHammer: Enables practical interactive use at 1-second latency
- Seed-Prover 1.5: RL training progressively internalizes retrieval, suggesting retrieval is a useful scaffold even for systems that eventually transcend it
- Compute constraints: Not every user has access to 671B-parameter models. Explicit retrieval enables smaller models to access library knowledge they cannot internalize

For Coq specifically, where AI models have far less training data than for Lean/Mathlib, explicit retrieval is likely to remain essential for the foreseeable future.

---

## 7. Open Problems Relevant to Coq

### Coq-Specific Tokenization

The finding that formal-language-specific tokenizers improve embedding quality (Section 3) suggests that Coq-specific tokenizers (handling Coq notation, MathComp conventions, and Ltac idioms) could substantially improve retrieval quality. No such tokenizer exists.

### Online Adaptation

Graph2Tac demonstrates the value of adapting embeddings as new definitions are added during interactive development. Extending this to dense neural retrievers (which currently require offline embedding computation) is an open challenge. Coq's interactive development workflow makes this especially relevant.

### Cross-Library Retrieval

No current system retrieves premises across proof assistant boundaries. As Coq-Lean translation tools mature, cross-library retrieval (finding a relevant Mathlib lemma when proving in Coq, or vice versa) could become valuable.

### Dependency Graph Exploitation

The +26% improvement from adding graph structure (Section 3) and the competitive performance of training-free tree-based methods suggest that Coq's dependency structure is underexploited by current tools. Coq's kernel tracks dependencies precisely; this information could feed directly into retrieval systems.

### User Intent Alignment

Lean Finder's success demonstrates that aligning retrieval with actual user search patterns is a significant opportunity. No equivalent study of how Coq users search for lemmas has been conducted.

---

## References

Blaauwbroek, L. et al. "Graph2Tac: Online Representation Learning of Formal Math Concepts." ICML 2024.

Cao, H. et al. "Library Learning Doesn't: The Curious Case of the Single-Use Library." NeurIPS 2024.

Berlot-Attwell, I. et al. "LLM Library Learning Fails: A LEGO-Prover Case Study." 2025.

Czajka, L. and Kaliszyk, C. "Hammer for Coq." JAR 2018.

"ProofFusion: Adaptive Retrieval-Augmented Reasoning for Theorem Proving." Accepted FSE 2026.

Hoder, K. and Voronkov, A. "Sine Qua Non for Large Theory Reasoning." CADE 2011.

Lu, Y. et al. "Lean Finder: Semantic Search for Mathlib." ICML 2025.

Meng, J. and Paulson, L.C. "Lightweight Relevance Filtering for Machine-Generated Resolution Problems." JAL 2009.

Mikula, M. et al. "Premise Selection for a Lean Hammer." 2025.

Mikula, M. et al. "Magnushammer: A Transformer-Based Approach to Premise Selection." ICLR 2024.

Petrovcic, J. et al. "Combining Textual and Structural Information for Premise Selection in Lean." 2025.

"Learning an Effective Premise Retrieval Model for Efficient Mathematical Formalization." 2025.

"REAL-Prover: Retrieval Augmented Lean Prover." 2025.

Wang, Z. et al. "Tree-Based Premise Selection for Lean4." NeurIPS 2025.

Xin, H. et al. "LEGO-Prover: Neural Theorem Proving with Growing Libraries." ICLR 2024.

Yang, K. et al. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." NeurIPS 2023.

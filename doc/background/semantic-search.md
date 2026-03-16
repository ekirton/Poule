# Semantic Search for Coq/Rocq Libraries: State of the Art (March 2026)

A survey of semantic search architectures, retrieval methods, and delivery mechanisms for formal libraries. Synthesized from research literature, the Lean ecosystem's deployed search tools, and emerging patterns in LLM-augmented retrieval.

Cross-references:
- [coq-premise-retrieval.md](coq-premise-retrieval.md) — Premise selection methods
- [coq-ecosystem-tooling.md](coq-ecosystem-tooling.md) — Section 4 (Library Search)

---

## 1. Lean's Deployed Search Tools: Lessons Learned

Lean 4 has five actively maintained search tools, providing the closest existence proof for semantic search over a formal math library. Their architectures and relative performance are instructive.

| Tool | Architecture | Embedding Model | Index | Arena Top-1 Rate |
|------|-------------|----------------|-------|-----------------|
| **Moogle** | Dense retrieval over informalized Mathlib | Unknown (proprietary) | Unknown | 12% (declining) |
| **LeanSearch** | Dense retrieval + LLM query augmentation | E5-mistral-7b-instruct | ChromaDB | 46% |
| **LeanExplore** | Hybrid BM25 + dense retrieval + PageRank | bge-base-en-v1.5 (109M params) | FAISS | 55% |
| **Lean Finder** | Contrastive + DPO-trained retrieval aligned with user intent | DeepSeek-Prover-based | Custom | 82% user preference |
| **Loogle** | Formal pattern matching (not semantic) | N/A | N/A | N/A (different task) |

**Key findings from Lean's experience:**

1. **User intent alignment dominates model size.** Lean Finder (ICML 2025) achieves 82% preference despite using a smaller model than LeanSearch's E5-mistral-7b, because it was trained on synthesized user queries (informalized statements, proof states, community discussions) rather than formal-to-formal retrieval. Lu et al. generated 1.4M+ query-code pairs for training.

2. **Hybrid retrieval beats pure dense retrieval.** LeanExplore's combination of BM25 (lexical), dense embeddings (semantic), and PageRank (graph authority) outperforms LeanSearch's pure dense approach despite using a much smaller embedding model (109M vs 7B parameters).

3. **Lightweight models suffice for the corpus scale.** Mathlib has ~210K declarations. Coq's standard library + MathComp + commonly used packages would be similar in scale. At this scale, lightweight models (bge-base, 109M params) with hybrid scoring are competitive with heavyweight models.

4. **Multi-facet indexing is standard.** All successful systems index multiple representations of each declaration: formal statement, informalized natural-language description, type signature, docstring, file path metadata. LeanExplore's "StatementGroups" unify related compiled declarations into single searchable units.

5. **The lean-lsp-mcp server** bridges all five search engines plus LSP tools into a single MCP interface, allowing LLMs to query any search engine and cross-reference results. This is the closest deployed precedent for the MCP-based architecture proposed for Coq.

---

## 2. Retrieval Architectures

### 2.1 Dense Contrastive Retrieval (Dominant Paradigm)

Encode queries (proof states, natural language) and documents (lemma statements) into a shared embedding space; retrieve by cosine similarity.

| System | Encoder | Domain | Recall@32 | Notes |
|--------|---------|--------|-----------|-------|
| ReProver (NeurIPS 2023) | ByT5 dual-encoder | Lean 4 | 38.7% | Established the paradigm |
| LeanHammer selector (2025) | Encoder-only transformer, masked contrastive loss | Lean 4 | 72.7% | Current SOTA for premise selection |
| Custom BERT (Zhu et al. 2025) | BERT with formal-language WordPiece tokenizer | Lean 4 | 38.2% R@5 | Key insight: domain-specific tokenization matters |
| Magnushammer (ICLR 2024) | Two-stage: contrastive select → cross-attention rerank | Isabelle | 59.5% (PISA) | Retrieve-then-rerank architecture |
| REAL-Prover (2025) | E5-mistral-7b-instruct, hard negative mining | Lean 4 | N/A | +12pp on FATE-M with retrieval |

Dense contrastive retrieval is well-understood and effective. The main Coq-specific challenge is the absence of training data (premise annotations linking proof states to used lemmas). Approaches explored in adjacent work include: (a) bootstrapping from symbolic selection as weak labels, (b) cross-lingual transfer from models trained on other proof assistants, (c) informalization combined with general embedding models to avoid fine-tuning entirely.

### 2.2 Graph-Augmented Retrieval

Combine dense text embeddings with graph neural network message passing over dependency graphs.

**RGCN-augmented retrieval** (Petrovcic et al., NeurIPS 2025 submission): Heterogeneous dependency graph with 3 edge types (signature-local-hypotheses, signature-goal, proof-dependency). RGCN propagates information across the graph, then proof states are treated as temporary query nodes. Results: +34% Recall@1, +26% Recall@10, +25% MRR over ReProver baseline.

**Graph2Tac** (Blaauwbroek et al., ICML 2024): GNN over Coq's dependency graph with online adaptation for new definitions. Combined GNN + k-NN achieves 1.27x over individual solvers, 1.48x over CoqHammer. The k-NN component exploits proof-level locality (nearby definitions in the dependency graph are more likely to be relevant). This is the only graph-based system built specifically for Coq.

These results indicate that graph structure encodes 25-34% additional retrieval signal beyond what text embeddings capture. Coq's kernel tracks dependencies precisely, making this information directly available for graph-based retrieval approaches.

### 2.3 Structural / Tree-Based Methods

**Tree-based premise selection** (Wang et al., NeurIPS 2025): Training-free approach using Common Subexpression Elimination, Weisfeiler-Lehman kernel for coarse screening, and Tree Edit Distance for fine ranking. Competitive with neural methods without requiring training data or GPU compute.

This result demonstrates viability as a zero-training baseline and as a complementary signal to embedding-based retrieval at low computational cost.

### 2.4 Hybrid Neural + Symbolic

**LeanHammer** achieves its best results by taking the union of neural and MePo (symbol-overlap) selections: 21% improvement over neural-only. Neural and syntactic selectors make complementary errors.

This result confirms that symbolic premise selection (such as CoqHammer's) and neural retrieval make complementary errors. Union-based fusion is simple and effective.

### 2.5 ColBERT / Late Interaction (Unexplored for Formal Math)

No published work applies ColBERT-style late interaction to formal math retrieval. ColBERT's token-level MaxSim scoring is theoretically well-suited to formal math's precise symbol-level semantics — a shared symbol between query and premise contributes to similarity even if surrounding context differs. Jina-ColBERT-v2 (560M params, 8K context) is the strongest available base model. This remains an unexplored gap in the literature.

---

## 3. Embedding Models and Tokenization

### 3.1 General-Purpose Models (No Fine-Tuning Required)

| Model | Size | Strengths | Weaknesses for Formal Math |
|-------|------|-----------|---------------------------|
| E5-mistral-7b-instruct | 7B | Highest quality general embeddings; used by LeanSearch (nDCG@20=0.733) | Large; slow inference; generic tokenizer |
| bge-base-en-v1.5 | 109M | Good quality/size ratio; used by LeanExplore | No formal math awareness |
| ByT5 | Varies | Byte-level tokenization handles formal syntax natively; used by ReProver | Slow encoding due to byte-level processing |
| all-MiniLM-L6-v2 | 22M | Very lightweight | Likely insufficient for formal math nuance |

### 3.2 Domain-Specific Approaches

**Formal-language WordPiece tokenizer** (Zhu et al., 2025): BERT pre-trained from scratch on formal corpora with a Lean-specific WordPiece vocabulary. Achieves 38.2% Recall@5 vs. ReProver's 28.8%. Key insight: standard tokenizers fragment formal identifiers (e.g., `Nat.add_comm` becomes multiple subwords); domain-specific tokenizers preserve them as single tokens.

**DeepSeek-Prover-based embeddings** (Lean Finder): Fine-tuned from a model already pre-trained on formal math, then further aligned with DPO using human preference data. Achieves the highest user satisfaction (82%).

**Coq-specific considerations:** Coq's notation system (e.g., `_ + _ = _ + _`), MathComp's conventions (e.g., `ssrnat`, `fingroup`), and Ltac idioms are all tokenization challenges. A Coq-specific tokenizer handling these conventions would likely yield similar gains to those observed for Lean.

### 3.3 Informalization as a Bridge

Several successful systems use LLM-generated natural language descriptions of formal statements as an intermediate representation:
- Lean Finder generates informalized descriptions as training queries
- LeanSearch augments user queries with LLM-generated formal-language expansions
- Moogle indexes informalized Mathlib content

This approach enables semantic search without domain-specific fine-tuning: index informalized descriptions with a general-purpose embedding model.

---

## 4. Knowledge Graph Approaches

### 4.1 MMLKG: The Only Formal Math Knowledge Graph

MMLKG (Nature Scientific Data, 2023) is the only published knowledge graph over a formal math library:
- **Scope:** Mizar Mathematical Library (1,415 articles, 13K definitions, 65K theorems)
- **Technology:** Neo4j 5.9+ with GraphML import
- **Schema:** SKOS + Dublin Core. Node types: predicates, adjectives, types, functors, structures, theorems, definitions. Edge types: MEMBER (hierarchical), RELATED (usage), BROADER (type inheritance), SAMEAS (synonymy)
- **Limitations:** Mizar only. Proof steps not modeled. SKOS thesaurus model less expressive than full ontologies.

**No equivalent exists for Coq, Lean, or Isabelle.** This is a clear gap.

### 4.2 GraphRAG for Mathematics: A Cautionary Finding

Microsoft's GraphRAG (entity-extraction → community-hierarchy → community-summary) was evaluated on mathematical text in GraphRAG-Bench (2025): **all GraphRAG methods degraded the LLM's generation accuracy on mathematics.** The entity-extraction paradigm loses the precise logical structure that makes formal proofs useful.

This finding indicates that standard GraphRAG is a poor fit for formal math. The entity-extraction paradigm loses the precise logical structure that formal proofs require; effective formal-math knowledge graphs in existing work (MMLKG, Graph2Tac) are constructed from kernel-level dependency and type information rather than NLP-based entity extraction.

### 4.3 Potential Knowledge Graph Architecture

Based on patterns from MMLKG and Graph2Tac, researchers have identified graph primitives relevant to formal math knowledge graphs that differ from standard GraphRAG entity-extraction approaches.

**Research suggests relevant node types include:** Definitions, lemmas, theorems, tactics, modules, sections, type classes, instances, notations. MMLKG annotates nodes with formal statements and type signatures; Graph2Tac demonstrates the value of embedding vectors assigned to each node. Additional metadata (source location, informalized descriptions) follows the multi-facet indexing pattern observed in Lean's search tools (Section 1).

**Based on Coq's kernel-level information, researchers have identified relevant edge types:**
- `DEPENDS_ON`: Definition X references definition Y (from Coq's dependency tracking)
- `PROVES_USING`: Proof of theorem X uses lemma Y (from premise annotations, if available)
- `HAS_TYPE`: Term X has type T
- `INSTANCE_OF`: Instance X is an instance of type class C
- `IN_MODULE`: Definition X is in module M
- `REWRITES_TO`: Lemma X can rewrite term pattern P to Q
- `UNFOLDS_TO`: Definition X unfolds to body B

**Technology options explored in existing work:**
- **Neo4j**: Used by MMLKG. Native vector search since 5.x enables hybrid graph+vector queries in Cypher. Well-documented, large community.
- **TypeDB**: Type-theoretic foundations (entities, relations with polymorphic inheritance) are conceptually aligned with dependent type theory, but no formal math precedent.
- **SQLite + custom graph layer**: Used by Tactician internally. Lightest weight; sufficient for the corpus scale; no external dependencies.
- **In-memory graph + FAISS**: Fastest for small corpora. No persistence overhead.

### 4.4 Hybrid Graph + Vector Retrieval: An Open Research Direction

No deployed system combines all three major retrieval signals for formal math:

1. **Vector retrieval** (embedding similarity) for semantic matching
2. **Graph traversal** (dependency walks) for structural relevance
3. **Symbolic matching** (type unification, symbol overlap) for syntactic precision

Evidence from existing work suggests these signals are complementary:
- RGCN work: +26% from adding graph structure to vectors
- LeanHammer: +21% from adding symbolic to neural
- Tree-based methods: competitive with neural using structure alone

Open questions in this area include fusion strategy -- how to weight and combine heterogeneous retrieval signals. Approaches explored in adjacent domains include learned score fusion, reciprocal rank fusion, and LLM-based reranking of candidates from multiple channels.

---

## 5. Open Questions and Research Gaps

### 7.1 No Coq-Specific Embedding Model Exists
All current formal-math embedding models are trained on Lean/Mathlib data. Transfer to Coq is plausible (similar underlying type theory) but unvalidated. A Coq-specific tokenizer handling Coq notation, MathComp conventions, and Ltac idioms would likely improve embedding quality significantly (cf. the 33% R@5 improvement from Lean-specific tokenization).

### 7.2 No Coq Premise Annotations Exist
Fine-tuning retrieval models requires premise annotations (which lemmas were actually used in each proof step). Coq lacks this data. Workarounds: (a) weak supervision from CoqHammer's selections, (b) cross-system transfer from Lean models, (c) informalization-based approach that avoids fine-tuning entirely.

### 7.3 ColBERT for Formal Math Is Unexplored
ColBERT's token-level MaxSim scoring should be well-suited to formal math's symbol-level semantics. No published work has evaluated this. Jina-ColBERT-v2 is the strongest available base model.

### 7.4 Online Adaptation
Graph2Tac demonstrates that online adaptation (updating embeddings as new definitions are added during interactive development) is highly valuable. Extending this to a general-purpose search index — re-embedding and re-indexing as the user develops their project — is an open challenge.

### 7.5 User Intent for Coq Is Unstudied
Lean Finder's success comes from aligning with how users actually search. No equivalent study of Coq user search behavior exists. The MCP approach partially addresses this: the LLM can interpret diverse user intents without training data, but the underlying retrieval still benefits from intent-aware training.

---

## References

Blaauwbroek, L. et al. "Graph2Tac: Online Representation Learning of Formal Math Concepts." ICML 2024.

Blaauwbroek, L. et al. "The Tactician's Web of Large-Scale Formal Knowledge." 2024.

Lu, Y. et al. "Lean Finder: Semantic Search for Mathlib." ICML 2025.

Mikula, M. et al. "Premise Selection for a Lean Hammer." 2025.

Mikula, M. et al. "Magnushammer: A Transformer-Based Approach to Premise Selection." ICLR 2024.

Petrovcic, J. et al. "Combining Textual and Structural Information for Premise Selection in Lean." 2025.

Thompson, S. et al. "Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification." ICSE 2025.

Wang, Z. et al. "Tree-Based Premise Selection for Lean4." NeurIPS 2025.

Yang, K. et al. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." NeurIPS 2023.

Zhu, R. et al. "Learning an Effective Premise Retrieval Model for Efficient Mathematical Formalization." 2025.

MMLKG. "Mizar Mathematical Library Knowledge Graph." Nature Scientific Data, 2023.

AutoMathKG. "The Automated Mathematical Knowledge Graph Based on LLM and Vector." 2025.

GraphRAG-Bench. "Evaluating Graph RAG Methods." 2025.

A-RAG. "Agentic Retrieval-Augmented Generation." 2026.

LeanSearch. GitHub: reaslab/LeanSearch.

lean-lsp-mcp. "MCP Server for Lean 4 LSP and Search Engines."

RocqStar. "JetBrains Research — Similarity-Driven Retrieval for Coq/Rocq."

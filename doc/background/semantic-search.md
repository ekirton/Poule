# Semantic Search for Coq/Rocq Libraries: State of the Art (March 2026)

A survey of semantic search architectures, retrieval methods, and delivery mechanisms relevant to building a semantic search system for Coq/Rocq formal libraries. Synthesized from research literature, the Lean ecosystem's deployed search tools, and emerging patterns in LLM-augmented retrieval.

Cross-references:
- [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) — Gap 1 (Semantic Lemma Search)
- [coq-premise-retrieval.md](coq-premise-retrieval.md) — Premise selection methods
- [coq-ecosystem-tooling.md](coq-ecosystem-tooling.md) — Section 4 (Library Search)

---

## 1. Lean's Deployed Search Tools: Lessons Learned

Lean 4 has five actively maintained search tools, providing the closest existence proof for what a Coq semantic search system should achieve. Their architectures and relative performance are instructive.

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

**Implications for Coq:** Dense contrastive retrieval is well-understood and effective. The main Coq-specific challenge is the absence of training data (premise annotations linking proof states to used lemmas). Options: (a) bootstrap from CoqHammer's symbolic selection as weak labels, (b) use cross-lingual transfer from Lean models, (c) use informalization + general embedding models without fine-tuning.

### 2.2 Graph-Augmented Retrieval

Combine dense text embeddings with graph neural network message passing over dependency graphs.

**RGCN-augmented retrieval** (Petrovcic et al., NeurIPS 2025 submission): Heterogeneous dependency graph with 3 edge types (signature-local-hypotheses, signature-goal, proof-dependency). RGCN propagates information across the graph, then proof states are treated as temporary query nodes. Results: +34% Recall@1, +26% Recall@10, +25% MRR over ReProver baseline.

**Graph2Tac** (Blaauwbroek et al., ICML 2024): GNN over Coq's dependency graph with online adaptation for new definitions. Combined GNN + k-NN achieves 1.27x over individual solvers, 1.48x over CoqHammer. The k-NN component exploits proof-level locality (nearby definitions in the dependency graph are more likely to be relevant). This is the only graph-based system built specifically for Coq.

**Implication:** Graph structure encodes 25-34% additional retrieval signal beyond what text embeddings capture. Coq's kernel tracks dependencies precisely — this information is directly available and should be exploited.

### 2.3 Structural / Tree-Based Methods

**Tree-based premise selection** (Wang et al., NeurIPS 2025): Training-free approach using Common Subexpression Elimination, Weisfeiler-Lehman kernel for coarse screening, and Tree Edit Distance for fine ranking. Competitive with neural methods without requiring training data or GPU compute.

**Implication:** Useful as a zero-training baseline and as a complementary signal. Could be combined with embedding-based retrieval at low cost.

### 2.4 Hybrid Neural + Symbolic

**LeanHammer** achieves its best results by taking the union of neural and MePo (symbol-overlap) selections: 21% improvement over neural-only. Neural and syntactic selectors make complementary errors.

**Implication:** CoqHammer's existing symbolic premise selection can serve as a complementary retrieval channel alongside any neural system. Union-based fusion is simple and effective.

### 2.5 ColBERT / Late Interaction (Unexplored for Formal Math)

No published work applies ColBERT-style late interaction to formal math retrieval. ColBERT's token-level MaxSim scoring is theoretically well-suited to formal math's precise symbol-level semantics — a shared symbol between query and premise should contribute to similarity even if surrounding context differs. Jina-ColBERT-v2 (560M params, 8K context) is the strongest available base model. **This is a clear research gap and opportunity.**

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

**Implication:** Standard GraphRAG is a poor fit for formal math. A formal-math knowledge graph must be constructed from the prover's kernel-level dependency and type information, not from NLP-based entity extraction.

### 4.3 What a Coq Knowledge Graph Could Look Like

A Coq-specific knowledge graph would differ fundamentally from standard GraphRAG:

**Nodes:** Definitions, lemmas, theorems, tactics, modules, sections, type classes, instances, notations. Each node annotated with: formal statement, type signature, source location, informalized description (LLM-generated), embedding vector.

**Edges (from kernel-level information):**
- `DEPENDS_ON`: Definition X references definition Y (from Coq's dependency tracking)
- `PROVES_USING`: Proof of theorem X uses lemma Y (from premise annotations, if available)
- `HAS_TYPE`: Term X has type T
- `INSTANCE_OF`: Instance X is an instance of type class C
- `IN_MODULE`: Definition X is in module M
- `REWRITES_TO`: Lemma X can rewrite term pattern P to Q
- `UNFOLDS_TO`: Definition X unfolds to body B

**Technology options:**
- **Neo4j** (most deployment-ready): Native vector search since 5.x enables hybrid graph+vector queries in Cypher. Well-documented, large community.
- **TypeDB**: Type-theoretic foundations (entities, relations with polymorphic inheritance) are conceptually aligned with dependent type theory, but no formal math precedent.
- **SQLite + custom graph layer**: Lightest weight; sufficient for the corpus scale; no external dependencies. Used by Tactician internally.
- **In-memory graph + FAISS**: Fastest for small corpora. No persistence overhead.

### 4.4 Hybrid Graph + Vector Retrieval

The most promising unexplored architecture for Coq semantic search combines:

1. **Vector retrieval** (embedding similarity) for semantic matching
2. **Graph traversal** (dependency walks) for structural relevance
3. **Symbolic matching** (type unification, symbol overlap) for syntactic precision

This three-signal fusion is supported by evidence:
- RGCN work: +26% from adding graph structure to vectors
- LeanHammer: +21% from adding symbolic to neural
- Tree-based methods: competitive with neural using structure alone

No deployed system combines all three signals. The challenge is fusion: how to weight and combine heterogeneous retrieval signals. Options include learned score fusion, reciprocal rank fusion, and LLM-based reranking of candidates from multiple channels.

---

## 5. Delivery Mechanism: MCP-Based Search with LLM Reasoning

### 5.1 The MCP Approach

The Model Context Protocol (MCP) allows LLMs to invoke external tools during reasoning. Exposing semantic search as an MCP server means:

- The LLM receives a user's natural-language query about Coq lemmas
- The LLM formulates one or more search tool calls (vector search, pattern search, graph traversal)
- The LLM receives raw results and applies **reasoning to filter, rerank, and explain** them
- The user gets curated, explained results rather than a raw ranked list

**This is architecturally distinct from both traditional search and LLM-as-reranker.** The LLM doesn't just rerank — it understands the user's intent, can reformulate queries, can cross-reference multiple search results, and can explain why a lemma is relevant to the user's goal.

### 5.2 Evidence Supporting LLM-as-Reasoning-Layer

1. **LLMs understand formal math.** Claude (Opus) has demonstrated the ability to read Coq lemma statements, explain their semantics in natural language, and answer questions about applicability — in offline testing and in general usage. This understanding can serve as a post-retrieval reasoning layer that no embedding model or reranker can replicate.

2. **Agentic retrieval outperforms single-shot.** A-RAG (Feb 2026) achieves 94.5% on HotpotQA by letting the LLM autonomously choose retrieval strategy (keyword, semantic, chunk-level) and iterate. PRISM separates precision and recall into an iterative loop (90.9% passage recall). The consensus is that LLM-guided iterative retrieval outperforms fixed pipelines.

3. **Specialized rerankers beat LLMs at pure reranking** — but LLMs excel at reasoning. Voyage AI's study found LLMs actually degraded reranking performance when paired with strong first-stage retrieval. The LLM's value is not in scoring relevance but in **understanding intent, reformulating queries, and explaining results**.

4. **The lean-lsp-mcp server** demonstrates this pattern for Lean: it bridges 5 search engines + LSP into one MCP interface, allowing the LLM to query any search engine and cross-reference results during a conversation.

### 5.3 Proposed MCP Tool Surface

A minimal MCP server for Coq semantic search might expose:

```
search_lemmas(query: string, mode: "semantic" | "pattern" | "type", limit: int)
  → [{name, statement, type, module, relevance_score, informalized_description}]

get_lemma_details(name: string)
  → {statement, type, proof_sketch, dependencies, dependents, module, docstring}

find_related(name: string, relation: "uses" | "used_by" | "similar" | "same_type_class")
  → [{name, statement, relation_type}]

search_by_type(type_pattern: string)
  → [{name, statement, type}]
```

The LLM would use these tools iteratively: search broadly, inspect promising candidates, follow dependency links, and synthesize an answer.

### 5.4 Trade-offs: MCP vs. CLI vs. Web

| Dimension | MCP (LLM-mediated) | CLI | Web Interface |
|-----------|-------------------|-----|---------------|
| **Query sophistication** | High — LLM reformulates and iterates | Low — user must formulate precise queries | Medium — UI can guide |
| **Result quality** | High — LLM filters and explains | Raw ranked list | Raw ranked list with UI |
| **Latency** | Higher (LLM reasoning loop) | Lowest | Medium |
| **Accessibility** | Requires Claude Code or similar | Universal | Universal |
| **Offline use** | Requires LLM API | Fully offline | Requires server |
| **Programmability** | Via LLM conversation | Scriptable | Limited |

**Recommendation:** MCP as primary interface for interactive use. Expose the same search backend as a lightweight HTTP API for direct programmatic access and potential future CLI/web interfaces. The MCP server is a thin adapter over the search API.

### 5.5 Comparison with Alternative Delivery Mechanisms

**coq-lsp extension:** Could expose search as custom LSP requests, usable from any LSP client (VS Code, Emacs). Tight IDE integration but no LLM reasoning layer. Good for pattern/type search; less suitable for natural language search.

**Coq vernacular command:** A `SemanticSearch "query"` command callable from within Coq scripts. Deepest integration but most implementation effort and least flexible.

**IDE plugin (VS Code / Emacs):** Direct integration with search UI panels. Good for browsing results but no conversational refinement.

**These are complementary, not competing.** The search backend should be designed as a service that multiple frontends can consume. MCP is the highest-leverage first frontend because it gets the most value from the LLM reasoning layer.

---

## 6. Architecture Options for Coq Semantic Search

### Option A: Vector DB + MCP (Simplest)

```
[Coq libraries] → [Extraction] → [Embedding model] → [Vector DB]
                                                            ↓
[User] → [Claude Code] → [MCP Server] → [Vector search API]
                ↑                              ↓
                └──── LLM reasoning ←── raw results
```

- **Extraction:** Use SerAPI or coq-lsp to extract all definitions, lemmas, theorems with their types and statements. Generate informalized descriptions via LLM.
- **Embedding:** Embed formal statements + informalized descriptions with a general-purpose model (E5 or bge-base). No fine-tuning initially.
- **Storage:** ChromaDB, LanceDB, or FAISS. Corpus scale (~50-100K items) doesn't require distributed systems.
- **Strengths:** Fast to build. No training data needed. Informalization + general embeddings is a proven approach (LeanSearch).
- **Weaknesses:** No graph structure (leaving 25-34% retrieval gains on the table). No type-aware search. Embedding quality limited by general tokenizer.

### Option B: Knowledge Graph + Vector DB + MCP (Richest)

```
[Coq libraries] → [Extraction] → [Embedding model] → [Vector index]
                       ↓                                     ↓
                  [Graph construction] → [Graph DB] ←→ [Hybrid query engine]
                                              ↓
[User] → [Claude Code] → [MCP Server] → [Search API]
                ↑                              ↓
                └──── LLM reasoning ←── structured results
```

- **Extraction:** Same as Option A, plus dependency graph extraction from Coq's kernel.
- **Graph:** Neo4j (with native vector search) or SQLite + custom graph layer. Nodes: definitions, lemmas, modules. Edges: DEPENDS_ON, PROVES_USING, INSTANCE_OF, etc.
- **Retrieval:** Multi-channel: vector similarity + graph neighborhood + symbol overlap. Reciprocal rank fusion or learned score fusion.
- **Strengths:** Captures all three retrieval signals (semantic, structural, syntactic). Enables graph-based queries ("what lemmas are used in proofs about finitely generated groups?"). Richest MCP tool surface.
- **Weaknesses:** More complex to build and maintain. Graph construction requires deeper Coq integration. Fusion scoring needs tuning.

### Option C: Lightweight Hybrid (Pragmatic Middle Ground)

```
[Coq libraries] → [coq-lsp extraction] → [SQLite: metadata + deps + FTS]
                                      ↓
                               [Embedding model] → [in-process vector index]
                                                          ↓
[User] → [Claude Code] → [MCP Server] → [Hybrid search: FTS + vector + deps]
                ↑                              ↓
                └──── LLM reasoning ←── results with graph context
```

- **Extraction:** Use coq-lsp for extraction. Store everything in SQLite: formal statements, types, module paths, dependency edges, plus FTS5 full-text index.
- **Embedding:** In-process vector index (FAISS or usearch). Embed with a lightweight model (bge-base or similar).
- **Graph:** Dependencies stored as SQLite rows, traversed with SQL. Not a full graph DB, but sufficient for 1-2 hop dependency queries.
- **Strengths:** Single-binary deployment (no external DB services). Fast. Simple. Sufficient for the corpus scale. SQLite's FTS5 provides BM25 for hybrid retrieval.
- **Weaknesses:** Less expressive graph queries than Neo4j. No native graph algorithms (PageRank, community detection). May need to graduate to Option B for complex graph queries.

---

## 7. Open Questions and Research Gaps

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

## 8. Recommendations

1. **Start with Option C (Lightweight Hybrid) + MCP.** SQLite + in-process vectors + coq-lsp extraction is the fastest path to a usable system. The MCP/LLM reasoning layer compensates for retrieval quality limitations by interpreting and filtering results intelligently.

2. **Use informalization as the primary embedding strategy.** Generate natural-language descriptions of each Coq declaration using an LLM. Index these with a general-purpose embedding model (bge-base or E5). This avoids the cold-start problem of needing Coq-specific training data.

3. **Include dependency graph data from the start.** Even in Option C, store dependency edges in SQLite and expose graph traversal via MCP tools (`find_related`, dependency walks). This enables the LLM to follow dependency chains during reasoning.

4. **Design the search backend as a service.** The MCP server should be a thin adapter over an HTTP API. This enables future CLI, web, and coq-lsp plugin frontends without reimplementation.

5. **Measure against Lean baselines.** Lean Finder's evaluation methodology (arena-style user preference testing) should be adopted for Coq. Cross-system comparison helps calibrate quality expectations.

6. **Plan for graduation to Option B.** If the lightweight hybrid proves valuable, the architecture should allow migration to Neo4j or similar for richer graph queries without rebuilding the extraction or embedding pipeline.

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

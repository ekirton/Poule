# Vector Database & Embedding-Based RAG for Semantic Search over Formal Mathematical Libraries

**Research Date**: March 2026
**Scope**: State-of-the-art findings as of early 2026

---

## 1. Vector Databases for Code/Math Search

### General Landscape

The vector database market has grown to ~$1.73B (2024) with projected growth to $10.6B by 2032. The major open-source players are:

| Database | Language | Key Strength | GitHub Stars |
|----------|----------|-------------|-------------|
| **Milvus** | Go/C++ | Scalability, multiple index types (HNSW, IVF, DiskANN) | 35K+ |
| **Qdrant** | Rust | Performance, advanced metadata filtering, production-ready | 9K+ |
| **Weaviate** | Go | Graph-based data model, GraphQL, semantic relationships | 8K+ |
| **ChromaDB** | Python | Simplicity, HNSW-based, good for prototyping | 6K+ |
| **LanceDB** | Rust | Embedded/serverless, Lance columnar format, TypeScript SDK | Growing |
| **pgvector** | C (PG ext) | PostgreSQL ecosystem, familiar SQL, hybrid search | Widely adopted |
| **FAISS** | C++/Python | Raw performance, research-grade, no built-in persistence | Meta standard |

### Formal Math Applications (Observed in Production)

- **ChromaDB**: Used by LeanSearch (the semantic search engine for Mathlib4) with HNSW indexing for approximate nearest neighbor search over theorem embeddings.
- **FAISS**: Used by LeanExplore with an inverted file structure of 4,096 quantization cells for k-NN retrieval over Lean 4 declarations.
- **LanceDB**: Powers Continue IDE's codebase retrieval; the only embedded vector DB with a TypeScript library supporting disk-backed storage and sub-millisecond lookups. Uses AST-aware chunking with tree-sitter for code.
- **pgvector**: Widely adopted for production RAG with code. Supports asymmetric embeddings (RETRIEVAL_DOCUMENT for storage, RETRIEVAL_QUERY for search), half-precision quantization for 2x efficiency with zero quality loss. A/B tests show 34% improvement in retrieval relevance with asymmetric embedding types.

### Observed Adoption Patterns

No formal math project has adopted Qdrant, Weaviate, or Milvus as of early 2026. Adoption has clustered around lightweight options: ChromaDB for prototyping (LeanSearch), FAISS for research systems (LeanExplore), and LanceDB for embedded/local deployments in adjacent code search tools. The relatively small corpus size of formal libraries (Mathlib has ~180K declarations, not billions of vectors) appears to reduce the need for heavy-duty vector database infrastructure.

---

## 2. Embedding Models for Formal Math

### Models Currently Used in Formal Math Systems

| Model | Parameters | Used By | Key Properties |
|-------|-----------|---------|---------------|
| **E5-mistral-7b-instruct** | 7B | LeanSearch, REAL-Prover (LeanSearch-PS) | Best overall for math; instruction-tuned; supports task-specific prompts |
| **ByT5 (byte-level)** | ~300M | ReProver (LeanDojo) | Tokenizer-free, works on raw UTF-8 bytes; handles Lean's special symbols natively |
| **Custom BERT (6-layer)** | ~67M | Premise retrieval for formalization (Zhu et al. 2025) | Custom WordPiece tokenizer trained on Lean corpus; pre-trained from scratch on formal math |
| **bge-base-en-v1.5** (BAAI) | 109M | LeanExplore | Lightweight; processes names, docstrings, informal translations |
| **DeepSeek-Prover-V1.5-RL** | 7B | Lean Finder | Decoder-only; embeddings from final hidden state of last token; fine-tuned with contrastive learning + DPO |
| **Custom decoder (38M/86M)** | 38-86M | Magnushammer | Pre-trained on GitHub + arXiv from the Pile; shared backbone for Select + Rerank |

### Key Findings on Embedding Model Choice

**E5-mistral-7b** is the current gold standard for formal math semantic search:
- Achieves nDCG@20 of 0.733 on the LeanSearch benchmark (vs. 0.365 for Moogle)
- Supports instruction-tuned task prefixes (e.g., "Instruct: Retrieve a Lean 4 theorem...")
- Drawback: 7B parameters makes it resource-intensive; difficult to deploy on constrained devices

**ByT5's byte-level approach** is uniquely suited to formal languages:
- No tokenizer mismatch: processes Unicode mathematical symbols, Lean syntax (`∀`, `→`, `⊢`, `⟨⟩`) as raw bytes
- ReProver achieves R@10 of 27.6% and MRR of 0.24 on LeanDojo benchmark (vs. BM25's 15.5% R@10)
- Compact enough for research deployment

**Custom formal-language BERT** (Zhu et al. 2025) is the most promising new direction:
- Pre-trains BERT from scratch on formalized corpora with a WordPiece tokenizer learned specifically for Lean syntax
- Achieves Recall@5 of 38.20% vs. ReProver's 28.78% on random split
- Achieves 30.74% pass@1 on miniF2F vs. ReProver's 28.28%
- Maintains efficiency comparable to ReProver despite superior performance
- Separates argument retrieval from goal retrieval for fine-grained similarity

**DeepSeek-Prover-based embeddings** (Lean Finder) achieve the best user-facing results:
- Leverages a model already trained on Lean 4 syntax and theorem proving
- Two-stage training: contrastive learning, then DPO with human preference data
- Preferred by users 81.6% of the time vs. 56.9% for LeanSearch

### Models NOT Yet Applied (but Promising)

- **Nomic-embed**: Open-source, 137M params, strong on MTEB; not yet tested on formal math
- **GTE-Qwen2**: Alibaba's embedding model family; untested on formal math
- **Cohere embed-v3**: Commercial; no formal math applications found

---

## 3. RAG Architectures for Theorem Proving

### Architecture Comparison

#### ReProver (LeanDojo) - NeurIPS 2023
- **Retrieval**: ByT5 encoder embeds proof states and premises into shared vector space; cosine similarity for retrieval
- **Generation**: ByT5 encoder-decoder; concatenates top-100 retrieved premises with proof state
- **Key innovations**: (1) Restricts retrieval to accessible premises via program analysis; (2) Hard negative mining via in-file negatives
- **Results**: 27.6% R@10 on LeanDojo benchmark; significantly outperforms BM25

#### Magnushammer - ICLR 2024
- **Two-stage retrieve-then-rerank**:
  - **Select stage**: Contrastive embedding with modified InfoNCE loss; retrieves top-1,024 from ~30-50K available premises using cached premise embeddings + dot product
  - **Rerank stage**: Cross-attention where proof state tokens attend to premise tokens; binary cross-entropy loss with hard negatives from Select
- **Shared backbone**: Both stages share a transformer backbone (38M or 86M params) with specialized linear projections
- **Results**: 59.5% on PISA (vs. Sledgehammer's 38.3%); combined with Thor, achieves 71.0% (vs. 57.0%)

#### REAL-Prover - 2025
- **Retrieval (LeanSearch-PS)**: E5-mistral-7b fine-tuned with contrastive learning on (state, theorem) pairs + hard negative mining
- **Generation**: Fine-tuned LLM with expert iteration
- **Pipeline**: Auto-formalization (HERALD-AF) -> premise retrieval -> tactic generation with best-first search
- **Results**: 23.7% Pass@64 on ProofNet; 56.7% on FATE-M (algebra)

#### Rango - ICSE 2025 (ACM SIGSOFT Distinguished Paper)
- **Retrieval**: Dual retrieval at every proof step:
  - *Proof Retriever*: BM25 over completed proofs from the current project (not just library lemmas)
  - *Lemma Retriever*: TF-IDF over lemma statements from project dependencies
- **Generation**: Fine-tuned DeepSeek-Coder 1.3B with retrieved proofs + lemmas as context
- **Key innovation**: Adapts to per-project proving style by retrieving local proof patterns
- **Results**: 32.0% on CoqStoq (vs. Tactician's 24.8%); proof retrieval alone gives 47% improvement

#### Lean Finder - 2025
- **Retrieval**: DeepSeek-Prover-V1.5-RL fine-tuned with contrastive learning + DPO using human feedback
- **Four input modalities**: Natural language, informalized statements, augmented proof states, formal declarations
- **Key innovation**: Reverse-synthesis for training data; intent-aware query generation from real Lean community discussions
- **Results**: 81.6% user preference rate; 64.2% Recall@1 on informalized statements (vs. LeanSearch's 49.2%)

#### Custom BERT Premise Retriever (Zhu et al. 2025)
- **Two-stage**: Context-Free Retrieval (dense, separate encoding) -> Context-Aware Re-ranking (cross-encoder)
- **Key innovation**: Separate similarity computation for premise arguments vs. goals
- **Results**: 38.20% Recall@5 (vs. ReProver's 28.78%)

### Architectural Trends

1. **Two-stage retrieve-then-rerank is dominant**: Magnushammer, Zhu et al., and effectively Lean Finder all use this pattern
2. **Shift from byte-level to LLM-based embeddings**: ByT5 (ReProver) -> E5-mistral (LeanSearch/REAL-Prover) -> DeepSeek-Prover (Lean Finder)
3. **Per-step retrieval**: Both Rango and ReProver retrieve at each proof step, not just once per theorem
4. **Project-aware retrieval**: Rango's retrieval of local proofs (not just library lemmas) is a significant innovation
5. **Human feedback integration**: Lean Finder's DPO training with user votes is a new direction

---

## 4. Chunking/Indexing Strategies for Formal Math Libraries

### How Formal Math Libraries Are Indexed

Formal math libraries present a unique chunking challenge: the natural "document" boundaries are well-defined by the language itself (declarations, lemmas, theorems, definitions).

#### By Declaration/Lemma (Most Common)
- **One embedding per declaration** is the standard approach across all systems
- LeanSearch, Moogle, and LeanExplore all index at the declaration level
- Each theorem/lemma/definition in Mathlib becomes a single vector
- Mathlib4 has ~180K declarations, yielding a manageable vector store

#### By Proof State (Emerging)
- **ReProver** and **Lean Finder** embed proof states as queries against a premise database
- Lean Finder trains on 337,647 "augmented proof states" (proof states enriched with natural language descriptions)
- This is a query-time strategy, not an indexing strategy: the corpus is still indexed by lemma, but queries are proof states

#### By Type Signature (Partial)
- **Zhu et al. (2025)** separate premise arguments from goals, computing fine-grained similarity on each
- **LeanExplore** indexes multiple "facets" per declaration: name, docstring, informal translation, file path keywords
- No system indexes purely by type signature alone, but type information is implicitly captured in formal statement embeddings

#### StatementGroups (LeanExplore Innovation)
- Groups user-authored code blocks that elaborate into multiple compiled declarations
- Example: a single `structure` definition generates constructor, recursor, and projector declarations; these are unified into one searchable unit
- Prevents fragmented search results and provides canonical naming

#### Bilingual/Informalized Indexing
- **LeanSearch**: Stores "formal statement \n informal name: informal statement" pairs, using GPT-3.5 to informalize
- **Lean Finder**: Trains on 244,521 informalized statements alongside formal ones
- **LeanExplore**: Generates AI-translated informal descriptions as additional embedding facets

#### Research on General Math Chunking (Systematic Study, 2026)
A systematic investigation of 36 chunking strategies across 6 domains found:
- **Paragraph Group Chunking (PGC)** dominates for mathematical texts (nDCG@5 ≈ 0.459)
- Mathematical texts distribute definitions, theorems, and proofs across contiguous sections
- Preserving multi-paragraph structures enables retrieval of complete logical units
- BAAI/bge-m3 (1024-dim) was the strongest embedding model across chunking strategies
- PGC is also the most efficient: 6.26 seconds preprocessing, 873 MB RAM

### Dominant Approach in the Literature

Systems in the literature consistently index at the **declaration level** with **multi-facet enrichment**:
1. All surveyed systems index each declaration as a unit (LeanSearch, Moogle, LeanExplore, Lean Finder)
2. Multiple systems generate informal translations as additional text (LeanSearch, Lean Finder, LeanExplore)
3. LeanExplore includes metadata (file path, module, type signature) as filterable fields
4. Hybrid search (dense embeddings + BM25 keyword matching) appears in the highest-performing system (LeanExplore)

---

## 5. Moogle, Lean Finder, LeanSearch, and LeanExplore

### Moogle (Morph Labs)
- **Status**: First semantic search engine for proof assistants; declining maintenance
- **Architecture**: Per-theorem embedding into vector database; cosine similarity retrieval
- **Performance**: Ranked 1st in only 12.0% of queries in comparative evaluation
- **Limitations**: Closed-source, not kept up-to-date with current Mathlib, no known improvements

### LeanSearch (Gao et al. 2024)
- **Embedding Model**: E5-mistral-7b-instruct
- **Vector Database**: ChromaDB with HNSW indexing
- **Indexing**: Bilingual corpus (formal + informal) per theorem; GPT-3.5 for informalization
- **Query Pipeline**: Optional LLM-based query augmentation (GPT-4 expands user queries into formal+informal form)
- **Task Instructions**: Domain-specific instruction prefixes for both queries and documents
- **Performance**: nDCG@20 = 0.733; Recall@10 = 0.913; ranked 1st in 46.3% of queries
- **Limitation**: 7B embedding model is hard to deploy on constrained devices

### Lean Finder (2025)
- **Embedding Model**: DeepSeek-Prover-V1.5-RL 7B, fine-tuned with contrastive learning + DPO
- **Training Data**: 1.4M query-statement pairs across 4 modalities (natural language, informalized, proof states, formal)
- **Key Innovation**: Intent-aware retrieval trained on real Lean community discussion patterns (693 Zulip/GitHub discussions clustered into 5 intent types)
- **Performance**: 81.6% user preference; 64.2% Recall@1 (vs. LeanSearch's 49.2%); dominates across all modalities
- **Human Feedback**: 1,154 preference triplets from user votes + GPT-4o evaluation for DPO training

### LeanExplore (2025)
- **Embedding Model**: BAAI bge-base-en-v1.5 (109M params) - deliberately lightweight
- **Vector Database**: FAISS with 4,096-cell inverted file index
- **Indexing Innovation**: StatementGroups unifying related declarations; multi-facet embeddings (name, docstring, informal translation, file path)
- **Retrieval**: Hybrid ranking: semantic similarity (threshold 0.525) + BM25+ lexical scoring + PageRank over dependency graph
- **Weights**: Semantic 1.0, BM25+ 1.0, PageRank 0.2 (configurable)
- **Performance**: 55.4% first-place rankings (vs. LeanSearch 46.3%, Moogle 12.0%); wins 79.2% head-to-head vs. Moogle

### Lightweight/LLM-Free Approach (AITP 2025)
- Research direction toward semantic search that does not require large LLMs
- Targets resource-constrained deployment (e.g., within Lean IDE)
- Likely uses smaller models like bge-base or MiniLM-family

### Comparative Summary

| System | Embedding Model | Vector DB | Hybrid? | User Pref | Key Innovation |
|--------|---------------|-----------|---------|-----------|---------------|
| Moogle | Unknown (closed) | Unknown | No | 12% 1st | First mover |
| LeanSearch | E5-mistral-7b | ChromaDB | No | 46% 1st | Query augmentation + bilingual corpus |
| LeanExplore | bge-base-en-v1.5 | FAISS | Yes (BM25+PageRank) | 55% 1st | StatementGroups + hybrid ranking |
| Lean Finder | DeepSeek-Prover-V1.5 | Not specified | No | 82% pref | Intent-aware + DPO with human feedback |

---

## 6. ColBERT/Late-Interaction Models for Formal Math

### Current State: No Direct Application Found

As of early 2026, **no published work applies ColBERT-style late interaction specifically to formal mathematics retrieval or theorem proving**. This represents a clear gap in the literature.

### Why ColBERT Could Be Valuable for Formal Math

ColBERT's late interaction mechanism has properties particularly well-suited to formal math:

1. **Token-level matching**: Formal math statements have precise token-level semantics (e.g., matching `∀ x : ℝ` in a query against `∀ y : ℝ` in a premise). ColBERT's MaxSim operator would naturally handle symbol-level alignment.

2. **Efficiency at scale**: ColBERT pre-computes document token embeddings and only computes query embeddings at search time. For a fixed library like Mathlib (~180K declarations), this is ideal.

3. **Expressiveness vs. bi-encoders**: Single-vector bi-encoders (E5, bge) compress a theorem into one vector, losing fine-grained structure. ColBERT preserves per-token representations.

4. **Storage is manageable**: ColBERT's main drawback (high storage for per-token embeddings) is mitigated by Mathlib's relatively small corpus. ColBERTv2's residual compression reduces storage 6-10x.

### Closest Analogues in Formal Math

The **Magnushammer Rerank stage** is architecturally similar to late interaction:
- Proof state tokens directly attend to premise tokens
- Provides contextualized relevance scoring beyond single-vector similarity
- But it's a cross-encoder (not pre-computable), so it's slower than ColBERT

The **Zhu et al. (2025) Context-Aware Re-ranking** also uses cross-attention between state and premise, resembling late interaction but without ColBERT's efficiency benefits.

### Available ColBERT Models (Potentially Applicable)

| Model | Params | Context | Languages | Notes |
|-------|--------|---------|-----------|-------|
| ColBERTv2 | 110M | 512 | English | Stanford reference; integrated in RAGatouille |
| Jina-ColBERT-v2 | 560M | 8192 | 89 languages | XLM-RoBERTa backbone; rotary embeddings; 6.5% over ColBERTv2 on BEIR |
| answerai-colbert-small-v1 | Small | - | English | Used as reranker in LanceDB code search |

### Gap in the Literature

ColBERT-style late interaction has not been applied to formal math premise selection, despite architectural properties that align with the domain's requirements. The closest existing work — Magnushammer's rerank stage and Zhu et al.'s context-aware re-ranking — uses cross-attention mechanisms that are architecturally similar to late interaction but lack ColBERT's pre-computation efficiency. No published results exist comparing ColBERT's MaxSim operator against these approaches on formal math benchmarks.

---

## Summary

### Approaches with Strongest Results
1. **Embedding**: E5-mistral-7b and DeepSeek-Prover produce the highest retrieval quality; custom BERT with formal tokenizer (Zhu et al.) achieves competitive results at lower compute cost
2. **Retrieval**: Two-stage retrieve-then-rerank (Magnushammer pattern) is the dominant architecture across recent systems
3. **Indexing**: All surveyed systems index one vector per declaration, with the strongest results coming from enrichment with informal translations and metadata
4. **Search**: Hybrid (dense + BM25) consistently outperforms pure dense retrieval in published evaluations (LeanExplore)
5. **Training**: Contrastive learning + hard negative mining is the standard training approach; DPO with human feedback (Lean Finder) is the most recent addition

### Open Gaps
1. **ColBERT/late interaction**: Completely unexplored for formal math
2. **Graph-aware retrieval**: No system exploits the dependency graph for retrieval beyond LeanExplore's PageRank
3. **Cross-library transfer**: All systems are Lean-specific or Isabelle-specific; no cross-prover retrieval
4. **Proof-state indexing**: Proof states are used as queries but never as indexed documents
5. **Incremental indexing**: No system handles live updates as Mathlib evolves (all require full re-indexing)

---

## Sources

### Semantic Search Engines for Lean
- [A Semantic Search Engine for Mathlib4 (LeanSearch)](https://arxiv.org/html/2403.13310v2)
- [Lean Finder: Semantic Search for Mathlib That Understands User Intents](https://arxiv.org/html/2510.15940v1)
- [LeanExplore: A search engine for Lean 4 declarations](https://arxiv.org/html/2506.11085v1)
- [Towards Lightweight and LLM-Free Semantic Search for mathlib4 (AITP 2025)](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)
- [How To Search For Theorems In Lean 4](https://lakesare.brick.do/how-to-search-for-theorems-in-lean-4-WXebAQkXVmx1)

### RAG & Theorem Proving
- [LeanDojo: Theorem Proving with Retrieval-Augmented Language Models](https://arxiv.org/pdf/2306.15626)
- [ReProver GitHub](https://github.com/lean-dojo/ReProver)
- [Magnushammer: A Transformer-Based Approach to Premise Selection](https://arxiv.org/html/2303.04488v3)
- [REAL-Prover: Retrieval Augmented Lean Prover for Mathematical Reasoning](https://arxiv.org/html/2505.20613v1)
- [Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification](https://arxiv.org/html/2412.14063)
- [Assisting Mathematical Formalization with A Learning-based Premise Retriever](https://arxiv.org/html/2501.13959)
- [Premise Selection for a Lean Hammer](https://arxiv.org/pdf/2506.07477)
- [Formal Mathematical Reasoning: A New Frontier in AI](https://arxiv.org/pdf/2412.16075)
- [DeepTheorem](https://arxiv.org/pdf/2505.23754)

### Vector Databases
- [Best Vector Databases in 2026 (Firecrawl)](https://www.firecrawl.dev/blog/best-vector-databases)
- [Best Vector Databases in 2026 (Encore)](https://encore.dev/articles/best-vector-databases)
- [LanceDB](https://lancedb.com/)
- [Building RAG on codebases with LanceDB](https://lancedb.com/blog/building-rag-on-codebases-part-2/)
- [SOTA Embedding Retrieval: Gemini + pgvector](https://shav.dev/blog/state-of-the-art-embedding-retrieval)
- [Using pgvector for AI and Semantic Search in Production](https://www.gocodeo.com/post/using-pgvector-for-ai-and-semantic-search-in-production)

### Embedding Models
- [E5-mistral-7b-instruct (Hugging Face)](https://huggingface.co/intfloat/e5-mistral-7b-instruct)
- [Top Embedding Models in 2025](https://artsmart.ai/blog/top-embedding-models-in-2025/)

### ColBERT / Late Interaction
- [ColBERT GitHub](https://github.com/stanford-futuredata/ColBERT)
- [Jina-ColBERT-v2](https://huggingface.co/jinaai/jina-colbert-v2)
- [Late Interaction Overview (Weaviate)](https://weaviate.io/blog/late-interaction-overview)
- [ColBERT in Practice (Sease, Nov 2025)](https://sease.io/2025/11/colbert-in-practice-bridging-research-and-industry.html)

### Chunking Strategies
- [A Systematic Investigation of Document Chunking Strategies and Embedding Sensitivity (2026)](https://arxiv.org/html/2603.06976)
- [Chunking Strategies (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/)

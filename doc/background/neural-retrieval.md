# Neural Retrieval Architectures for Formal Mathematics (March 2026)

A survey of neural network architectures for premise selection and semantic search over formal mathematical libraries, covering architecture families, training methods, compute requirements, and deployment considerations.

Cross-references:
- [tree-based-retrieval.md](tree-based-retrieval.md) — Training-free structural methods
- [semantic-search.md](semantic-search.md) — Semantic search state of the art
- [coq-premise-retrieval.md](coq-premise-retrieval.md) — Premise selection landscape

---

## 1. Architecture Families

### 1.1 Bi-Encoder (Dual-Encoder)

The dominant paradigm. Encode queries (proof states, natural language) and documents (lemma statements) independently into a shared vector space. Retrieve by cosine similarity with precomputed document embeddings.

**Strengths**: O(1) retrieval with ANN index; document embeddings computed once offline.
**Weaknesses**: No cross-attention between query and document; limited by single-vector representation.

| System | Base Model | Params | Training Objective | Key Metric | Prover |
|--------|-----------|--------|-------------------|------------|--------|
| **ReProver** (NeurIPS 2023) | ByT5-small | 299M | MSE contrastive, in-file hard negatives | R@10=38.4% | Lean |
| **LeanHammer** (Jun 2025) | Encoder-only transformer | 23-82M | Masked contrastive (InfoNCE), τ=0.05 | R@32=72.7% | Lean |
| **CFR** (Jan 2025) | Custom BERT (formal-language tokenizer) | ~110M | In-batch contrastive | R@10=46.5% | Lean |
| **Lean Finder** (Oct 2025) | DeepSeek-Prover-V1.5-RL 7B | 7B | Contrastive + DPO | R@1=64.2% | Lean |
| **RocqStar** (2025) | CodeBERT | 125M | InfoNCE, proof-similarity signal | +28% over Jaccard | **Coq/Rocq** |
| **LeanSearch-PS** (May 2025) | E5-mistral-7b + LoRA | 7B | Contrastive + hard negative triplet | +12pp on FATE-M | Lean |

### 1.2 Cross-Encoder (Reranker)

Jointly encode (query, document) pairs with full cross-attention. Used as a second stage after bi-encoder retrieval.

**Strengths**: Richer interaction between query and document tokens; higher precision on top-ranked results.
**Weaknesses**: O(K) forward passes per query (one per candidate); impractical for full library scan.

| System | Architecture | Rerank Pool | Performance |
|--------|-------------|-------------|-------------|
| **Magnushammer RERANK** (ICLR 2024) | Decoder-only, 38-86M | Top-1024 from SELECT | 59.5% on PISA (vs 38.3% Sledgehammer) |
| **CAR** (Jan 2025) | BERT cross-encoder | Top-K from CFR | Improved precision; nDCG@1=0.373 |

**The standard pattern** is two-stage: bi-encoder retrieval → cross-encoder reranking of top-K. This is the architecture used by Magnushammer, CFR+CAR, and implicitly by any system where an LLM reasons over retrieved results (including MCP-based approaches, where the LLM serves as the reranking/reasoning layer).

### 1.3 Graph Neural Networks

Operate on the graph structure of formal mathematics (dependency graphs, expression graphs) rather than linearized text.

| System | GNN Type | Graph Structure | Key Innovation | Prover |
|--------|----------|----------------|----------------|--------|
| **Graph2Tac** (ICML 2024) | TFGNN | Coq term + dependency graph | Online adaptation to unseen definitions | **Coq** |
| **RGCN-augmented** (Oct 2025) | Relational GCN (2 layers, 1024d) | Heterogeneous dependency graph (3 edge types) | +26% R@10 over ReProver | Lean |
| **Nazrin** (Feb 2026) | Equivariant GNN (5 attn-conv layers) | ExprGraphs from Lean expressions | 1.5M params; thousands of tactics/min | Lean |

**Key finding**: Adding graph structure to text embeddings yields +25-34% retrieval improvement (RGCN work). Graph2Tac's online learning — computing embeddings for definitions unseen during training — is unique and critical for interactive Coq development.

### 1.4 Sparse / Lexical (BM25, SPLADE)

Classical term-frequency methods applied to serialized formal expressions.

**Rango** (ICSE 2025, Distinguished Paper): BM25 over Coq proof states beat CodeBERT dense embeddings by **46%** for in-project proof retrieval. This is the strongest evidence that lexical overlap of formal identifiers carries critical signal that dense embeddings can miss.

No SPLADE (learned sparse) application to formal math exists. Sentence-transformers v5 provides training support. Hybrid dense+sparse achieves 66.3% NDCG@10 vs 55.4% dense-only on MSMARCO — a 20% relative improvement.

### 1.5 Multi-Vector / Late Interaction (ColBERT)

Token-level embeddings with MaxSim scoring. Precompute document token embeddings; compute query tokens at inference; score via per-token maximum cosine similarity.

**No published application to formal math.** This is an identified gap. ColBERT's token-level matching is theoretically well-suited to formal math's precise symbol-level semantics. Jina-ColBERT-v2 and BGE-M3 provide ready-made multi-vector modes. The First Workshop on Late Interaction is at ECIR 2026.

### 1.6 Generative Premise Selection

Autoregressive generation of premise names, rather than retrieval from a fixed index.

**PACT** (ICLR 2022): Generates premise identifiers token-by-token. Achieved 48% proving rate on Lean. Has since been superseded by retrieval-based approaches (LeanHammer: 37.3% cumulative with better evaluation; Magnushammer: 71% with Thor). The trend has moved decisively toward retrieval.

---

## 2. What Works: Key Design Decisions

### 2.1 Training Objectives

| Objective | Used By | Key Insight |
|-----------|---------|-------------|
| **Masked contrastive (InfoNCE)** | LeanHammer | Masks shared premises to avoid false negatives; best retrieval metrics for bi-encoders |
| **In-batch contrastive** | ReProver, CFR, RGCN | Standard; relies on batch size for negatives |
| **Contrastive + DPO** | Lean Finder | DPO aligns with user search intent; best user-facing satisfaction |
| **Contrastive + cross-entropy rerank** | Magnushammer | Two-stage; best end-to-end proving results |
| **Proof-similarity InfoNCE** | RocqStar | Trains on proof structure, not statement similarity; novel for Coq |

Based on published benchmarks, masked contrastive loss (LeanHammer) produces the strongest retrieval metrics; DPO (Lean Finder) achieves the highest user satisfaction scores; two-stage approaches (Magnushammer) yield the best end-to-end proving results.

### 2.2 Hard Negative Mining

All top systems use carefully designed hard negatives:

- **In-file negatives** (ReProver): Premises from the same file share topic but are wrong. Prevents file-level confusion.
- **Retriever-error negatives** (Magnushammer, CAR): Top-ranked false positives from the first-stage retriever. The hardest negatives are the system's own mistakes.
- **Accessible-set negatives** (LeanHammer): Sample from premises that are accessible (respecting dependency ordering) but unused. More realistic than random negatives.
- **Proof-distance calibrated** (RocqStar): Hard negatives have proof distance 0.45-0.65 (neither too similar nor too different). Included with 30% probability.

### 2.3 Tokenization

| Approach | Model | Impact |
|----------|-------|--------|
| **Byte-level (ByT5)** | ReProver | No OOV tokens; 4x longer sequences; safe default |
| **Custom WordPiece on formal corpus** | CFR (BERT) | +33% R@5 over ReProver; critical for small models |
| **Code-pretrained tokenizer** | Lean Finder (DeepSeek), RocqStar (CodeBERT) | Already handles formal syntax; good for 7B+ |
| **Generic NLP tokenizer** | LeanHammer | Works when paired with better training objective/data |

**For Coq**: A Coq-specific tokenizer handling notation conventions (e.g., `_ + _ = _ + _`), MathComp idioms (e.g., `ssrnat`, `fingroup`), and Ltac patterns would improve embedding quality. The CFR finding (+33% from domain-specific tokenization) is the strongest evidence.

### 2.4 Data: What Matters Most

**Quality > quantity**:
- Magnushammer outperforms Sledgehammer with **0.1% of training data** (4K examples)
- LeanHammer (82M) beats ReProver (299M) by capturing richer ground truth (implicit premises from `rw`/`simp`, term-style proofs)

**Training signal**:
- **Statement similarity**: Standard approach (most systems)
- **Proof similarity**: RocqStar's innovation — two theorems with similar proofs are trained to be close in embedding space. RocqStar demonstrated this on Coq/Rocq with open-source model and data.
- **User intent alignment**: Lean Finder's DPO stage. Requires user feedback data.

---

## 3. The Coq-Specific Landscape

### 3.1 Existing Coq/Rocq Neural Systems

| System | Type | Status | Data |
|--------|------|--------|------|
| **Graph2Tac** | GNN tactic prediction + premise selection | Research; niche adoption | 520K definitions, 120 Coq packages |
| **RocqStar** | CodeBERT bi-encoder, proof-similarity training | Open-source (HuggingFace, GitHub) | BigRocq: 76K statements, 4 projects |
| **Rango** | BM25 retrieval + LLM proving | Research; ICSE Distinguished Paper | CoqStoq: 197K theorems, 2,226 projects |
| **CoqHammer** | Traditional ML (symbol overlap) | Mature; widely used | N/A (rule-based) |
| **Tactician** | k-NN + GNN (Graph2Tac) | Maintained; niche | Tactician's Web: 520K+ definitions |

### 3.2 Available Coq Training Data

| Source | Size | Format | Notes |
|--------|------|--------|-------|
| Tactician's Web | 520K definitions (260K theorems), 120 packages | Graph + text | Largest Coq dataset; includes dependency graph |
| CoqStoq | 197K theorems, 2,226 GitHub projects | Proof states + tactics | Used by Rango |
| BigRocq | 76K statements, 4 projects | Proof trees with intermediate states | Used by RocqStar; open-source |
| CoqGym | 71K proofs, 123 projects | JSON proof states | Aging (2019); pinned to Coq 8.9+ |

### 3.3 Cold-Start Strategies

The core challenge: no Coq-specific retrieval training data (premise annotations linking proof states to used lemmas) exists at the scale of LeanDojo's datasets.

**Strategy 1: Informalization (zero-shot, ~$5)**
Use an LLM to generate natural-language descriptions of each Coq declaration. Embed with off-the-shelf model (bge-base). Combine with BM25 and dependency graph signals. Following LeanExplore's approach — 109M off-the-shelf model with hybrid ranking matched or beat 7B fine-tuned models.

**Strategy 2: Cross-lingual transfer from Lean (~$200-400)**
Fine-tune a model pre-trained on Lean retrieval data (LeanHammer's 5.8M pairs) on available Coq data. PROOFWALA (2025) shows models trained on both Lean and Coq outperform monolingual models. Cross-system steering vectors work.

**Strategy 3: Proof-similarity training on Coq data (~$50-200)**
Follow RocqStar's approach: train CodeBERT on proof similarity (Levenshtein distance over tactic lists) using BigRocq or CoqStoq data. 14 hours on 1x H100. Model and training code are open-source.

**Strategy 4: Synthetic data generation (~$200-450 total)**
Extract Coq declarations → informalize with LLM → generate synthetic queries (following Lean Finder) → generate hard negatives via BM25 → train contrastive model.

---

## 4. Compute Requirements

### 4.1 Training

| System | Params | GPU | Wall-Clock | Cost Estimate |
|--------|--------|-----|-----------|---------------|
| LeanHammer (large) | 82M | 1× A6000 | 6.5 days | $200-400 |
| ReProver | 299M | 1× A100 | 5 days | $400-600 |
| RocqStar | 125M | 1× H100 | 14 hours | $50-100 |
| REAL-Prover retriever | 7B (LoRA) | 4× L40 | 12 hours | $100-200 |
| RGCN-augmented (ensemble) | ByT5 + RGCN | 3× A6000 | ~1 day | $150-300 |
| LeanExplore | 109M | None (off-the-shelf) | 0 | $0 |

**Key insight**: Training a formal math retrieval model costs $50-600 in GPU time. The bottleneck is data preparation, not compute.

### 4.2 Inference

| Model Size | CPU Latency (per item) | GPU Latency | INT8 Quantized (CPU) |
|-----------|----------------------|-------------|---------------------|
| 45M (bge-small) | ~40ms | ~2ms | <10ms |
| 109M (bge-base) | ~80ms | ~3ms | <10ms |
| 125M (CodeBERT) | ~80ms | ~3ms | <10ms |
| 299M (ByT5-small) | ~150ms | ~5ms | <20ms |
| 7B (E5-mistral) | ~10s | ~100ms | Impractical on CPU |

### 4.3 Vector Index (FAISS HNSW, 768-dim)

| Items | Index Build | Memory | Query Latency (CPU) |
|-------|------------|--------|-------------------|
| 50K | ~15-30s | ~166MB | <1ms |
| 100K | ~30-120s | ~333MB | ~1ms |
| 200K | ~60-240s | ~666MB | ~1-2ms |

At 50-200K items (the scale of Coq libraries), even brute-force FAISS is <5ms. HNSW is overkill but provides margin.

### 4.4 End-to-End Query Latency (100K corpus, CPU)

| Architecture | Encode | Search | Rerank | Total |
|-------------|--------|--------|--------|-------|
| Bi-encoder (100M, INT8) | ~10ms | ~1ms | — | **~11ms** |
| Bi-encoder (7B, GPU) | ~100ms | ~1ms | — | ~101ms |
| Two-stage (bi+cross, 100M) | ~10ms | ~1ms | ~2.5s (top-10) | ~2.5s |
| LLM reranking (via MCP) | ~10ms | ~1ms | ~2-5s (LLM call) | ~3-6s |

### 4.5 Hardware Requirements for Deployment

| Model Size | Min Hardware | Apple Silicon | Notes |
|-----------|-------------|---------------|-------|
| ≤109M | Any modern CPU | All M-series | INT8: <10ms/item |
| ~300M | Any modern CPU | M1+ | INT8: <20ms/item |
| 7B | 16GB VRAM GPU (INT4) | M2 Max+ (32GB) | ~100-200ms/item |

For a local MCP server use case, a 100M-class model with INT8 quantization runs at <10ms/item on any laptop. No GPU needed. Total query latency including FAISS: ~12ms.

---

## 5. Model Size: Small Models Win

The most striking finding across all systems:

| Comparison | Result |
|-----------|--------|
| LeanHammer (82M) vs ReProver (299M) | 150% more theorems proved |
| LeanExplore (109M, off-the-shelf) vs LeanSearch (7B, fine-tuned) | 55.4% vs 46.3% top ranking |
| Magnushammer (920K minimal) vs Sledgehammer | Outperforms with 0.1% of training data |
| RocqStar (125M) vs Jaccard baseline | +28% improvement |

**Why small models compete**:
1. **Hybrid ranking compensates**: BM25 + PageRank + semantic (LeanExplore pattern) lets small embeddings compete with large ones
2. **Better training > more parameters**: LeanHammer's masked contrastive loss + richer data extraction matters more than model size
3. **Formal math is a small domain**: ~50-200K items; the embedding space doesn't need to be as expressive as for web-scale retrieval
4. **Scaling law evidence** (SIGIR 2024): When accounting for inference cost, optimal model size drops to million-scale parameters

The evidence consistently shows that 100-125M parameter models (bge-base, CodeBERT) match or exceed much larger models when combined with hybrid ranking and quality training data. Scaling to 7B has not demonstrated retrieval improvements sufficient to offset the inference cost increase.

---

## 6. Hybrid Retrieval: The Emerging Consensus

No single retrieval signal dominates. The evidence points to combining multiple complementary signals:

| Signal | Method | Evidence |
|--------|--------|----------|
| **Semantic** | Dense bi-encoder embeddings | All neural systems |
| **Lexical** | BM25 / FTS5 | Rango: BM25 beats CodeBERT by 46% for Coq |
| **Structural** | Graph (RGCN, Graph2Tac) or tree-based (WL kernel) | RGCN: +26% over text-only |
| **Symbolic** | MePo symbol overlap | LeanHammer: +21% from neural+symbolic union |
| **Authority** | PageRank over dependency graph | LeanExplore uses this |

**Hybrid dense+sparse** achieves 66.3% NDCG@10 vs 55.4% dense-only on MSMARCO (sentence-transformers benchmark). Nobody has combined all five signals for formal math.

**Fusion methods**:
- Reciprocal Rank Fusion (simple, effective, no training)
- Learned score fusion (needs validation data)
- LLM-based reasoning over multi-channel results (MCP-based approaches)

---

## 7. Open Research Directions

### 7.1 ColBERT / Late Interaction for Formal Math
Token-level MaxSim scoring is theoretically well-suited to fine-grained symbol matching in formal expressions. Jina-ColBERT-v2 and BGE-M3 provide ready-made multi-vector modes. No published application to formal math exists.

### 7.2 SPLADE / Learned Sparse for Formal Math
Rango's BM25 results suggest lexical features carry critical signal for formal math retrieval. SPLADE's learned term expansion (e.g., `Nat.add_comm` → `commutativity`, `addition`, `natural`) has not been evaluated in this domain. Sentence-transformers v5 provides training support.

### 7.3 Matryoshka Embeddings for Formal Math
Variable-dimension embeddings (768 down to 64) enabling dimension-accuracy tradeoffs have not been applied to formal math retrieval.

### 7.4 Hybrid Dense+Sparse for Formal Math
Dense+sparse fusion improved MSMARCO by 20% relative. BGE-M3 supports dense + sparse + multi-vector in a single model. No formal-math evaluation exists.

### 7.5 Cross-Prover Transfer
No work transfers retrieval models across Lean/Coq/Isabelle. PROOFWALA shows cross-system training benefits, but a single retrieval model serving multiple proof assistants remains unstudied.

---

## References

### Bi-Encoder Systems
Yang, K. et al. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." NeurIPS 2023.

Mikula, M. et al. "Premise Selection for a Lean Hammer." arXiv:2506.07477, June 2025.

Zhu, R. et al. "Assisting Mathematical Formalization with A Learning-based Premise Retriever." arXiv:2501.13959, January 2025.

Lu, Y. et al. "Lean Finder: Semantic Search for Mathlib That Understands User Intents." AI4Math@ICML 2025.

"REAL-Prover: Retrieval Augmented Lean Prover for Mathematical Reasoning." arXiv:2505.20613, May 2025.

"RocqStar: Leveraging Similarity-driven Retrieval and Agentic Systems for Rocq Generation." arXiv:2505.22846, AAMAS 2026.

### Cross-Encoder / Reranker
Mikula, M. et al. "Magnushammer: A Transformer-Based Approach to Premise Selection." ICLR 2024.

### Graph Neural Networks
Blaauwbroek, L. et al. "Graph2Tac: Online Representation Learning of Formal Math Concepts." ICML 2024.

Petrovcic, J. et al. "Combining Textual and Structural Information for Premise Selection in Lean." arXiv:2510.23637, October 2025.

### Sparse / Hybrid
Thompson, S. et al. "Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification." ICSE 2025.

### Joint Embeddings
"ProofBridge: Auto-Formalization of Natural Language Proofs in Lean via Joint Embeddings." arXiv:2510.15681, October 2025.

### Scale / Infrastructure
"Semantic Search over 9 Million Mathematical Theorems." arXiv:2602.05216, February 2026.

"LeanExplore: A Search Engine for Lean 4." arXiv:2506.11085, June 2025.

### Scaling Laws
Fang, Y. et al. "Scaling Laws for Dense Retrieval." SIGIR 2024.

"Scaling Laws for Generative Retrieval." SIGIR 2025.

### Training Frameworks
Han, J. et al. "Proof Artifact Co-Training for Theorem Proving with Language Models." ICLR 2022.

Song, P. et al. "Lean Copilot: LLMs as Copilots for Theorem Proving in Lean." ICLR 2025.

### Cross-System
"PROOFWALA: Multilingual Proof Data Synthesis and Verification in Lean 4 and Coq." arXiv:2502.04671, 2025.

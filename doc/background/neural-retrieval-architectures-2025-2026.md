# Neural Retrieval Architectures for Formal Math / Code Semantic Search (2025-2026)

*Research compiled: 2026-03-15*

---

## 1. Lean Finder (AI4Math@ICML 2025)

**Paper:** [arXiv:2510.15940](https://arxiv.org/abs/2510.15940) — "Lean Finder: Semantic Search for Mathlib That Understands User Intents"
**Venue:** AI4Math Workshop @ ICML 2025 (poster)
**From:** Simon Fraser University

### Architecture

- **Base model:** DeepSeek-Prover-V1.5-RL 7B, chosen for its extensive training on Lean 4 syntax
- **Embedding extraction:** Final hidden states from the last decoder layer's final token → sequence embeddings
- **Embedding space:** Shared space for queries (multiple modalities) and formal Lean code

### Training Pipeline — Two Stages

**Stage 1: Contrastive Learning**
- Optimizes contrastive loss across diverse query modalities (synthetic user queries, informalized statements, augmented proof states, formal statements)
- Each batch constructs sample groups with 1 positive Lean statement and G-1 in-batch negatives
- Loss: `L_contrastive = -1/B * sum_i log(exp(Sim(q_i, c_i+)/τ) / sum_c exp(Sim(q_i, c)/τ))`
- Token-level augmentation enhances robustness to noisy/partial queries

**Stage 2: Direct Preference Optimization (DPO)**
- Collects user feedback from web deployment + LLM-based judgments (GPT-4o on Zulip queries)
- Adapted DPO objective replaces sequence likelihoods with query-code similarity scores
- Joint training combines DPO loss + contrastive loss (weight λ) to prevent degradation
- Preference dataset: 1,154 triplets from upvotes/downvotes and blinded model comparisons

### Data Generation — 1.4M Query-Code Pairs

Total: 1,408,791 pairs. Sources: mathlib4 (97%), research-linked repos (1%), domain-specific libs (2%).

| Modality | Count | Generation Method |
|---|---|---|
| Synthetic user queries | 582,102 | Reverse annotation: 693 real Lean Zulip + GitHub discussions → GPT-4o clustering into 5 intent categories via o3 → per-statement query generation |
| Informalized statements | 244,521 | Rich context (dependents, neighbors, docstrings) → GPT-4o natural language translation |
| Augmented proof states | 337,647 | Synthetic proof state descriptions from Lean proofs, describing proof transitions |
| Formal statements | 244,521 | Declaration-only versions for partial recall |

**Five intent clusters** (discovered from real user discussions):
1. Searching for existing code/lemmas
2. Meta/tactic programming questions
3. Type-class and instance issues
4. Proof engineering & daily usage
5. Library design & formalization

### Performance

| Test Set | Lean Finder R@1 | LeanSearch R@1 | GPT-4o R@1 | Lean Finder MRR |
|---|---|---|---|---|
| Informalized stmts (1000) | **64.2%** | 49.2% | 21.1% | **0.75** |
| Synthetic user queries (1000) | **54.4%** | 47.1% | — | — |
| Augmented proof states (2224) | **24.6%** | — (4.99% LeanStateSrch) | — | — |

**User study** (128 GitHub queries, 5 participants, LMArena-style):
- Lean Finder preferred: **81.6%** of top-3 rankings
- LeanSearch: 56.9%, GPT-4o: 54.1%
- Normalized Borda score: 0.67 vs 0.41 / 0.40

### Significance
Intent-aware, multi-modal query synthesis from real community discussions combined with DPO alignment yielded substantial gains over generic embeddings across all evaluated query types. The system uses a 7B decoder-as-encoder approach, which is computationally expensive but produced the highest reported accuracy. The dataset of 1.4M pairs is the largest Lean code search dataset available as of this writing.

---

## 2. REAL-Prover / LeanSearch-PS

**Paper:** [arXiv:2505.20613](https://arxiv.org/abs/2505.20613) — "REAL-Prover: Retrieval Augmented Lean Prover for Mathematical Reasoning"

### LeanSearch-PS Architecture

- **Base model:** E5-mistral-7b-instruct (dense retriever)
- **Training framework:** Tevatron
- **Fine-tuning:** LoRA with bf16 optimization
- **Config:** LR 2e-5, batch size 128, query max 128 tokens, passage max 256 tokens

### Two-Stage Training for the Retriever

**Stage 1 — Contrastive loss with in-batch negatives:**
- Pairs: (proof_state, positive_theorem) with in-batch negatives
- Loss: `L(x1,x2) = y*d(x1,x2)^2 + (1-y)*max(m - d(x1,x2), 0)^2`

**Stage 2 — Hard negative mining + triplet loss:**
- Embed all statements with initial model
- For each query, sample 1 passage from top-30 to top-100 most similar as hard negative
- Triplets: (state, positive_theorem, hard_negative)
- Loss: `L(x,p,n) = max(d(x,p) - d(x,n) + m, 0)`

### FATE-M Benchmark
- 141 undergraduate-level abstract algebra problems formalized in Lean 4
- From 12 textbooks covering groups, rings, fields
- Verified by Mathlib contributors and PhD students

### Performance

| Benchmark | REAL-Prover (Pass@64) | Best Baseline |
|---|---|---|
| ProofNet | **23.7%** | 21.6% (DeepSeek-Prover-V1.5-RL + RMaxTS) |
| FATE-M | **56.7%** | 41.8% (same baseline) |

**Ablation — retrieval impact:**
| | Without retrieval | With LeanSearch-PS | Delta |
|---|---|---|---|
| ProofNet | 22.6% | 23.7% | +1.1% |
| FATE-M | 44.7% | 56.7% | **+12.0%** |

### Significance
**Hard negative mining from top-30 to top-100 similar passages** proved effective in this setting. The +12% improvement on FATE-M (college-level algebra) indicates that retrieval provides disproportionate benefit for problems requiring extensive theorem recall. The authors used E5-Mistral-7B with LoRA, a 7B-parameter model that remains trainable with standard hardware.

---

## 3. RocqStar (JetBrains Research)

**Paper:** [arXiv:2505.22846](https://arxiv.org/abs/2505.22846) — "RocqStar: Leveraging Similarity-driven Retrieval and Agentic Systems for Rocq generation"
**Venue:** AAMAS 2026 (Autonomous Agents and Multiagent Systems)
**Model:** [HuggingFace: JetBrains-Research/rocq-language-theorem-embeddings](https://huggingface.co/JetBrains-Research/rocq-language-theorem-embeddings)
**Code:** https://github.com/JetBrains-Research/big-rocq

### Embedding Model

- **Base:** CodeBERT (microsoft/codebert-base), 125M parameters
- **Output:** 768-dimensional embeddings
- **Pooling:** Multi-head self-attention + learned self-attentive pooling head
- **Max sequence length:** 128 tokens
- **Also tested:** gte-modernbert-base (no improvement over CodeBERT)

### Training

- **Objective:** InfoNCE (contrastive learning)
- **Optimizer:** AdamW (lr=4e-6, betas=(0.9, 0.99))
- **Batch size:** 16
- **Warmup:** Linear, 10% of 22,000 steps
- **Hardware:** 1x NVIDIA H100, 14 hours wall-clock
- **Hard negatives:** Incorporated with 30% probability when proof distance falls between 0.45-0.65
- **Positive pairs:** proof distance < 0.3; Negative pairs: proof distance > 0.65

### Core Innovation — Proof Similarity as Training Signal

**Key insight:** Instead of training embeddings on statement similarity, train on **proof similarity**. Two theorems with different statements but similar proofs should be close in embedding space.

**Proof distance metric:**
```
D_L(p_i, p_j) = Lev(p_i, p_j) / max(l_i, l_j)
```
Levenshtein distance over tactic lists, where substitution cost = Levenshtein distance between tactic strings.

**Combined distance:**
```
proof_distance = 0.7 * D_L + 0.3 * D_J + γ  (γ = small noise)
```
Where D_J = Jaccard distance over tactic sets.

### BigRocq Dataset
- **76,524 statements** with proofs from 4 large Rocq projects across 344 files
- Sequential proofs transformed into trees by extracting intermediate proof states → ~4x data amplification
- Split: 70% train / 20% val / 10% test (theorems from same file stay in one partition)

### Performance

**IMM-300 benchmark** (300 Rocq theorems, top-7 retrieved premises):
- **28% relative improvement** over Jaccard-based retrieval
- Particularly effective for medium-complexity theorems

**Agentic system** (with multi-agent debate, reflection):
- Baseline (Claude 3.5 Sonnet): 51% overall (73% simple, 41% medium, 27% complex)
- RocqStar Agent: **60% overall** (76% simple, 56% medium, 38% complex)
- Complex theorems nearly doubled in success rate

**Ablation on IMM-50:**
| Configuration | Success |
|---|---|
| Full system | 66% |
| Without multi-agent debate | 56% |
| Without planning | 58% |
| Without RocqStar retrieval | 62% |
| Without reflection | 48% |

**Cost:** ~$1.30/theorem (agent) vs ~$0.12/theorem (baseline generation)

### Significance
The **proof-similarity-driven embedding** approach is defined in terms of tactic sequences, a concept common across proof assistants. CodeBERT provides a lightweight base at 125M parameters, trainable on a single GPU in 14 hours. The Levenshtein-over-tactics metric operates on tactic lists, which exist in analogous form in other provers. The agentic wrapper with multi-agent debate increased success rates but at roughly 10x the per-theorem cost. Model and data are open-source.

---

## 4. Rango (ICSE 2025 — Distinguished Paper Award)

**Paper:** [arXiv:2412.14063](https://arxiv.org/abs/2412.14063) — "Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification"
**Venue:** ICSE 2025 (Research Track)

### Retrieval Architecture — Sparse, Not Dense

**Surprising finding:** Rango uses **BM-25** (sparse/lexical), not neural embeddings.

- **Proof retriever:** BM-25 over proof states, treating identifiers as "words"
  - Accesses a project-local "proof bank" of completed proofs
  - Scores each candidate by maximum BM-25 similarity between current proof state and any state in candidate proof
  - Returns top-k ranked proofs as context
- **Lemma retriever:** TF-IDF over lemma statements (not proofs)
  - Returns top-j relevant lemma statements

**Key result:** BM-25 proved **46% more effective** than CodeBERT dense embeddings for proof state similarity.

### Adaptive Retrieval
- Retrieval at **every proof step** (not just once at start)
- This adaptive approach yields **35% improvement** over static initial retrieval

### CoqStoq Benchmark
- 196,929 theorems across 2,226 GitHub repositories
- 2,225,515 total proof steps
- Split: 181,562 train / 10,396 benchmark / 4,971 validation

### Performance
- **32.0% theorem proof rate** on CoqStoq
- 29% more theorems than Tactician, 66% more than Proverbot9001
- Proof retriever alone: **47% increase** in theorems proven

### Significance
BM-25 outperforming CodeBERT for proof state retrieval indicates that **lexical overlap of identifiers carries significant signal** in formal math retrieval. No published work has yet combined sparse and dense methods for formal math. The adaptive per-step retrieval paradigm produced a 35% improvement over static initial retrieval, indicating that proof-state retrieval benefits from updating as the proof evolves.

---

## 5. Other Recent Papers on Formal Math Embeddings

### 5a. Semantic Search over 9 Million Mathematical Theorems (Feb 2026)

**Paper:** [arXiv:2602.05216](https://arxiv.org/abs/2602.05216)

- **Corpus:** 9.29M theorem statements (99.5% from arXiv, plus ProofWiki, Stacks Project, etc.)
- **Strategy:** Generate natural-language "slogans" per theorem using DeepSeek V3 (~$4,000 cost for full corpus), then embed slogans
- **Embedding model:** Qwen3-Embedding-8B (top performer)
- **Indexing:** PostgreSQL + pgvector, HNSW index with binary quantization
- **Retrieval:** Hamming distance on quantized embeddings → rerank with full cosine similarity
- **Latency:** ~3 seconds per query
- **Performance on 111 expert queries:** Hit@1: 17.1% (27.0% with reranker), Hit@20: 45.0%
- **Deployment:** Web interface, REST API, MCP server for AI agent integration
- **Interesting insight:** Claude Opus 4.5 outperformed DeepSeek V3 for slogan generation quality

### 5b. ProofBridge (Oct 2025)

**Paper:** [arXiv:2510.15681](https://arxiv.org/abs/2510.15681) — "ProofBridge: Auto-Formalization of Natural Language Proofs in Lean via Joint Embeddings"

- **NL encoder:** all-MiniLM-L6-v2 (22.7M params) → 384-dim → project to 512-dim shared space
- **FL encoder:** LeanDojo's ByT5 proof-state encoder (218M params) → linearized DAG traversals of Lean proofs → 1,472-dim → mean pool → project to 512-dim
- **Training:** Symmetric contrastive loss, τ=0.07, AdamW lr=1e-5, 10 epochs, batch 32
- **Dataset:** NuminaMath-Lean-PF — 38,951 NL↔Lean 4 theorem-proof pairs
- **Key result:** 3.28x higher Recall@1 vs all-MiniLM baseline for NL→FL retrieval
- **Outperforms:** Qwen3-Embedding-8B (mMG=0.29) and E5-Mistral (mMG=0.10) with mMG=0.65
- **Insight:** Explicit DAG structure encoding of proofs massively outperforms general-purpose embeddings

### 5c. LeanExplore (Jun 2025)

**Paper:** [arXiv:2506.11085](https://arxiv.org/abs/2506.11085)

- Lightweight embedding model: bge-base-en-v1.5
- Hybrid ranker over multiple text sources
- Designed for resource-constrained deployment

### 5d. "Towards Lightweight and LLM-Free Semantic Search for mathlib4" (AITP 2025)

**Source:** [AITP 2025 abstract](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)

- Explores alternatives to large LLM-based embedding models for Mathlib search

---

## 6. Matryoshka Embeddings / Variable-Dimension Embeddings

### Core Concept
Matryoshka Representation Learning (MRL) trains embeddings that remain useful after truncation to smaller dimensions. The model is incentivized to frontload important information into early dimensions.

**Training:** Multiple contrastive losses applied at different truncation points (e.g., 768, 512, 256, 128, 64, 32 dimensions).

### Models with MRL Support (2025-2026)

| Model | Full Dim | Truncation Dims | Notes |
|---|---|---|---|
| Jina Embeddings v4 | 2048 | 128, 256, 512, 1024 | Also has multi-vector mode |
| EmbeddingGemma-300M | 768 | 128, 256, 512 | 300M params, on-device |
| Nomic Embed Text V2 | 768 | 256 | First MoE embedding model |
| ModernBERT-Embed | 768 | 256 | Apache 2.0, good at code |
| OpenAI text-embedding-3 | 3072 | Any | Commercial |

### Application to Code/Math
- **No formal-math-specific MRL work found.** However, all the above models can be fine-tuned with MRL loss via sentence-transformers.
- **Practical value:** Use high dimensions for offline indexing, low dimensions for fast approximate search, then rerank. Particularly useful for large libraries like Mathlib (230K+ theorems).
- Jina v4's combination of Matryoshka + multi-vector + code LoRA adapter is the closest to a ready-made solution for code search with flexible dimensions.

### How to Train with MRL (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer
from sentence_transformers.losses import MatryoshkaLoss, MultipleNegativesRankingLoss

model = SentenceTransformer("base-model")
base_loss = MultipleNegativesRankingLoss(model)
loss = MatryoshkaLoss(model, base_loss, matryoshka_dims=[768, 512, 256, 128, 64])
```

---

## 7. Sparse Embeddings (SPLADE and Friends)

### Application to Formal Math

**Rango's finding is the most relevant:** BM-25 (a classic sparse method) beat CodeBERT dense embeddings by 46% for Coq proof state retrieval. This strongly suggests sparse/lexical representations capture something crucial about formal code.

**No SPLADE-specific work for formal math exists yet.** This is an open opportunity.

### Why Sparse Could Work for Formal Math
- Formal languages have precise, structured vocabulary (tactic names, type constructors, namespace paths)
- SPLADE's learned term expansion could map proof state concepts to relevant tactic/lemma vocabulary
- Interpretable: you can see which tokens the model considers important
- Compatible with inverted indices (fast retrieval without ANN)

### Sentence Transformers v5 — Sparse Encoder Training

Full SPLADE training support landed in sentence-transformers v5 (2025). Three architectures supported:

1. **SPLADE:** MLMTransformer + SpladePooling (max pooling over MLM logits)
2. **Inference-free SPLADE:** Router with SparseStaticEmbedding for queries (fast) + full SPLADE for documents
3. **CSR (Contrastive Sparse Representation):** SparseAutoEncoder on top of dense embeddings

**Key losses:** SpladeLoss wrapping SparseMultipleNegativesRankingLoss, SparseDistillKLDivLoss, SparseMarginMSELoss.

**Benchmark (NanoMSMARCO):**

| Method | NDCG@10 |
|---|---|
| Sparse only | 52.41% |
| Dense only | 55.40% |
| **Hybrid (dense+sparse)** | **66.31%** |

The hybrid approach massively outperforms either alone.

### BGE-M3 — Production Hybrid Model

BGE-M3 from BAAI natively supports dense + sparse + multi-vector retrieval in a single model:
- Dense: 1024-dim vectors
- Sparse: SPLADE-style vocabulary-sized vectors
- Multi-vector: ColBERT-style token embeddings
- Supports 8192-token inputs, 100+ languages

---

## 8. Multi-Vector Representations (Beyond ColBERT)

### Active Research Area

The **First Workshop on Late Interaction and Multi Vector Retrieval** is at ECIR 2026, indicating this is a hot topic.

### Key Systems

**ColBERTv2/PLAID → WARP (2025):**
- WARP engine combines ColBERTv2/PLAID with WARPSELECT for imputing missing similarities
- Implicit decompression during search
- Addresses the main ColBERT weakness: storage cost (one vector per token)

**Jina Embeddings v4 (2025):**
- Multi-vector mode: 128-dim per token via projection layers
- Late interaction scoring for fine-grained matching
- **Code search adapter** with 71.59 on CoIR benchmark
- Also supports single-vector (2048-dim) and Matryoshka truncation

**BGE-M3:**
- Native ColBERT-style multi-vector output alongside dense and sparse
- Production-ready with vector DB integrations (Milvus, Qdrant)

### Application to Code/Math

- **No published multi-vector work specifically for formal math retrieval.**
- However, late interaction is particularly promising for proof states because:
  - Token-level matching can capture alignment between specific hypotheses/goals
  - Different parts of a proof state (context, goal type, variable names) can be matched independently
  - ColBERT-style MaxSim naturally handles variable-length proof states

### Efficiency Considerations

| Approach | Storage | Search Speed | Quality |
|---|---|---|---|
| Single dense vector | Low | Fast (ANN) | Good |
| Multi-vector (ColBERT) | High (per-token) | Medium | Best |
| Sparse (SPLADE) | Medium | Fast (inverted index) | Good for lexical |
| Hybrid (dense+sparse) | Medium | Medium | Very good |

---

## 9. Embedding Model Fine-Tuning Frameworks

### Available Frameworks

#### 1. Sentence Transformers

- **URL:** https://sbert.net
- **Capabilities:** Most mature framework; supports dense, sparse, and Matryoshka training in one package
- **Training:** Full fine-tune, LoRA (via PEFT), or linear adapter
- **Losses:** MultipleNegativesRankingLoss, CoSENTLoss, MatryoshkaLoss, SpladeLoss, distillation losses
- **Evaluators:** Built-in IR evaluation, NanoBEIR zero-setup benchmarking
- **Data format:** Simple (sentence1, sentence2, [label]) pairs
- **v5 additions:** Full sparse encoder pipeline, Router for asymmetric models

#### 2. LlamaIndex Fine-Tuning

- **URL:** https://docs.llamaindex.ai/en/stable/optimizing/fine-tuning/
- **Capabilities:** Integrated with RAG pipeline, includes synthetic data generation
- **Approaches:**
  - `SentenceTransformersFinetuneEngine` — wraps sentence-transformers
  - `EmbeddingAdapterFinetuneEngine` — trains linear adapter on top of frozen embeddings (fast, cheap)
  - NUDGE — corpus embedding fine-tuning
  - LoRA fine-tuning for any HuggingFace model
- **Typical usage:** Teams already using LlamaIndex for RAG who want end-to-end integration

#### 3. GritLM (Generative + Retrieval in One Model)

- **Paper:** [arXiv:2402.09906](https://arxiv.org/abs/2402.09906)
- **Key idea:** Single model handles both generation and embedding via instruction switching
- **Reported benefit:** 60% speedup for RAG by eliminating separate retrieval model
- **Note:** 7B parameters; designed for joint generation+retrieval workloads

#### 4. UniME (Multimodal, ACM MM 2025)

- **Paper/Code:** https://github.com/deepglint/UniME
- **Two-stage:** Knowledge distillation from NV-Embed V2 + hard negative instruction tuning
- **Focus:** Multimodal (image+text) embeddings; not code-specific

### Observed Practices

**Approaches used in published formal math/code systems:**

- **RocqStar** used sentence-transformers with CodeBERT as base, trained with contrastive loss and hard negatives on 1x H100 in ~14 hours. LoRA was not required at this model size (125M params).

- **REAL-Prover** used Tevatron to fine-tune E5-Mistral-7B-Instruct with LoRA, handling longer contexts at the cost of more GPU memory.

- **Hybrid dense+sparse retrieval** has not yet been applied to formal math in published work, though sentence-transformers v5 and BGE-M3 both provide infrastructure for it. On general benchmarks, hybrid retrieval substantially outperformed either method alone (see Section 7).

- **ModernBERT-Embed** and **CodeBERT** are the smallest base models reported in recent code/math embedding work, ranging from 125M to ~150M parameters.

---

## 10. Summary: Architecture Decision Matrix

| System | Base Model | Params | Approach | Best At |
|---|---|---|---|---|
| Lean Finder | DeepSeek-Prover-V1.5-RL | 7B | Dense (decoder-as-encoder) | Multi-intent Lean search |
| LeanSearch-PS | E5-Mistral-7B-Instruct | 7B | Dense (LoRA) | Premise selection for provers |
| RocqStar | CodeBERT | 125M | Dense (proof-similarity) | Coq/Rocq premise retrieval |
| Rango | BM-25 (no neural model) | 0 | Sparse/lexical | Per-step Coq proof retrieval |
| ProofBridge | MiniLM + ByT5 | 241M | Joint NL-FL embedding | Cross-modal NL↔Lean retrieval |
| TheoremSearch | Qwen3-Embedding-8B | 8B | Dense (slogan-based) | Informal math search at scale |

### Observed Patterns

1. **No single approach dominates across tasks.** Rango (BM-25) outperformed dense models for in-project Coq retrieval, while Lean Finder (7B dense) achieved the highest accuracy for intent-based search across Mathlib. Performance varied with retrieval context and query type.

2. **Proof similarity outperformed statement similarity** for premise selection in RocqStar's evaluation. Training embeddings on proof structure rather than statement text produced a 28% relative improvement over Jaccard-based retrieval.

3. **Hybrid sparse+dense retrieval has not been applied to formal math.** Rango demonstrated strong sparse retrieval results, LeanSearch-PS demonstrated strong dense results, and general-domain benchmarks show hybrid methods outperforming either alone, but no published system combines them for formal math.

4. **Hard negative mining appeared in multiple systems.** Both REAL-Prover (top-30-to-100 similar passages) and RocqStar (proof distance 0.45-0.65) used carefully calibrated hard negative selection.

5. **Matryoshka and multi-vector representations have not been explored** in formal math retrieval as of this survey.

6. **Per-step retrieval outperformed one-shot retrieval.** Rango reported a 35% improvement from adaptive per-step retrieval compared to static initial retrieval.

---

## Sources

- [Lean Finder](https://arxiv.org/abs/2510.15940)
- [REAL-Prover](https://arxiv.org/abs/2505.20613)
- [RocqStar](https://arxiv.org/abs/2505.22846)
- [RocqStar HuggingFace Model](https://huggingface.co/JetBrains-Research/rocq-language-theorem-embeddings)
- [RocqStar Code](https://github.com/JetBrains-Research/big-rocq)
- [Rango](https://arxiv.org/abs/2412.14063)
- [Semantic Search over 9M Theorems](https://arxiv.org/abs/2602.05216)
- [ProofBridge](https://arxiv.org/abs/2510.15681)
- [LeanExplore](https://arxiv.org/abs/2506.11085)
- [AITP 2025 Lightweight Mathlib Search](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)
- [Jina Embeddings v4](https://arxiv.org/abs/2506.18902)
- [GritLM](https://arxiv.org/abs/2402.09906)
- [Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147)
- [SPLADE](https://arxiv.org/abs/2109.10086)
- [BGE-M3](https://arxiv.org/abs/2402.03216)
- [ColBERT Workshop @ ECIR 2026](https://arxiv.org/abs/2511.00444)
- [Sentence Transformers v5 Sparse Encoder Training](https://huggingface.co/blog/train-sparse-encoder)
- [Sentence Transformers Matryoshka Training](https://sbert.net/examples/sentence_transformer/training/matryoshka/README.html)
- [LlamaIndex Embedding Fine-tuning](https://docs.llamaindex.ai/en/stable/examples/finetuning/embeddings/finetune_embedding/)
- [MTEB Leaderboard (March 2026)](https://awesomeagents.ai/leaderboards/embedding-model-leaderboard-mteb-march-2026/)
- [Best Open Source Embedding Models 2026](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)

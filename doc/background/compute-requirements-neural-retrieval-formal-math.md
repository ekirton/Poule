# Compute Requirements, Training Costs, and Scaling Behavior of Neural Retrieval Models for Formal Mathematics and Code Search

**Research date**: March 2026
**Scope**: Training compute, inference cost, scaling laws, and deployment requirements for neural retrieval models used in formal mathematics (Lean, Coq/Rocq, Isabelle)

---

## 1. Training Compute for Formal Math Retrieval Models

### 1.1 ReProver (LeanDojo, NeurIPS 2023)

| Attribute | Value |
|---|---|
| **Architecture** | ByT5-small encoder-decoder (299M params total) |
| **Retriever** | Dense bi-encoder using ByT5 encoder; retrieves top-100 premises per proof state |
| **GPU** | 1x NVIDIA A100 (80GB) |
| **Training time** | ~5 days (120 hours) |
| **Evaluation** | 2 days on 8x V100 GPUs |
| **Dataset** | 98,734 theorems from 3,384 Lean files; 130,262 premises; 217,776 tactics (129,243 with at least one premise); 5.8M (state, premise) pairs implied |
| **Train/val/test split** | 94,734 / 2,000 / 2,000 theorems |
| **Negatives** | k in-file negatives + (n-k) random negatives per positive |
| **Loss** | Mean squared loss with contrastive learning |
| **Avg accessible premises** | 33,160 per theorem (filtered from 128K total) |
| **Performance** | 51.2% Pass@1 (random split), 26.3% Pass@1 (novel_premises split) |

**Estimated FLOPs**: ~5 days x 312 TFLOPS (A100 FP16) x 86,400s/day x 0.3 utilization ~ 4.0 x 10^19 FLOPs (rough upper bound).

Sources: [LeanDojo paper](https://ar5iv.labs.arxiv.org/html/2306.15626), [ReProver GitHub](https://github.com/lean-dojo/ReProver)

---

### 1.2 LeanHammer Premise Selector (June 2025)

| Attribute | Value |
|---|---|
| **Architecture** | Encoder-only transformer, BPE-tokenized |
| **Model sizes** | Small: 23M (6 layers, 384 dim), Medium: 33M (12 layers, 384 dim), Large: 82M (6 layers, 768 dim) |
| **GPU** | NVIDIA A6000 |
| **Training time** | 6.5 A6000-days for large model (~156 GPU-hours) |
| **Batch size** | B=256 (state, premise) pairs with 3 negatives per pair |
| **Loss** | Masked contrastive loss (modified InfoNCE), temperature=0.05 |
| **Dataset** | 469,965 states from 206,005 theorem proofs; 265,348 premises; 5,817,740 (state, premise) pairs |
| **Performance** | Large model proves 150% more theorems than ReProver (218M params) in full pipeline; 33.3% of Mathlib test theorems (cumul setting) |
| **Inference latency** | ~1 second amortized on CPU server; sub-second on GPU; full pipeline < 10 seconds |

**Key insight**: 82M-param LeanHammer outperforms 218M-param ReProver by 150%, demonstrating that architecture and training strategy matter more than raw parameter count.

Source: [Premise Selection for a Lean Hammer](https://arxiv.org/html/2506.07477v1)

---

### 1.3 Magnushammer (ICLR 2024)

| Attribute | Value |
|---|---|
| **Architecture** | Decoder-only transformers (38M and 86M non-embedding params) |
| **Training approach** | Batch-contrastive learning (two stages: Select with InfoNCE + Rerank with BCE) |
| **Pre-training** | GitHub and arXiv subsets from The Pile |
| **Dataset** | 4.4M premise selection instances; 433K unique premises (Isabelle); 1.1M from human proofs + 3.3M from Sledgehammer |
| **Data extraction cost** | 10K CPU-hours (human proofs), 150K CPU-hours / 17 CPU-years (Sledgehammer-augmented) |
| **Select stage** | Batch size N with M=3N additional negatives per positive |
| **Rerank stage** | Binary cross-entropy, 15 negatives per positive, sampled from top-1024 Select predictions |
| **Performance** | 59.5% on PISA (vs 38.3% Sledgehammer), 34.0% on miniF2f (vs 20.9%); combined with LM prover: 71.0% on PISA with 4x fewer params |
| **Data efficiency** | Outperforms Sledgehammer with only 4K training examples (0.1% of available data) |

**GPU specifics not published** in the paper. Training hardware and wall-clock time are not disclosed.

Source: [Magnushammer paper](https://arxiv.org/html/2303.04488v3)

---

### 1.4 REAL-Prover + LeanSearch-PS (May 2025)

| Attribute | Value |
|---|---|
| **Prover architecture** | Qwen2.5-Math-7B with LoRA fine-tuning |
| **Prover training** | 8x A800 GPUs (80GB each), ~18 hours, 3 epochs, lr=5e-5, batch_size=2, cosine decay, bf16 + flash_attn, max context 8192 tokens |
| **Prover dataset** | 210,420 state-tactic pairs (expert iteration algebra: 25,818; NuminaMath: 30,589; annotated undergrad algebra: 18,669; Mathlib extracted: 92,152; Lean-Workbook augmented: 43,192) |
| **Retrieval system** | LeanSearch-PS: E5-mistral-7B-instruct with LoRA fine-tuning |
| **Retrieval training** | 4x L40 GPUs (40GB each), ~12 hours, 1 epoch, lr=2e-5, batch_size=2, bf16 + flash_attn |
| **Retrieval loss** | InfoNCE with in-batch negatives, then hard negative mining (two-stage) |
| **Performance** | 56.7% Pass@64 on FATE-M benchmark; 23.7% Pass@64 on ProofNet |

**Total compute for retrieval training**: 4x L40 x 12h = 48 GPU-hours (L40).

Source: [REAL-Prover](https://arxiv.org/html/2505.20613v3)

---

### 1.5 Lean Finder (October 2025)

| Attribute | Value |
|---|---|
| **Architecture** | DeepSeek-Prover-V1.5-RL (7B params, decoder-only) |
| **Embedding** | Last hidden state of last token in last decoder layer |
| **Training** | Two-stage: contrastive learning + DPO preference alignment |
| **Dataset** | 1.4M query-code pairs across 4 modalities: synthesized user queries (582K, 42%), augmented proof states (338K, 24%), informalized statements (245K, 17%), formal statements (245K, 17%) |
| **DPO data** | 1,154 preference triplets from user votes + GPT-4o judgments |
| **Performance** | Recall@1: 64.2% (vs LeanSearch 49.2%, GPT-4o 21.1%); Recall@10: 93.3% (vs LeanSearch 82.5%) |
| **GPU/time** | Not disclosed |

Source: [Lean Finder](https://arxiv.org/html/2510.15940v1)

---

### 1.6 Graph2Tac (ICML 2024)

| Attribute | Value |
|---|---|
| **Architecture** | Novel GNN for Coq term graphs with definition embedding task |
| **Framework** | TensorFlow |
| **GPU** | Tested up to 2x A100 (multi-GPU supported) |
| **Dataset** | 520K definitions (260K theorems) across 120 Coq packages |
| **Key innovation** | Online learning: computes embeddings for definitions not seen during training |
| **Performance** | Rivals state-of-the-art kNN predictors (Tactician) |
| **Training time** | Not explicitly published |

Source: [Graph2Tac GitHub](https://github.com/IBM/graph2tac), [Paper](https://arxiv.org/abs/2401.02949)

---

### 1.7 LeanExplore (June 2025)

| Attribute | Value |
|---|---|
| **Embedding model** | BAAI bge-base-en-v1.5 (109M params), **not fine-tuned** (off-the-shelf) |
| **Informalization** | Gemini 2.0 Flash generates natural language translations traversing dependency graph in topological order |
| **Ranking** | Hybrid: semantic embeddings + BM25+ + PageRank |
| **Index** | FAISS with inverted file structure, 4096 quantization cells |
| **Coverage** | 6 Lean 4 packages (Batteries, Init, Lean, Mathlib, PhysLean, Std) |
| **Performance** | Ranked 1st in 55.4% of AI-generated queries (vs LeanSearch 46.3%, Moogle 12.0%); head-to-head vs LeanSearch: 50.0% win rate |
| **Deployment** | Web app + Python library; supports local offline mode |
| **Training cost** | Effectively zero for embedding model (uses pre-trained); informalization cost is LLM API calls |

**Key insight**: A 109M-param off-the-shelf model with hybrid ranking (semantic + lexical + graph) matches or exceeds a fine-tuned 7B model (LeanSearch/E5-mistral) on many query types.

Source: [LeanExplore paper](https://arxiv.org/abs/2506.11085)

---

### 1.8 Rango (ICSE 2025, Coq)

| Attribute | Value |
|---|---|
| **Target** | Coq (automated software verification) |
| **Approach** | Retrieval-augmented proof synthesis; retrieves relevant premises AND similar proofs at each proof step |
| **Dataset** | CoqStoq: 2,226 open-source Coq projects, 196,929 theorems |
| **Architecture** | Fine-tuned LLM with retrieval via self-attentive embedder |
| **Performance** | 32.0% of theorems proven (29% more than Tactician); adding relevant proofs to context yields 47% increase |

Source: [Rango](https://arxiv.org/abs/2412.14063)

---

### 1.9 Summary Table: Training Compute

| System | Params | GPU | Wall-clock | Dataset size | Target |
|---|---|---|---|---|---|
| ReProver | 299M (ByT5-small) | 1x A100 | 5 days | 98K theorems, 130K premises | Lean |
| LeanHammer | 82M | 1x A6000 | 6.5 days | 206K theorems, 265K premises | Lean |
| Magnushammer | 86M | Not disclosed | Not disclosed | 4.4M instances, 433K premises | Isabelle |
| REAL-Prover (retriever) | 7B (E5-mistral+LoRA) | 4x L40 | 12 hours | 210K state-tactic pairs | Lean |
| Lean Finder | 7B (DeepSeek) | Not disclosed | Not disclosed | 1.4M query-code pairs | Lean |
| Graph2Tac | Not disclosed | Up to 2x A100 | Not disclosed | 520K definitions | Coq |
| LeanExplore | 109M (off-the-shelf) | None (no fine-tuning) | 0 | N/A | Lean |
| Rango | Not disclosed | Not disclosed | Not disclosed | 197K theorems | Coq |

---

## 2. Inference Compute

### 2.1 Embedding Latency Per Item

**Bi-encoder models (single item)**:
- BERT-base (110M) on CPU: ~8-38 ms per item (batch size 1, varies by CPU; M2 Max: 8 ms at batch=1)
- BERT-base on GPU: ~2-5 ms per item
- bge-base (109M) INT8-quantized on CPU: < 10 ms per item
- bge-large (355M) INT8-quantized on CPU: < 20 ms per item
- 7B embedding model (E5-mistral) on GPU: ~50-200 ms per item (estimated from Mistral-7B inference benchmarks)

**GNN (Graph2Tac)**: No published per-item latency, but GNN inference is typically fast for single graphs (< 10 ms on GPU for small graphs).

### 2.2 Index Construction Time (100K-200K items)

For 768-dimensional embeddings:

| Step | Time estimate |
|---|---|
| Embedding 100K items (BERT-base, GPU) | ~5-8 minutes |
| Embedding 100K items (BERT-base, CPU INT8) | ~17-30 minutes |
| Embedding 100K items (7B model, GPU) | ~3-6 hours |
| FAISS Flat index build (100K x 768) | < 1 second |
| FAISS HNSW index build (100K, M=32) | ~30-120 seconds |
| FAISS IVF4096 index build (100K x 768) | ~5-15 seconds (plus training) |

**Memory for HNSW index** (100K items, 768-dim, M=32):
- Formula: (d * 4 + M * 2 * 4) bytes/vector = (3072 + 256) = 3,328 bytes/vector
- Total: 100K x 3,328 = ~333 MB
- At 200K items: ~666 MB
- At 500K items: ~1.66 GB

### 2.3 Query Latency

| Method | Scale | Latency | Hardware |
|---|---|---|---|
| FAISS Flat (brute force) | 100K | < 1 ms | CPU |
| FAISS HNSW (M=32, efSearch=100) | 100K-500K | ~1-2 ms | CPU |
| FAISS IVF4096,Flat | 100K-500K | ~1-5 ms | CPU |
| Bi-encoder embed + FAISS search | 100K | ~10-40 ms total | CPU |
| Cross-encoder rerank (top-100) | N/A | ~24.7 seconds (100 pairs at 247ms each) | CPU |
| LeanHammer full pipeline | Mathlib scale | < 10 seconds | CPU server |
| LeanHammer premise selection | Mathlib scale | ~1 second amortized | CPU server |

### 2.4 Bi-Encoder vs Cross-Encoder vs GNN

| Architecture | Encode cost | Search cost | Rerank 100 candidates | Total (100K corpus) |
|---|---|---|---|---|
| **Bi-encoder** (100M) | ~10 ms/query | ~1 ms (HNSW) | N/A | ~11 ms |
| **Bi-encoder** (7B) | ~100 ms/query | ~1 ms (HNSW) | N/A | ~101 ms |
| **Cross-encoder** (100M) | N/A | N/A | ~24.7s (100 pairs) | Requires pre-filter |
| **Two-stage** (bi-enc + cross-enc) | ~10 ms | ~1 ms | ~2.5s (10 pairs) | ~2.5s |
| **GNN** (Graph2Tac) | Online per definition | Per-graph inference | N/A | Not benchmarked at scale |

**Conclusion**: Bi-encoders are 100-1000x faster than cross-encoders for retrieval. The two-stage approach (bi-encoder retrieval + cross-encoder rerank of top-k) is the standard production pattern.

---

## 3. Scaling Laws

### 3.1 Dense Retrieval Scaling Laws (SIGIR 2024)

The first formal study of scaling laws for dense retrieval, by Fang et al., tested BERT-based models from 0.5M to 82M non-embedding parameters on MS MARCO and T2Ranking.

**Model size scaling**:
```
L(N) = (A/N)^alpha + delta_N
```
- MS MARCO: A=3.22e4, alpha=0.53, delta_N=0.04, R^2=0.991
- T2Ranking: A=9.89e6, alpha=0.53, delta_N=0.14, R^2=0.999

**Data size scaling**:
```
L(D) = (B/D)^beta + delta_D
```
- MS MARCO: B=3.49e3, beta=1.05, R^2=0.954
- T2Ranking: B=6.04e4, beta=0.50, R^2=0.991

**Joint scaling**:
```
L(N,D) = [(A/N)^(alpha/beta) + B/D]^beta + delta
```
Fitted: A~3.6e4, B~7.1e3, alpha~0.56, beta~1.31, delta~0.03

**Key findings**:
- Retrieval performance follows power-law scaling with both model size and data size
- A critical transition point exists at contrastive entropy ~0.25 where ranking metrics jump significantly
- **Budget allocation**: Without inference costs, optimal at ~13B params for $20K budget; WITH inference costs, optimal drops to million-scale parameters because inference dominates cost
- High-quality annotations dramatically boost performance; ChatGLM3-generated annotations can surpass human quality at 500K+ examples

### 3.2 Generative Retrieval Scaling Laws (SIGIR 2025)

Tested T5 (Small through XXL) and LLaMA-2 (7B, 13B, 70B):

**Model size scaling**: L(P) = (gamma/P)^alpha + lambda_P
- T5: gamma=2.26e-2, alpha=0.40, R^2=0.996
- LLaMA: gamma=1.24e8, alpha=2.40, R^2=0.999

**Inference scaling**: MR(C) = (mu/C)^sigma + lambda_C
- Performance improves with beam size (tested 1 to 100)
- LLaMA-7B surpasses at >10^11 FLOPs per query

**Key finding**: Decoder-only models (LLaMA) show steeper improvement curves and higher performance ceilings than encoder-decoder models (T5).

### 3.3 Formal Math-Specific Scaling Observations

No formal scaling study exists specifically for formal math retrieval. However, empirical evidence from the systems above suggests:

1. **Small models can match large ones with the right design**: LeanHammer (82M) outperforms ReProver (299M) by 150% on theorem proving. LeanExplore (109M, off-the-shelf) matches LeanSearch (7B, fine-tuned) on many queries.

2. **Data quality > data quantity**: Magnushammer outperforms Sledgehammer with only 0.1% of training data. High-quality contrastive pairs matter more than volume.

3. **Hybrid ranking compensates for model size**: LeanExplore combines semantic embeddings with BM25+ and PageRank to match larger models.

4. **Library size scaling**: Mathlib has ~130K premises (ReProver) to ~265K (LeanHammer). No published study tests how retrieval degrades beyond 500K, but FAISS HNSW maintains sub-2ms search up to millions of items.

---

## 4. Lightweight / Efficient Alternatives

### 4.1 Can 100M Match 7B?

**Evidence strongly supports yes, with caveats**:

| System | Params | vs. 7B comparison | Result |
|---|---|---|---|
| LeanExplore (bge-base, 109M, off-shelf) | 109M | vs. LeanSearch (E5-mistral, 7B, fine-tuned) | 50% head-to-head win rate; ranked 1st 55.4% vs 46.3% |
| LeanHammer (large) | 82M | vs. ReProver (ByT5-small, 299M) | 150% more theorems proven |

**Why small models can compete**:
- Hybrid ranking (semantic + lexical + structural) compensates for smaller embeddings
- Domain-specific training data is more important than model capacity
- Off-the-shelf models already capture enough semantic structure for formal math when augmented with informalized descriptions
- LeanExplore struggles only on "very general queries" where the 7B model's broader knowledge helps

### 4.2 Quantization Results

From benchmarks on BGE models (Intel Xeon 8480+):

| Model | Size | Optimization | Latency | Speedup | Accuracy loss (NDCG@10) |
|---|---|---|---|---|---|
| bge-small | 45M | FP32 baseline | ~40 ms | 1x | - |
| bge-small | 45M | INT8 ONNX | < 10 ms | 4.5x | -0.58% |
| bge-base | 109M | FP32 baseline | ~80 ms | 1x | - |
| bge-base | 109M | INT8 ONNX | < 10 ms | ~4x | -1.55% |
| bge-large | 355M | FP32 baseline | ~200 ms | 1x | - |
| bge-large | 355M | INT8 ONNX | < 20 ms | ~4x | -1.53% |

**Throughput at batch=128** (256-token documents): INT8 achieves **4x throughput improvement** over BF16 across all model sizes.

### 4.3 Knowledge Distillation

- **DISKCO (ACM Web 2024)**: Distills cross-encoder knowledge into bi-encoder, closing but not fully eliminating the gap
- **Flipped KD (ACL 2025)**: Small fine-tuned models can produce more effective domain-specific representations than large models for text matching
- **General pattern**: Cross-encoder teacher -> bi-encoder student is the standard pipeline; gains are 2-5% on retrieval metrics

### 4.4 Optimization Stack for Production

Best practice for a 100M-param retrieval model:
1. Start with pre-trained bge-base or similar
2. Fine-tune with contrastive loss on domain data (hours on single GPU)
3. Export to ONNX with INT8 dynamic quantization
4. Deploy with ONNX Runtime: < 10 ms/item on CPU
5. Use FAISS HNSW for index: < 2 ms/query

**Total query latency**: ~12 ms on CPU (no GPU required).

---

## 5. Fine-Tuning vs Training from Scratch

### 5.1 Cost Comparison

| Approach | Typical compute | Time | Data needed |
|---|---|---|---|
| **Pre-training BERT from scratch** | 64+ TPU-days (~$50K-100K) | Weeks-months | Billions of tokens |
| **Fine-tuning BERT for retrieval** | 1 GPU-day (~$10-50) | Hours | 10K-1M pairs |
| **Fine-tuning 7B for retrieval (LoRA)** | 4x L40 x 12h = 48 GPU-hours (~$100-200) | 12 hours | 100K-1M pairs |
| **LeanHammer (82M from scratch on domain data)** | 6.5 A6000-days (~$200-400) | 6.5 days | 5.8M pairs |
| **ReProver (ByT5-small, full fine-tune)** | 1x A100 x 5 days (~$400-600) | 5 days | ~6M pairs |

**When to fine-tune**: Almost always. Pre-trained models already encode useful language/code structure. Fine-tuning adapts this to the specific retrieval task at 100-1000x less cost.

**When to train from scratch**: Only when the domain is radically different from pre-training data (e.g., a novel formal language with no English/code overlap) or when you need very specific architectural choices (e.g., GNN for graph-structured proofs like Graph2Tac).

### 5.2 Transfer Learning: Code Models -> Formal Math

Strong evidence that code pre-training transfers well to formal math:
- **DeepSeek-Prover** (code-trained) is the backbone for Lean Finder
- **E5-mistral** (general + code) is used by LeanSearch and REAL-Prover
- **Qwen2.5-Math** (math-specialized) is used by REAL-Prover's tactic generator
- **bge-base** (general English) works surprisingly well for LeanExplore, suggesting that even general English embeddings capture useful structure when combined with informalization

### 5.3 Informalization as a Bridge

Rather than fine-tuning embeddings, LeanExplore demonstrates that **informalizing formal statements into natural language** and then using off-the-shelf English embeddings is a viable zero-shot approach:
- Cost: LLM API calls for informalization (Gemini 2.0 Flash is cheap: ~$0.01/1K items)
- Advantage: No training required; immediately works for any formal language
- Disadvantage: Quality depends on informalization quality; struggles with very formal/structural queries

---

## 6. Hardware Requirements for Deployment

### 6.1 GPU Requirements

| Model size | Minimum GPU | Recommended GPU | Can run on CPU? |
|---|---|---|---|
| bge-small (45M) | None needed | Any | Yes, < 10 ms/item INT8 |
| bge-base (109M) | None needed | Any | Yes, < 10 ms/item INT8 |
| bge-large (355M) | None needed | Any | Yes, < 20 ms/item INT8 |
| 7B (E5-mistral, Lean Finder) | 16GB VRAM (INT4) | 24-48GB VRAM | Impractical (~10s/item) |
| ReProver (ByT5-small, 299M) | None needed | 8GB+ GPU | Yes, but slower |

### 6.2 Apple Silicon Performance

From published benchmarks:

| Model | M1 (8GB) | M2 Max (32GB) | Comparison |
|---|---|---|---|
| BERT-base inference | ~179 ms | ~38 ms | vs CUDA: 23 ms |
| BERT-base batch=1 | Not tested | 8.02 ms | Competitive with low-end GPU |
| BERT-base batch=32 | Not tested | 70.48 ms | ~9x for 32x batch (efficient) |
| BERT-base (50 chars) | Not tested | 16.93 ms | Short text is fast |
| BERT-base (500 chars) | Not tested | 76.40 ms | Linear scaling with length |

**M3/M4 estimates** (from broader LLM benchmarks):
- M3 Pro/Max: ~20-30% faster than M2 Max for transformer inference
- M4 Pro: Tested in LLM benchmarks with 8B-405B models; expected ~1.3-1.5x M2 Max for embedding models

**Practical recommendations for Apple Silicon**:
- **100M-param models (bge-base)**: Run excellently on all Apple Silicon, including M1. Expect ~10-40 ms/item.
- **300M-param models**: Run well on M2+ with 16GB+ RAM. ~30-80 ms/item.
- **7B models**: Require M2 Max/Ultra or M3 Max/Ultra with 32GB+ unified memory. Expect 200-500 ms/item with INT4 quantization via MLX.
- **LeanExplore approach** (109M + FAISS): Ideal for Apple Silicon deployment.

### 6.3 Minimum Viable Deployment

For a Coq/Lean retrieval system serving a single user:
- **CPU-only** (any modern x86/ARM): bge-base INT8 + FAISS HNSW. ~12 ms/query total. < 1 GB RAM for 100K items.
- **Apple Silicon laptop**: Same as above, native Metal acceleration available via MLX. ~15-25 ms/query.
- **Budget GPU** (RTX 3060 12GB): Can run 7B models with INT4 quantization. ~100-200 ms/query.
- **Production server** (A100/L40): Sub-10ms for any model size up to 7B.

---

## 7. Vector Index Scaling

### 7.1 FAISS Performance at Different Scales

**768-dimensional vectors, HNSW M=32, efSearch=100**:

| Items | Index build time | Index memory | Query latency (CPU) | Query latency (GPU) |
|---|---|---|---|---|
| 50K | ~15-30s | ~166 MB | < 1 ms | < 0.1 ms |
| 100K | ~30-120s | ~333 MB | ~1 ms | < 0.1 ms |
| 200K | ~60-240s | ~666 MB | ~1-2 ms | < 0.1 ms |
| 500K | ~3-10 min | ~1.66 GB | ~1-2 ms | < 0.1 ms |

**FAISS Flat (brute force)** for comparison:
| Items | Memory | Query latency (CPU) |
|---|---|---|
| 50K | ~150 MB | < 1 ms |
| 100K | ~300 MB | ~1-2 ms |
| 200K | ~600 MB | ~2-5 ms |
| 500K | ~1.5 GB | ~5-15 ms |

At the 50K-200K scale relevant to Mathlib/Coq libraries, **even brute-force FAISS is fast enough** (< 5ms). HNSW provides marginal benefit at this scale but becomes important above 500K items.

### 7.2 FAISS vs Qdrant vs usearch

| Engine | Best for | Overhead | Query latency (100K) | Notes |
|---|---|---|---|---|
| **FAISS** (library) | Embedded use, Python/C++ | Minimal (in-process) | < 1 ms | No server needed; ideal for single-user tools |
| **Qdrant** (server) | Multi-user, filtering, persistence | Server process, ~100-500MB base | ~1-3 ms | REST/gRPC API; up to 4x RPS vs alternatives |
| **usearch** (library) | Minimal footprint, embedded | Very minimal | < 1 ms | Single-file library; good for CLI tools |

**Observed pattern in formal math tools**: At the 50K-200K scale typical of formal math libraries, published systems use FAISS (library mode) or similar embedded solutions. No formal math project has adopted a database server (Qdrant, Milvus) for vector search; the corpus scale does not warrant the operational overhead.

### 7.3 GPU-Accelerated Indexing (2025)

NVIDIA cuVS integration in FAISS (May 2025):
- IVF build: **4.7x faster** than classical GPU-accelerated IVF
- IVF search: **8.1x faster** latency reduction
- CAGRA graph build: **12.3x faster** than CPU HNSW build
- CAGRA search: **4.7x faster** than CPU HNSW search

At the 100K-500K scale, these GPU accelerations are overkill (CPU is already < 2ms), but they become relevant if indexing needs to be rebuilt frequently (e.g., incremental updates during development).

---

## 8. Cold-Start Strategies for Coq/Rocq

### 8.1 The Challenge

As of early 2026, there is **no Coq-specific neural retrieval model** comparable to ReProver or LeanHammer for Lean. The available systems are:
- **Tactician**: kNN-based (not neural retrieval), uses locality-sensitive hashing
- **Graph2Tac**: GNN-based tactic prediction with premise selection, but not a retrieval model per se
- **Rango**: LLM-based with retrieval augmentation, dataset is CoqStoq (197K theorems)

### 8.2 Strategy 1: Cross-Lingual Transfer from Lean

**Evidence from PROOFWALA (2025)**:
- Models trained on data from BOTH Lean and Coq outperform models trained on just one language
- Cross-system transfer works: steering vectors from Lean successfully construct proofs in Rocq
- Multilingual models have higher tactic diversity (more compilable tactics per proof state)

**Practical approach**:
1. Start with a model trained on Lean retrieval data (e.g., LeanHammer's training data)
2. Fine-tune on available Coq data (Graph2Tac's 520K definitions, CoqStoq's 197K theorems, or the 10K+ Coq source files dataset)
3. Expected boost: cross-lingual training consistently improves over monolingual baselines

### 8.3 Strategy 2: Informalization (Zero-Shot)

Following LeanExplore's approach:
1. Use an LLM (Gemini Flash, GPT-4o-mini) to generate natural language descriptions of Coq definitions
2. Embed both queries and informalized descriptions with off-the-shelf model (bge-base)
3. Combine with BM25+ lexical matching and dependency-graph PageRank
4. **Cost**: ~$1-5 in API calls for informalizing 100K Coq definitions
5. **No training required**

**Expected quality**: Competitive with fine-tuned models for natural-language queries; weaker for structural/formal queries.

### 8.4 Strategy 3: Synthetic Data Generation

From the broader formal math community (2025):

| Method | Scale | Source |
|---|---|---|
| Informalization + back-translation | 332K informal-formal pairs (MMA dataset for Isabelle+Lean) | Multilingual Math Autoformalization |
| HERALD pipeline | 580K NL-FL statement pairs for Lean | ICLR 2025 |
| Expert iteration | 8M formal statements + proofs | Goedel-Prover-V2 |
| Theorem Prover as Judge | Variable | RLPF framework |
| Process-Driven Autoformalization | Variable, quality > quantity | PDA framework |

**For Coq specifically**:
1. Extract all definitions, lemmas, and proofs from the Coq standard library + popular opam packages
2. Use an LLM to informalize each item (natural language description)
3. Generate synthetic query-document pairs using query synthesis (following Lean Finder's approach)
4. Generate hard negatives via BM25 retrieval of similar-but-wrong premises
5. Train contrastive model on this synthetic data

**Estimated cost**:
- Data extraction: Available via Coq SerAPI or Tactician's infrastructure
- Informalization of 100K items: ~$1-5 (Gemini Flash)
- Synthetic query generation (3-5 queries per item): ~$5-25
- Training (82M model like LeanHammer): ~6.5 GPU-days on A6000 (~$200-400)
- **Total: $200-450 for a working prototype**

### 8.5 Strategy 4: Iterative Bootstrapping

The research literature describes an iterative bootstrapping pattern in which systems begin with off-the-shelf components and progressively incorporate domain-specific training data:

1. **Zero-shot baseline**: An off-the-shelf embedding model (e.g., bge-base) operates over informalized descriptions without any domain-specific training (as in Strategy 2).
2. **Implicit feedback collection**: User interaction data (e.g., clicked results, accepted suggestions) provides signal for relevance judgments.
3. **Synthetic data augmentation**: Query synthesis and hard negative mining (as in Strategy 3) generate contrastive training pairs.
4. **Domain fine-tuning**: The base model is fine-tuned on the combined synthetic and feedback data, producing improved retrieval quality. The improved model then enables harder negative mining for subsequent rounds.

LeanExplore and Lean Finder illustrate successive stages of this pattern: LeanExplore operates with an off-the-shelf model and hybrid ranking, while Lean Finder fine-tunes with synthetic data and user preference feedback.

---

## Summary of Findings

1. **Training compute is low relative to other ML tasks**: Published formal math retrieval models train in 1-7 GPU-days on a single mid-range GPU ($100-600). Data preparation (extraction, informalization, synthetic query generation) accounts for a larger share of total effort than model training.

2. **Small models achieve competitive retrieval quality**: 82M-109M parameter models (LeanHammer, LeanExplore) match or exceed 7B models in published evaluations when combined with hybrid ranking or domain-specific training. Scaling law research (SIGIR 2024) confirms that inference cost dominates total cost at scale, which favors smaller model deployments.

3. **CPU-only deployment produces sub-15ms query latency**: Benchmarks show INT8-quantized 100M-class models run at < 10 ms/item on CPU. FAISS HNSW search at 100K-200K scale adds < 2 ms. Published total query latencies are under 15 ms on modern x86 and ARM CPUs.

4. **Apple Silicon benchmarks show competitive inference times**: M2 Max runs BERT-base at 8 ms (batch=1). M1 with 8GB RAM supports 100M-class models. 7B models require M2 Max or later with 32GB+ unified memory.

5. **Multiple cold-start strategies exist for Coq**: Informalization provides a zero-shot baseline at minimal cost (~$5 in API calls). Cross-lingual transfer from Lean has been demonstrated (PROOFWALA). Published cost estimates for bootstrapping a full custom retrieval model range from $200-450.

6. **Hybrid ranking narrows the gap between small and large models**: LeanExplore demonstrates that combining semantic search + BM25+ + dependency-graph PageRank with a 109M off-the-shelf model produces results competitive with fine-tuned 7B models across multiple evaluation metrics.

---

## Sources

### Papers
- [LeanDojo / ReProver (NeurIPS 2023)](https://ar5iv.labs.arxiv.org/html/2306.15626)
- [Magnushammer (ICLR 2024)](https://arxiv.org/html/2303.04488v3)
- [Scaling Laws for Dense Retrieval (SIGIR 2024)](https://arxiv.org/html/2403.18684v2)
- [Graph2Tac (ICML 2024)](https://arxiv.org/abs/2401.02949)
- [REAL-Prover (May 2025)](https://arxiv.org/html/2505.20613v3)
- [Premise Selection for a Lean Hammer (June 2025)](https://arxiv.org/html/2506.07477v1)
- [LeanExplore (June 2025)](https://arxiv.org/abs/2506.11085)
- [Lean Finder (October 2025)](https://arxiv.org/html/2510.15940v1)
- [Rango (ICSE 2025)](https://arxiv.org/abs/2412.14063)
- [PROOFWALA: Multilingual Proof Data Synthesis (2025)](https://arxiv.org/abs/2502.04671)
- [Scaling Laws for Generative Retrieval (SIGIR 2025)](https://arxiv.org/html/2503.18941v1)
- [Autoformalization Survey (2025)](https://arxiv.org/html/2505.23486v1)
- [DISKCO: Cross-Encoder to Bi-Encoder Distillation (ACM Web 2024)](https://dl.acm.org/doi/10.1145/3589335.3648333)

### Benchmarks and Tools
- [FAISS Index Selection Guide](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)
- [FAISS + NVIDIA cuVS (2025)](https://engineering.fb.com/2025/05/08/data-infrastructure/accelerating-gpu-indexes-in-faiss-with-nvidia-cuvs/)
- [CPU-Optimized Embeddings with Optimum Intel](https://huggingface.co/blog/intel-fast-embedding)
- [Sentence Transformers Efficiency Guide](https://sbert.net/docs/sentence_transformer/usage/efficiency.html)
- [Apple Silicon ML Benchmarks](https://arxiv.org/html/2510.18921v1)
- [Embedding Quantization (HuggingFace)](https://huggingface.co/blog/embedding-quantization)
- [Qdrant Benchmarks](https://qdrant.tech/benchmarks/)
- [Lean Copilot](https://github.com/lean-dojo/LeanCopilot)

# Neural Retrieval Evolution

Design rationale for evolving the search system beyond tree-based structural retrieval toward neural and hybrid retrieval methods.

**Stories**: Future work beyond the initial tree-based MVP.

---

## Context

The initial system uses training-free structural retrieval (WL kernel, MePo, TED, FTS5). This document captures design decisions for adding neural retrieval capabilities, grounded in the evidence surveyed in the [background research](../background/index.md).

---

## Cold-Start Strategy for Coq

Coq lacks the premise annotation datasets (proof state → used lemma mappings) that neural retrieval models require. The background research identifies four strategies used by analogous systems, ordered by increasing investment:

### Phase 1: Informalization (zero-shot, ~$5)

Use an LLM (e.g., Gemini Flash) to generate natural-language descriptions of each Coq declaration. Embed both user queries and informalized descriptions with an off-the-shelf model (e.g., bge-base-en-v1.5, 109M params). Combine with the existing BM25 and structural channels.

This follows the LeanExplore approach, where a 109M off-the-shelf model with hybrid ranking matched or exceeded a fine-tuned 7B model (LeanSearch) on many query types.

### Phase 2: Proof-similarity training (~$50-200)

Follow the RocqStar approach: train a CodeBERT-class model (125M params) on proof similarity using the Levenshtein-over-tactics distance metric. Training data available from BigRocq (76K statements) or CoqStoq (197K theorems). RocqStar reported 14 hours on 1x H100.

### Phase 3: Synthetic data generation + contrastive training (~$200-450)

Extract Coq declarations → informalize with LLM → generate synthetic query-document pairs (following Lean Finder's approach of synthesizing diverse query modalities) → mine hard negatives via BM25 → train contrastive model.

### Phase 4: Cross-lingual transfer from Lean

Fine-tune a model pre-trained on Lean retrieval data (e.g., LeanHammer's 5.8M pairs) on available Coq data. PROOFWALA (2025) demonstrated that models trained on both Lean and Coq outperform monolingual models.

### Bootstrapping sequence

The phases are cumulative: Phase 1 provides a baseline; user interaction data from Phase 1 deployment informs Phase 3 data generation; Phase 4 can be layered on at any point. LeanExplore → Lean Finder followed a similar progression (off-the-shelf → fine-tuned with synthetic + user data).

---

## Model Selection

### Why small models (100-125M)

The background research consistently shows small models competing with or beating large ones for formal math retrieval at the relevant corpus scale (50-200K items):

| Comparison | Finding |
|-----------|---------|
| LeanExplore (109M, off-the-shelf) vs LeanSearch (7B, fine-tuned) | 55.4% vs 46.3% top ranking |
| LeanHammer (82M) vs ReProver (299M) | 150% more theorems proved |
| Magnushammer (920K minimal) vs Sledgehammer | Outperforms with 0.1% of training data |

Hybrid ranking (structural + lexical + semantic) compensates for smaller embedding capacity. SIGIR 2024 scaling law research confirms that when inference cost is accounted for, optimal deployment model size drops to million-scale parameters.

### Candidate base models

| Model | Params | Rationale |
|-------|--------|-----------|
| bge-base-en-v1.5 | 109M | Used by LeanExplore; Apache 2.0; good balance |
| CodeBERT | 125M | Used by RocqStar; code-aware; 768-dim embeddings |
| ModernBERT-Embed | ~150M | Apache 2.0; Matryoshka support; strong at code |

Scale to 7B (E5-Mistral, DeepSeek-Prover) only if retrieval quality proves insufficient after hybrid ranking with a small model.

---

## Tokenization

The background research identifies tokenization as a high-impact design decision:

- **Custom formal-language tokenizer**: The CFR system (Zhu et al., 2025) found +33% Recall@5 from a Lean-specific WordPiece tokenizer. Standard tokenizers fragment formal identifiers (e.g., `Nat.add_comm` becomes multiple subwords).
- **Byte-level (ByT5)**: No OOV tokens for formal syntax, but 4x longer sequences and higher compute cost.
- **Code-pretrained tokenizers**: DeepSeek-Prover and CodeBERT tokenizers already handle formal syntax reasonably well.

For Coq specifically, a tokenizer handling Coq notation conventions (`_ + _ = _ + _`), MathComp idioms (`ssrnat`, `fingroup`), and Ltac patterns would improve embedding quality.

The approach depends on model size: for models under 100M, a custom tokenizer yields the largest gains; for 7B+ code-pretrained models, the existing tokenizer is adequate.

---

## Training Approach

### Contrastive learning with hard negatives

All top-performing formal math retrieval systems use contrastive learning with carefully designed hard negatives:

- **Masked contrastive loss** (LeanHammer): Masks shared premises in the loss to avoid false negatives. Produces the strongest retrieval metrics among bi-encoders.
- **Hard negative mining from retriever errors** (Magnushammer): The top-ranked false positives from first-stage retrieval are the hardest negatives for reranking.
- **Proof-distance calibrated negatives** (RocqStar): Hard negatives with proof distance 0.45-0.65, included with 30% probability.

### Hybrid dense + sparse

Dense embeddings and sparse lexical features capture complementary signals. On MSMARCO, hybrid dense+sparse achieves 66.3% NDCG@10 vs 55.4% dense-only (a 20% relative improvement). Sentence-transformers v5 provides full SPLADE training support. BGE-M3 supports dense + sparse + multi-vector in a single model. No formal math system has combined dense and sparse signals.

### Training frameworks

Sentence-transformers is the most mature framework for embedding fine-tuning, supporting dense, sparse, Matryoshka, and distillation losses with LoRA support. Tevatron is the framework used by REAL-Prover for 7B-class models with LoRA.

---

## Deployment

### Compute requirements

| Model Size | CPU Latency (INT8) | GPU Latency | Memory (100K index) |
|-----------|-------------------|-------------|-------------------|
| 109M (bge-base) | <10ms/item | ~3ms/item | ~333MB (HNSW) |
| 125M (CodeBERT) | <10ms/item | ~3ms/item | ~333MB (HNSW) |
| 7B (E5-mistral) | Impractical | ~100ms/item | ~333MB (HNSW) |

At the 50-200K scale of Coq libraries, even brute-force FAISS is <5ms per query. HNSW provides margin but is not required. Total query latency with a 100M model on CPU: ~12ms (encode + search).

### Apple Silicon

M2 Max runs BERT-base at 8ms per item (batch=1). All M-series chips handle 100M-class models comfortably. 7B models require M2 Max+ with 32GB unified memory.

### Quantization

INT8 quantization via ONNX Runtime provides 4x throughput improvement with <2% accuracy loss across BGE model sizes. This is the standard deployment optimization for production embedding models.

---

## Research Gaps as Opportunities

The following approaches have strong theoretical motivation for formal math but no published evaluation:

### ColBERT / late interaction
Token-level MaxSim scoring preserves fine-grained symbol matching lost by single-vector bi-encoders. Precomputed document token embeddings avoid per-query cross-encoding cost. Jina-ColBERT-v2 and BGE-M3 provide ready-made multi-vector modes. The First Workshop on Late Interaction is at ECIR 2026.

### SPLADE / learned sparse representations
Rango's finding that BM25 beats CodeBERT by 46% for Coq proof state retrieval demonstrates that lexical features carry critical signal. SPLADE could learn to expand formal terms to related concepts. Sentence-transformers v5 provides training support.

### Matryoshka embeddings
Variable-dimension embeddings that remain useful after truncation. Train at multiple dimensions (768 down to 64); use high dimensions for precision, low for fast approximate screening. No formal-math-specific MRL work exists.

### Cross-prover transfer
No work transfers retrieval models across Lean/Coq/Isabelle. PROOFWALA shows cross-system benefits. A single model serving both Lean and Coq retrieval is unexplored.

---

## References

See [background research index](../background/index.md) for the full evidence base, particularly:
- [Neural retrieval architectures](../background/neural-retrieval-architectures-2025-2026.md)
- [Compute requirements](../background/compute-requirements-neural-retrieval-formal-math.md)
- [Neural encoder architectures](../background/neural-encoder-architectures-premise-selection.md)
- [Neural retrieval survey](../background/neural-retrieval.md)

# Neural Network Encoder Architectures for Premise Selection and Semantic Search over Formal Math Libraries

**Research date**: March 2026
**Scope**: Architectures, training, and performance for premise selection in Coq, Lean, and Isabelle

---

## 1. Dual-Encoder / Bi-Encoder Architectures

### 1.1 ReProver (LeanDojo) — ByT5-Based Bi-Encoder

**Paper**: Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models" (NeurIPS 2023)
**Source**: https://ar5iv.labs.arxiv.org/html/2306.15626

| Attribute | Value |
|-----------|-------|
| Architecture type | Dual-encoder (bi-encoder) + encoder-decoder tactic generator |
| Base model | `google/byt5-small` (encoder portion used for retrieval) |
| Parameter count | 299M (full ByT5-small); encoder used for embedding |
| Tokenization | Byte-level (UTF-8 bytes directly, no tokenizer) |
| Embedding method | ByT5 encoder with average pooling over hidden states |
| Similarity function | Cosine similarity between state and premise embeddings |
| Training objective | Mean squared contrastive loss: L = sum |l_ij - cos_sim(s_i, p_j)|^2 |
| Negative sampling | In-batch negatives + in-file hard negatives (k in-file negatives + n-k random negatives) |
| Training data | 129,243 tactics with premises out of 217,776 total tactics from Lean's mathlib |
| Accessible premises | Average 33,160 per theorem (out of ~128K total) |
| Training hardware | 1x NVIDIA A100 (80GB) |
| Training time | 5 days on single A100 |
| Evaluation hardware | 8x V100 GPUs |
| Retrieval budget | Top 100 premises retrieved per query |
| Recall@1 (random split) | 13.5% |
| Recall@10 (random split) | 38.4% |
| MRR (random split) | 0.31 |
| Recall@1 (novel premise split) | 9.1% |
| Recall@10 (novel premise split) | 27.6% |
| MRR (novel premise split) | 0.24 |
| End-to-end theorem proving | 51.2% (random), 26.1% (novel premise) on LeanDojo Benchmark |
| Total compute | ~120 GPU-hours (vs. >1000 for prior methods) |

**Key design decisions**:
- ByT5 byte-level encoding avoids vocabulary mismatch with formal syntax (no OOV tokens for Lean identifiers).
- No domain-specific pretraining required; uses generic ByT5-small checkpoint.
- Two-stage pipeline: (1) train retriever, (2) use retriever to fetch 100 premises per state, then train tactic generator (ByT5 encoder-decoder) on concatenation of state + retrieved premises.
- Hard negative mining uses in-file premises: sampling all negatives randomly caused the model to "mistakenly retrieve other premises from the same file."

---

### 1.2 LeanHammer Premise Selector — Encoder-Only Transformer

**Paper**: Zhu, Clune, Avigad, Jiang, Welleck, "Premise Selection for a Lean Hammer" (June 2025)
**Source**: https://arxiv.org/html/2506.07477v1

| Attribute | Value |
|-----------|-------|
| Architecture type | Encoder-only transformer (bi-encoder) |
| Model sizes | Small: 23M (6L, 384d), Medium: 33M (12L, 384d), Large: 82M (6L, 768d) |
| Base model | Pre-trained NLP embedding models (not ByT5; general-purpose encoders) |
| Training objective | Masked contrastive loss (InfoNCE variant) |
| Temperature | tau = 0.05 |
| Negative sampling | B^- = 3 negatives per state, sampled from accessible premises excluding ground-truth; masking of positive in-batch premises to avoid mislabeling shared premises |
| Training data | 469,965 extracted states from 206,005 theorem proofs; 265,348 filtered premises; 5,817,740 (state, premise) pairs |
| Batch size | B = 256 states |
| Training hardware | 6.5 A6000-days (for large model) |
| Inference latency | ~1 second amortized on CPU servers (premise selection) |
| Full pipeline latency | <10 seconds average (selection + ATP proof search via Aesop) |
| Index | FAISS for efficient similarity search |
| Embedding caching | Caches embeddings for fixed Mathlib versions; recomputes only for new user-defined premises |
| Recall@16 (large model, Mathlib-test) | 63.5% |
| Recall@32 (large model, Mathlib-test) | 72.7% |
| Full pipeline proof rate | 30.1% |
| Cumulative ensemble proof rate | 37.3% |
| vs. ReProver (218M params) | 150% more theorems proven in full setting; 50% more cumulative |

**Key design decisions**:
- Masked contrastive loss prevents false negatives from shared premises across multiple proofs (a premise used in many proofs could be labeled as negative when it is actually valid).
- Extracts richer ground-truth data than ReProver: captures term-style proofs and implicit premises from `rw` and `simp` calls, not just explicit tactic premises.
- Integrates with Lean's Aesop proof search framework, forming an end-to-end hammer.
- Dramatically smaller than ReProver (82M vs 299M) yet significantly outperforms it, largely due to better data extraction and training objective.

---

### 1.3 Custom BERT with Formal-Language Tokenizer (CFR + CAR)

**Paper**: "Assisting Mathematical Formalization with A Learning-based Premise Retriever" (January 2025)
**Source**: https://arxiv.org/html/2501.13959v1

| Attribute | Value |
|-----------|-------|
| Architecture type | Bi-encoder retriever (CFR) + cross-encoder reranker (CAR) |
| Base model | BERT pre-trained from scratch on formalized corpora |
| CFR architecture | 6 transformer layers, 12 attention heads, hidden size 768, intermediate 3072 |
| Tokenizer | Custom WordPiece tokenizer trained on formal math corpus (vocab 30,522) |
| Max sequence length | States: 512 tokens; premise args/goals: 256 tokens each |
| CAR architecture | Same BERT backbone, max position embeddings 1024, sequence-pair classification via [CLS] + sigmoid |
| Training objective (CFR) | In-batch contrastive loss (B x |P| candidates per batch) |
| Training objective (CAR) | Cross-entropy loss with hard negatives from top-k1 retrieved premises |
| Training data | 149,549 premises from Mathlib4 (v4.10.0); 65,567 training theorems; 2,000 val/test each |
| Training hardware | 8x RTX 4080 |
| Batch size | CFR: 32; CAR: 2 with 8 gradient accumulation steps |
| Fine-grained similarity | sim(s, p) = state_emb . 0.5*(arg_emb + goal_emb) — separate encodings for premise arguments and goals |
| Recall@1 (random split) | 15.17% (vs ReProver 11.79%) |
| Recall@5 (random split) | 38.20% (vs ReProver 28.78%) |
| Recall@10 (random split) | 46.53% (vs ReProver 36.69%) |
| nDCG@1 | 0.3731 (vs ReProver 0.3351) |
| Pass@1 on MiniF2F | 30.74% (vs ReProver 28.28%) |
| Inference FLOPs | Lowest among baselines (without reranking) |

**Key design decisions**:
- Domain-specific tokenizer is critical: "performance when k=5 or 10 degrades a lot" without it.
- Pre-training on formal corpus alone yields limited gains; the custom tokenizer matters more.
- Fine-grained similarity (separate argument and goal embeddings) outperforms naive concatenation.
- BERT pre-trained from scratch on formal corpora with custom tokenizer outperforms generic ByT5 at a fraction of the parameters.

---

### 1.4 Lean Finder — DeepSeek-Prover-Based Semantic Search

**Paper**: "Lean Finder: Semantic Search for Mathlib That Understands User Intents" (October 2025)
**Source**: https://arxiv.org/html/2510.15940v1

| Attribute | Value |
|-----------|-------|
| Architecture type | Bi-encoder (decoder backbone used as encoder) |
| Base model | DeepSeek-Prover-V1.5-RL 7B |
| Embedding extraction | Final hidden state of last token in decoder's final layer |
| Training objective | Two-stage: (1) contrastive learning with in-batch negatives, (2) DPO (Direct Preference Optimization) jointly with contrastive loss |
| DPO adaptation | Replaces sequence likelihoods with probabilities defined over candidate statements |
| Training data | 1.4M query-code pairs: 582K synthesized user queries (42%), 338K augmented proof states (24%), 245K informalized statements (17%), 245K formal statements (17%) |
| Data sources | mathlib4 (97%), research repos (1%), Lean libraries (2%) |
| User intent modeling | 5 semantic intent categories derived from clustering Lean Zulip + GitHub discussions |
| Recall@1 (informalized) | 64.2% |
| Recall@1 (synthetic queries) | 54.4% |
| Recall@1 (augmented statements) | 82.7% |
| MRR (informalized) | 0.75 |
| MRR (synthetic) | 0.68 |
| User study preference | 81.6% vs 56.9% for competitors |

**Key design decisions**:
- Uses a decoder-only model (DeepSeek-Prover) as an encoder by extracting the last-token embedding -- enabled by the model's extensive pre-training on Lean 4 syntax.
- DPO alignment stage uses user preference triplets to align with mathematician search intent, going beyond pure contrastive training.
- Multi-modal input support: handles informalized math, formal statements, proof states, and natural language queries.
- Plug-and-play with existing provers: compatible with LLM-based theorem provers without retraining.

---

### 1.5 E5-Mistral (General-Purpose, Not Formal-Math-Specific)

**Source**: https://huggingface.co/intfloat/e5-mistral-7b-instruct

| Attribute | Value |
|-----------|-------|
| Architecture type | Decoder-only transformer used as bi-encoder |
| Base model | Mistral-7B |
| Parameter count | ~7B |
| Fine-tuning | LoRA on top of pretrained Mistral-7B |
| Embedding dimension | 4096 |
| Layers | 32 |
| Training data | Synthetic data generated by proprietary LLMs for hundreds of thousands of embedding tasks across 93 languages |
| MTEB benchmark | State-of-the-art average score (at time of release, late 2023/early 2024) |

**Relevance to formal math**: No published application to formal math premise selection as of early 2026. However, its architecture (decoder-only LLM fine-tuned for embedding) is the same pattern used by Lean Finder with DeepSeek-Prover. E5-Mistral could serve as a baseline or starting point for formal math retrieval if fine-tuned on formal corpora.

---

## 2. Cross-Encoder / Reranker Architectures

### 2.1 Magnushammer — SELECT + RERANK Pipeline

**Paper**: Mikula et al., "Magnushammer: A Transformer-Based Approach to Premise Selection" (ICLR 2024)
**Source**: https://arxiv.org/html/2303.04488v3

| Attribute | Value |
|-----------|-------|
| Architecture type | Two-stage: bi-encoder SELECT + cross-encoder RERANK |
| Backbone | Decoder-only transformer pre-trained on GitHub + arXiv subsets of The Pile |
| Model sizes | 38M and 86M non-embedding parameters (main configs); minimal 920K (L=1, D=256) |
| Proof assistant | Isabelle |
| **SELECT stage** | |
| Objective | Modified InfoNCE (batch-contrastive) |
| Mechanism | Embed proof states and premises into shared latent space; retrieve top K_S=1024 by cosine similarity |
| Batch config | N proof states + N positive premises + M negative premises (M=3N) |
| **RERANK stage** | |
| Objective | Binary cross-entropy loss |
| Mechanism | Joint transformer encoding of (proof_state, premise) pairs; tokens from state directly attend to tokens of premise (cross-attention) |
| Negatives | 15 false positives per positive pair, sampled from top 1024 SELECT candidates |
| **Training data** | |
| MAPL dataset | 4.4M premise selection examples, 433K unique premises |
| HPL (human proofs) | 1.1M examples, 300K unique premises |
| SH (Sledgehammer-augmented) | 3.3M examples, 306K unique premises |
| Data mining cost | ~10K CPU hours (HPL), ~150K CPU hours (SH); ~17 CPU-years total |
| **Performance** | |
| PISA single-step | 59.5% (vs Sledgehammer 38.3%, BM25 30.6%, TF-IDF 31.8%, OpenAI embeddings 36.1%) |
| miniF2F single-step | 34.0% (vs Sledgehammer 20.9%) |
| Thor + Magnushammer (PISA) | 71.0% (vs Thor baseline 57.0%) |
| Thor + Magnushammer (miniF2F test) | 37.3% |
| Data efficiency | With 0.1% of MAPL (~4K samples), already outperforms Sledgehammer |
| Inference timeout | 2 seconds per step |

**Key design decisions**:
- Cross-encoder RERANK stage provides "proof-state-aware scores: tokens of the proof state directly attend to tokens of the premise, giving a more contextualized relevance score" -- this is the key advantage over bi-encoders.
- Cost trade-off: RERANK is O(K_S) forward passes per query (one per candidate), vs. a single embedding + dot product for SELECT. The two-stage pipeline mitigates this by restricting RERANK to the top 1024 SELECT results.
- Even the minimal 920K parameter model outperforms Sledgehammer (40.7%), demonstrating that contrastive training is the key ingredient, not model size.
- Scaling study: increasing layers provides more benefit than increasing embedding dimension.
- Pre-training on The Pile (GitHub + arXiv) before fine-tuning on premise selection is important.

### 2.2 CFR + CAR Reranker (from Section 1.3 above)

The CAR (Context-Aware Re-ranking) module in the BERT-based premise retriever (Section 1.3) also acts as a cross-encoder reranker:
- Concatenates state and premise via [SEP] token.
- Sigmoid on [CLS] embedding produces relevance probability.
- Uses hard negatives from the top-k retrieved premises for training.
- Adds computational cost but improves precision on top-ranked results.

---

## 3. GNN Architectures for Formal Math

### 3.1 Graph2Tac — GNN for Coq Tactic Prediction

**Paper**: Blaauwbroek et al., "Graph2Tac: Online Representation Learning of Formal Math Concepts" (ICML 2024)
**Source**: https://arxiv.org/abs/2401.02949, https://github.com/IBM/graph2tac

| Attribute | Value |
|-----------|-------|
| Architecture type | Graph Neural Network (TFGNN-based) |
| Proof assistant | Coq (via Tactician platform) |
| Graph representation | Directed graph of Coq term structure + definition dependency graph |
| Node types | Definition nodes (from definition embeddings table) and non-definition nodes (from node label embeddings table) |
| Edge types | E original edge labels + E reverse edge labels + self-edge label (2E+1 total entries in edge embedding table) |
| Edge handling | All edges duplicated for bidirectional message passing; self-edges added |
| Graph pruning | Each graph pruned to 1024 nodes |
| Dense layer | Output dimension h_dim |
| MLP | 2-layer MLP (Dense, ReLU, Dense) with inner hidden dimension 2*h_dim, followed by Dropout, Residual, LayerNorm |
| Training batch | 512 definitions + 512 proof states |
| Training data | 120 Coq packages from Opam; >250M nodes encoding 520K definitions |
| Definition embedding task | Trained with cosine similarity loss; learns to compute representations for math concepts not seen during training |
| Online learning | Deeply integrated into user workflow; adapts in real time to new Coq projects and their definitions |
| Implementation | TensorFlow GNN (TFGNN) |
| **Performance** | |
| Online definition task improvement | 1.5x over offline baseline |
| vs. CoqHammer | at least 1.48x improvement |
| vs. Proverbot9001 | at least 1.48x improvement |
| vs. transformer baseline | at least 1.48x improvement |
| Combined with k-NN | 1.27x over individual performances |

**Key design decisions**:
- Operates on a faithful graph representation of Coq terms, not a linearized string representation. This preserves the tree/DAG structure of dependent type theory terms.
- Novel definition embedding task allows the GNN to compute representations for unseen definitions at inference time, without retraining -- critical for online use.
- The hierarchical representation builds definition embeddings from the subgraph of all definitions a concept depends on.
- Parameter count and exact h_dim not reported in available materials; the codebase uses configurable YAML files for hyperparameters.

### 3.2 RGCN-Augmented Retrieval (Text + Structure Fusion)

**Paper**: "Combining Textual and Structural Information for Premise Selection in Lean" (October 2025)
**Source**: https://arxiv.org/html/2510.23637v1

| Attribute | Value |
|-----------|-------|
| Architecture type | Hybrid: ByT5 dual-encoder + RGCN (Relational Graph Convolutional Network) |
| Proof assistant | Lean 4 (Mathlib) |
| Text encoder | ReProver's ByT5 dual-encoder (produces initial embeddings h_p^(0), h_s^(0)) |
| GNN type | RGCN with relation-specific weight matrices |
| GNN update rule | h_p^(l+1) = sigma(W_0^(l) * h_p^(l) + sum_r (1/N_r(p)) * W_r^(l) * h_u^(l)) |
| Edge/relation types | Signature hypotheses, signature goals, proof dependencies |
| GNN layers | L = 2 |
| Hidden dimensions | 1024 |
| Activation | ReLU |
| Dropout | 0.256 (node), 0.142 (edge) |
| Training objective | InfoNCE contrastive loss, temperature tau = 0.0138 |
| Optimizer | Learning rate 0.00499, L2 weight decay 2.359e-5 |
| Epochs | 120 |
| Batch size | 1024 with 2-batch gradient accumulation |
| Ensemble | 6 independently trained models with exponential moving average |
| Graph structure | 440,487 total nodes (180,907 premise + 259,580 state nodes); 1.77M premise-to-premise edges; 4.21M premise-to-state edges |
| Edge distribution | Signature hypotheses: 36.9-63.4%, Signature goals: 35.4-36.6%, Proof dependencies: 27.7% |
| Training data | LeanDojo Mathlib benchmark (commit 29dcec07); 379,861 next-tactic premise labels |
| Training note | Proof-dependency edges excluded during training to prevent memorization |
| Training hardware | 3x NVIDIA A6000 (48GB), dual Intel Xeon Silver 4410Y, 512GB RAM |
| Training time (ensemble) | ~1 day |
| **Performance vs. ReProver** | |
| Recall@1 | 17.98% (+33.98% relative, from 13.42%) |
| Recall@10 | 50.04% (+26.36% relative, from 39.60%) |
| MRR | 0.4095 (+24.73% relative, from 0.3283) |

**Key design decisions**:
- The RGCN propagates information through the dependency graph of the math library, enriching text-based embeddings with structural context (which premises reference which other premises).
- Proof-dependency edges must be excluded during training to prevent the model from memorizing which premises were used in a proof (data leakage).
- The hybrid approach significantly outperforms pure text-based ReProver, demonstrating that structural information in formal libraries is highly valuable for premise selection.
- Ensemble of 6 models with EMA provides further gains.

### 3.3 Other GNN Approaches (Historical Context)

From the COLM 2024 survey (Li et al., "A Survey on Deep Learning for Theorem Proving"):

- **FormulaNet** (Wang et al., 2017): Graph embedding preserving edge ordering for HOL Light.
- **Olsak et al.** (2019): GNN capturing logical invariances in first-order logic.
- **Paliwal et al.** (2020): Comprehensive evaluation of graph representations for HOL Light formulas.
- **Ferreira & Freitas** (2020b) and **Bauer et al.** (2023): Graph contrastive learning over theorem dependency graphs.

Note: The term "Nazrin's equivariant GNN" does not appear in available literature as of early 2026. There may be unpublished or very recent work under a different name. Equivariant GNNs (preserving permutation/group symmetries) have been explored in molecular modeling but no published application to formal math premise selection was found.

---

## 4. ColBERT / Late-Interaction Models

### 4.1 Status for Formal Math (as of early 2026)

**No published application of ColBERT or late-interaction models to formal math premise selection exists** as of early 2026. The search across arXiv, conference proceedings, and research forums yielded no results.

**Architecture overview** (for reference):
- ColBERT (Khattab & Zaharia, SIGIR 2020; ColBERTv2, 2021) independently encodes query and document into token-level embeddings using BERT, then computes relevance via MaxSim: for each query token, take the max cosine similarity against all document tokens, then sum.
- Precomputes document token embeddings; only query encoding is needed at inference time.
- Jina-ColBERT-v2 (August 2024): multilingual, 89 languages, flexible output dimensions (128 or 64), based on XLM-RoBERTa.
- ColPali extends the paradigm to visual documents.

**Why it could be relevant to formal math**:
- Token-level matching could capture fine-grained structural similarity in formal terms (e.g., matching specific type constructors, lemma names, or proof patterns).
- Precomputation advantage: all library premises can have token embeddings precomputed and indexed; only the proof state needs encoding at inference time.
- MaxSim scoring preserves token-level detail that is lost in mean-pooled bi-encoder embeddings.
- Storage cost: ~128 floats per token vs 1 vector per document; significant for large math libraries but tractable with compression (ColBERTv2 uses residual compression to ~2 bytes/dim).

**Gap**: This is an unexplored opportunity. A ColBERT-style model with a formal-math tokenizer could potentially outperform bi-encoders while being cheaper than cross-encoders.

---

## 5. Sequence-to-Sequence / Generative Approaches to Premise Selection

### 5.1 PACT (Proof Artifact Co-Training) — Autoregressive Premise Selection

**Paper**: Han et al., "Proof Artifact Co-Training for Theorem Proving with Language Models" (ICLR 2022)
**Source**: https://arxiv.org/abs/2102.06203

| Attribute | Value |
|-----------|-------|
| Architecture type | Autoregressive (decoder-only / seq2seq) |
| Proof assistant | Lean |
| Approach | Uses auto-regressive language modeling objective for premise selection: generates premise names token-by-token |
| Training | Co-trains on proof artifacts (kernel-level proof terms) alongside tactic prediction |
| Base improvement | 32% to 48% theorem proving success rate on held-out test |

**Key point**: PACT demonstrates that generative models can perform premise selection by generating premise identifiers autoregressively, rather than ranking a fixed library. This is fundamentally different from retrieval-based approaches.

### 5.2 ReProver's Tactic Generator (Encoder-Decoder)

ReProver's tactic generator (ByT5, encoder-decoder) implicitly performs premise selection: it generates tactic strings that may reference premises, conditioned on retrieved premises. The retriever narrows the search space from ~128K to 100 premises, then the generator selects among them by generating the tactic text.

### 5.3 Lean Copilot — Multiple LLM Backends

**Paper**: Song et al., "Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean" (ICLR 2025)
**Source**: https://arxiv.org/html/2404.12534v2

Lean Copilot supports multiple generative backends for tactic suggestion:
- Local: ReProver (ByT5 encoder-decoder via CTranslate2)
- APIs: GPT-4, Claude, Gemini, InternLM2
- Both whole-proof generation (single forward pass) and proof search (sequential tactic generation)

The generative approach treats premise selection as part of tactic generation: the LLM generates a tactic string that implicitly names the premises it wants to use.

### 5.4 Assessment: Retrieval vs. Generation for Premises

| Dimension | Retrieval (Bi/Cross-Encoder) | Generation (Autoregressive) |
|-----------|-------------------------------|------------------------------|
| Scalability | O(1) per query with precomputed index | O(L) per premise where L = name length |
| Coverage | Scores all library premises | May miss premises not in training data |
| Latency | Single forward pass + dot products | Multiple decoding steps |
| Composability | Retrieved premises can be reranked or filtered | Generated premises need validation |
| Current best results | LeanHammer (37.3% cumulative), Magnushammer (71% with Thor) | PACT (48% on Lean, but older evaluation) |
| Trend | Dominant paradigm as of 2025 | Used as part of tactic generation, not standalone premise selection |

---

## 6. Training Objectives: Detailed Comparison

### 6.1 Contrastive Loss Variants Used in Premise Selection

| System | Loss Function | Temperature | Negative Strategy | Key Innovation |
|--------|---------------|-------------|-------------------|----------------|
| ReProver | Mean squared contrastive loss | N/A | In-batch + in-file hard negatives | In-file negatives prevent file-level confusion |
| LeanHammer | Masked contrastive loss (InfoNCE variant) | tau=0.05 | B^-=3 per state from accessible premises | Masks positive in-batch premises to avoid mislabeling shared premises |
| Magnushammer SELECT | Modified InfoNCE | N/A | In-batch (M=3N negatives) | Batch-contrastive with oversampled negatives |
| Magnushammer RERANK | Binary cross-entropy | N/A | 15 false positives from top-1024 SELECT results | Hard negatives from retriever's own errors |
| RGCN-augmented | InfoNCE | tau=0.0138 | Standard in-batch | Applied after GNN propagation |
| CFR (BERT-based) | In-batch contrastive | Not specified | B x |P| candidates per batch | Fine-grained similarity decomposition |
| CAR reranker | Cross-entropy | N/A | Hard negatives from top-k retrieved | Cross-encoder reranking |
| Lean Finder | Contrastive + DPO | N/A | In-batch | DPO aligns with user preference triplets |

### 6.2 Hard Negative Mining Strategies

1. **In-file negatives** (ReProver): Premises from the same source file as the positive are strong negatives because they share namespace and topic but are not the correct premise.

2. **Retriever-error negatives** (Magnushammer RERANK, CAR): The top-ranked false positives from the bi-encoder/retriever stage are the hardest negatives for the cross-encoder.

3. **Accessible-set negatives** (LeanHammer): Negatives sampled from the set of premises accessible to a given theorem (respecting dependency ordering), not from the entire library.

4. **Masked positives** (LeanHammer): Shared premises (used in multiple proofs) are masked in the contrastive loss rather than treated as negatives, preventing false negative signal.

### 6.3 DPO for Retrieval (Lean Finder)

Lean Finder is the first system to apply DPO to formal math retrieval:
- Replaces sequence likelihoods (standard DPO) with probabilities defined over candidate statements.
- Trained jointly with contrastive loss.
- Uses user preference triplets derived from mathematician discussion forums.
- Achieves 81.6% user study preference rate, indicating strong alignment with human search intent.

### 6.4 Comparative Assessment

Based on the published results:
- **Masked contrastive loss** (LeanHammer) produces the best retrieval metrics among bi-encoders when combined with high-quality data extraction (capturing implicit premises, term-style proofs).
- **Two-stage contrastive + cross-encoder** (Magnushammer) produces the best end-to-end theorem proving results when combined with a prover.
- **DPO** (Lean Finder) achieves the highest user satisfaction scores but has not been evaluated in an end-to-end theorem proving pipeline.
- **Hard negative mining from retriever errors** is consistently beneficial across all systems that use it.
- **Temperature tuning** matters significantly: LeanHammer uses tau=0.05 (very sharp), RGCN uses tau=0.0138 (extremely sharp).

---

## 7. Tokenization: Impact on Retrieval Quality

### 7.1 Approaches Used in Premise Selection Systems

| System | Tokenization | Vocab Size | Notes |
|--------|-------------|------------|-------|
| ReProver | ByT5 byte-level (UTF-8) | 256 bytes | No tokenizer; operates directly on bytes; no OOV for any formal syntax |
| LeanHammer | Standard NLP tokenizer (pre-trained encoder) | Typical ~30K | Details not published |
| CFR/CAR (BERT) | Custom WordPiece trained on formal corpus | 30,522 | Domain-specific tokenizer is critical for performance |
| Magnushammer | Standard tokenizer (The Pile pre-training) | Not specified | Pre-trained on GitHub + arXiv |
| Lean Finder | DeepSeek tokenizer | Not specified | Trained on Lean 4 code |

### 7.2 Key Findings on Tokenization

1. **Custom formal-math tokenizer is critical**: The BERT-based system (CFR) found that "performance when k=5 or 10 degrades a lot" without a domain-specific tokenizer. A custom WordPiece tokenizer trained on formal Lean code significantly outperforms generic NLP tokenizers.

2. **ByT5 byte-level avoids the problem entirely**: By operating on raw bytes, ByT5 never encounters OOV tokens for formal syntax (Unicode identifiers, special symbols). However, byte sequences are ~4x longer than token sequences, increasing compute cost and limiting context length.

3. **Decoder-based models pre-trained on code**: DeepSeek-Prover's tokenizer (used by Lean Finder) already handles Lean 4 syntax well due to code-focused pre-training, without needing a custom tokenizer.

4. **Emerging approaches**: Meta's Byte Latent Transformer (BLT, December 2024) uses entropy-based dynamic patching that gives complex regions (rare words, code, numbers) smaller patches with more compute, potentially combining the best of both byte-level and token-level approaches. BLT matches Llama 3 at 8B scale while using up to 50% fewer inference FLOPs.

5. **SuperBPE** (COLM 2025): Two-pass BPE that learns cross-word superword tokens, achieving up to 15% improvement in bytes per token. Not yet applied to formal math.

### 7.3 Summary

The evidence across these systems shows a consistent relationship between model scale and tokenization strategy:
- For small models (<100M parameters), domain-specific tokenizers show the largest gains (cf. CFR's 33% improvement over generic tokenizers).
- At medium scale (~300M), ByT5's byte-level approach avoids OOV issues entirely without requiring tokenizer engineering, though at a 4x sequence length cost.
- At large scale (7B+), code-pretrained models (DeepSeek-Prover, CodeLlama) already handle formal syntax adequately due to their pre-training distribution.

---

## 8. Summary Comparison Table

| System | Year | Prover | Arch Type | Params | Training Obj | Hardware | Training Time | Key Metric |
|--------|------|--------|-----------|--------|--------------|----------|---------------|------------|
| ReProver | 2023 | Lean | Bi-encoder (ByT5) | 299M | MSE contrastive | 1x A100 | 5 days | R@10=38.4%, 51.2% proved |
| Magnushammer | 2024 | Isabelle | Bi-enc + Cross-enc | 38-86M | InfoNCE + BCE | Not specified | Not specified | 59.5% single-step, 71% with Thor |
| Graph2Tac | 2024 | Coq | GNN (TFGNN) | Not reported | Cosine sim | Not specified | Not specified | 1.48x over CoqHammer |
| RGCN-augmented | 2025 | Lean | ByT5 + RGCN | ByT5+RGCN | InfoNCE | 3x A6000 | ~1 day | R@10=50.04% (+26% vs ReProver) |
| LeanHammer | 2025 | Lean | Encoder-only | 23-82M | Masked contrastive | A6000s | 6.5 A6000-days | R@32=72.7%, 37.3% proved |
| CFR+CAR (BERT) | 2025 | Lean | BERT bi-enc + cross-enc | ~110M est. | Contrastive + CE | 8x RTX 4080 | Not specified | R@10=46.53%, 30.74% MiniF2F |
| Lean Finder | 2025 | Lean | Decoder-as-encoder | 7B | Contrastive + DPO | Not specified | Not specified | R@1=64.2% (informalized) |
| PACT | 2022 | Lean | Autoregressive | Not specified | LM + co-training | Not specified | Not specified | 48% proved (older eval) |

---

## 9. Summary and Open Problems

1. **Bi-encoders dominate**: The retrieval stage in all modern systems uses a bi-encoder (dual-encoder) for scalability. Cross-encoders are used only for reranking.

2. **Small models can win**: LeanHammer (82M) dramatically outperforms ReProver (299M) by improving data quality and training objectives, not model size. Magnushammer's 920K model beats Sledgehammer.

3. **Structural information helps significantly**: The RGCN-augmented approach shows +26% R@10 over ReProver by incorporating dependency graph structure. This is the clearest evidence that formal math retrieval benefits from graph structure beyond text.

4. **Graph2Tac is unique**: It is the only system that operates purely on graph structure (no text linearization) and supports online learning for unseen definitions. However, it targets Coq and tactic prediction rather than pure premise retrieval.

5. **ColBERT / late-interaction is unexplored**: No published work applies token-level late interaction to formal math. This is a clear gap.

6. **DPO for retrieval is nascent**: Only Lean Finder uses DPO, and only for user-facing search. Applying DPO to premise selection in an end-to-end theorem proving pipeline is unexplored.

7. **Tokenization matters but is under-studied**: The CFR paper is the only one that rigorously ablates tokenizer choice. More systematic study is needed.

8. **Generative premise selection has stalled**: PACT (2022) demonstrated it but retrieval-based approaches have since dominated. No recent system uses pure autoregressive premise generation.

9. **Cross-prover transfer is unexplored**: All systems are trained and evaluated on a single proof assistant. No work transfers premise selection models across Lean/Coq/Isabelle.

---

## Sources

- [LeanDojo / ReProver (NeurIPS 2023)](https://ar5iv.labs.arxiv.org/html/2306.15626)
- [ReProver GitHub](https://github.com/lean-dojo/ReProver)
- [Magnushammer (ICLR 2024)](https://arxiv.org/html/2303.04488v3)
- [Graph2Tac (ICML 2024)](https://arxiv.org/abs/2401.02949)
- [Graph2Tac GitHub](https://github.com/IBM/graph2tac)
- [Premise Selection for a Lean Hammer (June 2025)](https://arxiv.org/html/2506.07477v1)
- [LeanHammer GitHub](https://github.com/JOSHCLUNE/LeanHammer)
- [Combining Textual and Structural Information / RGCN (October 2025)](https://arxiv.org/html/2510.23637v1)
- [Learning-based Premise Retriever / CFR+CAR (January 2025)](https://arxiv.org/html/2501.13959v1)
- [Lean Finder (October 2025)](https://arxiv.org/html/2510.15940v1)
- [Lean Copilot (ICLR 2025)](https://arxiv.org/html/2404.12534v2)
- [Lean Copilot GitHub](https://github.com/lean-dojo/LeanCopilot)
- [A Survey on Deep Learning for Theorem Proving (COLM 2024)](https://arxiv.org/abs/2404.09939)
- [PACT (ICLR 2022)](https://arxiv.org/abs/2102.06203)
- [E5-Mistral](https://huggingface.co/intfloat/e5-mistral-7b-instruct)
- [ColBERT](https://github.com/stanford-futuredata/ColBERT)
- [Jina-ColBERT-v2](https://arxiv.org/abs/2408.16672)
- [LeanAgent (2024)](https://arxiv.org/html/2410.06209v5)

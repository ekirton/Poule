# Retrieval Pipeline

Technical design for the multi-channel retrieval pipeline and fusion logic.

**Feature**: [Multi-Channel Retrieval](../features/retrieval-channels.md)
**Stories**: [Epic 3: Retrieval Quality](../requirements/stories/tree-search-mcp.md#epic-3-retrieval-quality)
**Implementation spec**: [specification/](../../specification/) ([pipeline](../../specification/pipeline.md), [fusion](../../specification/fusion.md))

---

## Query Processing

### search_by_structure

```
1. Parse the query expression (via coq-lsp or the Coq parser)
2. coq_normalize(constr_t)              → normalized expr_tree
3. cse_normalize(tree)                   → CSE-reduced tree
4. wl_histogram(tree, h=3)              → query histogram
5. wl_screen(histogram, library, N=500) → top-500 WL candidates
6. For candidates with node_count ≤ 50:
     compute ted_similarity, collapse_match, const_jaccard
     combine with weighted sum
7. For candidates with node_count > 50:
     compute collapse_match, const_jaccard
     combine with weighted sum
8. Rank by structural_score
9. Return top-N results (default N=50)
```

### search_by_type (multi-channel)

```
1. Parse the type expression
2. Run WL screening pipeline (above)    → structural ranked list
3. Extract symbols, run MePo            → symbol ranked list
4. Run FTS5 query on pretty-printed type → lexical ranked list
5. rrf_fuse([structural, symbol, lexical], k=60) → final ranked list
6. Return top-N results
```

### search_by_symbols

```
1. Receive symbol list from caller
2. Run MePo iterative selection (p=0.6, c=2.4, max_rounds=5)
3. Optionally compute const_jaccard for top candidates
4. Return ranked results
```

### search_by_name

```
1. Preprocess query for FTS5 (qualified name → AND terms, escape specials)
2. Run FTS5 MATCH with BM25 weights (name=10.0, statement=1.0, module=5.0)
3. Return ranked results
```

## WL Kernel Screening

Precompute WL histogram vectors for all declarations at h=3. On query:
1. Extract and normalize the query expression
2. Compute WL histogram at h=3
3. Apply size filter (ratio threshold 1.2 for small, 1.8 for large expressions)
4. Cosine similarity against all precomputed vectors (sparse dot product)
5. Return top-N candidates (N=200-500, tunable for recall)

Sub-second on 100K items. Histograms loaded into memory at server startup (~100MB for 100K declarations).

## MePo Symbol Overlap

Iterative breadth-first selection with inverse-frequency weighting:
- Weight function: `1.0 + 2.0 / log2(freq + 1)` — rare symbols get high weight
- Relevance: weighted overlap of candidate's symbols with working set, normalized by candidate's total weight
- Iterative expansion: each round adds selected declarations' symbols to the working set, with decaying threshold (`p * (1/c)^round`)
- Parameters: p=0.6, c=2.4, max_rounds=5

Typical runtime: <200ms for 100K declarations with inverted index.

## FTS5 Full-Text Search

SQLite FTS5 with Porter stemming and Unicode tokenization. BM25 ranking with column weights biased toward name matches. Queries preprocessed to handle qualified name patterns. Runtime: <10ms.

## TED Fine Ranking

Zhang-Shasha tree edit distance on CSE-normalized trees. Applied only to expressions ≤ 50 nodes. Cost model distinguishes leaf vs. interior operations and same-category vs. cross-category renames. Threshold can be raised to 200-500 nodes with an OCaml/Rust APTED implementation.

## Fine-Ranking Metric Fusion

For candidates with TED available (node_count ≤ 50):

```
structural_score = 0.15 * wl_cosine
                 + 0.40 * ted_similarity
                 + 0.30 * collapse_match
                 + 0.15 * const_jaccard
```

For candidates without TED (node_count > 50):

```
structural_score = 0.25 * wl_cosine
                 + 0.50 * collapse_match
                 + 0.25 * const_jaccard
```

## Reciprocal Rank Fusion

```
RRF_score(d) = Σ_c  1 / (k + rank_c(d))
```

k=60 (standard). Each channel contributes independently. No learned weights.

### Channel Contributions by Tool

| MCP Tool | Channels Used |
|----------|--------------|
| `search_by_structure` | WL + TED + Const Jaccard, fused with RRF |
| `search_by_symbols` | MePo, optionally Const Jaccard |
| `search_by_name` | FTS5 only |
| `search_by_type` | WL + MePo + FTS5, fused with RRF |

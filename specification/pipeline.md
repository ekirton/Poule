# Query Processing Pipeline

End-to-end flow for each MCP search tool. Ties together all components.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Components: [coq-normalization.md](coq-normalization.md), [cse-normalization.md](cse-normalization.md), [channel-wl-kernel.md](channel-wl-kernel.md), [channel-mepo.md](channel-mepo.md), [channel-fts.md](channel-fts.md), [channel-ted.md](channel-ted.md), [channel-const-jaccard.md](channel-const-jaccard.md), [fusion.md](fusion.md)

---

## `search_by_structure`

For a query Coq expression:

```
1. Parse the query expression (via coq-lsp or the Coq parser)
2. coq_normalize(constr_t)              → normalized expr_tree
3. cse_normalize(tree)                   → CSE-reduced tree
4. wl_histogram(tree, h=3)              → query histogram
5. wl_screen(histogram, library, N=500) → top-500 WL candidates
6. For candidates with node_count ≤ 50:
     compute ted_similarity(query, candidate)
     compute collapse_match(query, candidate)
     compute const_jaccard(query, candidate)
     combine with weighted sum (see fusion.md)
7. For candidates with node_count > 50:
     compute collapse_match(query, candidate)
     compute const_jaccard(query, candidate)
     combine with weighted sum (see fusion.md)
8. Rank by structural_score
9. Return top-N results (default N=50)
```

---

## `search_by_type`

For a query type expression (multi-channel):

```
1. Parse the type expression
2. Run WL screening pipeline (steps 2-8 above)     → structural ranked list
3. Extract symbols, run MePo                        → symbol ranked list
4. Run FTS5 query on the pretty-printed type        → lexical ranked list
5. rrf_fuse([structural, symbol, lexical], k=60)    → final ranked list
6. Return top-N results
```

---

## `search_by_symbols`

```
1. Extract symbols from the query (or accept a symbol list directly)
2. Run MePo iterative selection
3. Optionally compute Const Jaccard for top MePo results
4. Return ranked results
```

---

## `search_by_name`

```
1. Preprocess query for FTS5 (qualified name splitting, escaping)
2. Run FTS5 MATCH query with BM25 weights
3. Return results ordered by BM25 score
```

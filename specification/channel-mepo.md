# Channel 2: MePo Symbol Overlap

An iterative, breadth-first symbol-relevance filter. Selects declarations whose symbol sets overlap with the query, with inverse-frequency weighting so rare symbols count more.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Data structures: [data-structures.md](data-structures.md)
Used by: [fusion.md](fusion.md)

Based on the MePo algorithm (see [doc/background/tree-based-retrieval.md](../doc/background/tree-based-retrieval.md)).

---

## Symbol Weight Function

```
function symbol_weight(symbol, freq_table):
    f = freq_table[symbol]  # number of declarations containing this symbol
    return 1.0 + 2.0 / log2(f + 1)
```

Rare symbols (low frequency) get high weight. A symbol appearing in 1 declaration has weight ~3.0; a symbol appearing in 10,000 declarations has weight ~1.15.

---

## Relevance Score

For a candidate declaration `d` with symbol set `symbols(d)`, and the current working symbol set `S`:

```
function relevance(d, S, freq_table):
    numerator   = sum(symbol_weight(s, freq_table) for s in symbols(d) ∩ S)
    denominator = sum(symbol_weight(s, freq_table) for s in symbols(d))
    if denominator == 0:
        return 0.0
    return numerator / denominator
```

---

## Iterative Selection

MePo selects declarations in rounds. Each round adds new symbols from selected declarations, allowing transitive relevance discovery.

```
function mepo_select(query_symbols, library, freq_table, p=0.6, c=2.4, max_rounds=5):
    S = set(query_symbols)          # working symbol set
    selected = []                    # (decl_id, relevance_score) pairs
    remaining = set(all declaration IDs)

    for round_i in 0..max_rounds:
        threshold = p * (1/c) ^ round_i
        newly_selected = []

        for decl_id in remaining:
            r = relevance(decl_id, S, freq_table)
            if r >= threshold:
                newly_selected.append((decl_id, r))

        if len(newly_selected) == 0:
            break

        for (decl_id, r) in newly_selected:
            remaining.remove(decl_id)
            selected.append((decl_id, r))
            S = S ∪ symbols(decl_id)   # expand working symbol set

    selected.sort(by=score, descending=True)
    return selected
```

**Parameters**:
- `p = 0.6`: Base threshold. Declarations must have at least 60% of their weighted symbol mass overlapping with the working set to be selected in round 0.
- `c = 2.4`: Decay factor. Each subsequent round reduces the threshold by a factor of 1/2.4, admitting weaker matches.
- `max_rounds = 5`: Cap on iteration depth. In practice, most useful results appear in rounds 0-2.

---

## Offline Precomputation

1. For each declaration, extract its symbol set (all `LConst`, `LInd`, `LConstruct` names from the expression tree). Store in `declarations.symbol_set` as a JSON array.
2. Build the global `symbol_freq` table by counting how many declarations each symbol appears in.
3. For fast lookup, build an inverted index in memory: `symbol -> set of decl_ids`. This enables efficient intersection of `symbols(d) ∩ S`.

---

## Online Query

1. Extract symbols from the query expression.
2. Run iterative selection.
3. Return results with scores.


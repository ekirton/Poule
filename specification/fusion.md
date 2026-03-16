# Fusion: RRF and Fine-Ranking Metric Fusion

Combines the independent ranked lists produced by all channels into a single result. Two stages: (1) fine-ranking metric fusion for structural channels, (2) Reciprocal Rank Fusion across all channels.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Channels: [channel-wl-kernel.md](channel-wl-kernel.md), [channel-ted.md](channel-ted.md), [channel-const-jaccard.md](channel-const-jaccard.md), [channel-mepo.md](channel-mepo.md), [channel-fts.md](channel-fts.md)
Pipeline: [pipeline.md](pipeline.md)

---

## Reciprocal Rank Fusion

All channels produce independent ranked lists. RRF combines them without learned weights.

```
function rrf_fuse(ranked_lists, k=60):
    scores = {}  # decl_id -> accumulated RRF score
    for channel_results in ranked_lists:
        for (rank, decl_id) in enumerate(channel_results, start=1):
            scores[decl_id] = scores.get(decl_id, 0) + 1.0 / (k + rank)

    fused = sorted(scores.items(), by=value, descending=True)
    return fused
```

### Channel Contributions by MCP Tool

Each MCP search tool invokes a different subset of channels:

| MCP Tool | Channels Used |
|----------|--------------|
| `search_by_structure` | WL screening + TED fine ranking + Const Jaccard, fused with RRF |
| `search_by_symbols` | MePo (primary), optionally Const Jaccard |
| `search_by_name` | FTS5 only |
| `search_by_type` | WL screening (on the parsed type expression) + MePo + FTS5, fused with RRF |

### Parameter k

`k = 60`.

---

## Fine-Ranking Metric Fusion

When multiple structural metrics are computed for the same candidate (from `search_by_structure`), they are combined with a weighted sum before RRF fusion with other channels.

### Score Computation

For candidates with node_count <= 50 (TED available):

```
structural_score = 0.15 * wl_cosine
                 + 0.40 * ted_similarity
                 + 0.30 * collapse_match
                 + 0.15 * const_jaccard
```

For candidates with node_count > 50 (TED skipped):

```
structural_score = 0.25 * wl_cosine
                 + 0.50 * collapse_match
                 + 0.25 * const_jaccard
```


### Collapse-Match Similarity

Measures whether the query tree can "collapse onto" a candidate tree by merging nodes at matching levels.

```
function collapse_match(query, candidate):
    if query is a leaf and candidate is a leaf:
        if same_category(query.label, candidate.label):
            return 1.0
        else:
            return 0.0

    if query is a leaf:
        # leaf matches against any subtree of candidate
        return max(collapse_match(query, c) for c in candidate.children)
            if candidate.children else 0.0

    if candidate is a leaf:
        return 0.0

    if not same_category(query.label, candidate.label):
        return 0.0

    # Match children greedily left-to-right
    score = 0.0
    matched = 0
    for qc in query.children:
        best = 0.0
        for cc in candidate.children:
            best = max(best, collapse_match(qc, cc))
        score += best
        matched += 1

    if matched == 0:
        return 1.0 if same_category(query.label, candidate.label) else 0.0

    return score / max(len(candidate.children), matched)
```

This metric is asymmetric: it measures how well the query structure appears within the candidate, normalized by the candidate's size. A small query that matches a subtree of a large candidate scores well.

The `same_category` grouping uses the same node categories as the TED cost model (see [channel-ted.md](channel-ted.md#cost-model)).


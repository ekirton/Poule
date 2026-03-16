# Channel 4: TED Fine Ranking

Tree Edit Distance provides precise structural comparison for small expressions. Applied only to the top candidates from WL screening, not to the full library.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Prerequisites: [channel-wl-kernel.md](channel-wl-kernel.md) (WL screening must run first)
Data structures: [data-structures.md](data-structures.md)
Used by: [fusion.md](fusion.md)

---

## Algorithm: Zhang-Shasha

The Zhang-Shasha algorithm computes the minimum-cost edit distance between two ordered labeled trees in O(n1 * n2 * min(d1, l1) * min(d2, l2)) time, where n = node count, d = depth, l = leaf count. For balanced trees this is approximately O(n^2 * m^2).

The algorithm uses dynamic programming over "keyroots" (rightmost nodes in left subtrees) and the leftmost-leaf decomposition.

The implementation must produce a minimum-cost edit distance consistent with the Zhang-Shasha algorithm's semantics.

---

## Cost Model

Edit operation costs reflect structural importance:

| Operation | Condition | Cost |
|-----------|-----------|------|
| Insert leaf node | `LRel`, `LVar`, `LCseVar`, `LSort` | 0.2 |
| Delete leaf node | `LRel`, `LVar`, `LCseVar`, `LSort` | 0.2 |
| Insert interior node | `LApp`, `LProd`, `LLambda`, `LCase`, ... | 1.0 |
| Delete interior node | `LApp`, `LProd`, `LLambda`, `LCase`, ... | 1.0 |
| Rename same category | e.g., `LConst "a"` -> `LConst "b"` | 0.0 |
| Rename cross category | e.g., `LConst _` -> `LProd` | 0.4 |

**Category definition** for same-vs-cross rename:
- Leaf constants: `LConst`, `LInd`, `LConstruct` (all in one category)
- Leaf variables: `LRel`, `LVar`, `LCseVar` (one category)
- Sorts: `LSort _` (one category)
- Binders: `LProd`, `LLambda`, `LLetIn` (one category)
- Application: `LApp` (its own category)
- Elimination: `LCase`, `LProj` (one category)
- Recursion: `LFix`, `LCoFix` (one category)

Renaming within the same category costs 0 (e.g., swapping one constant for another doesn't change the structural shape). Renaming across categories costs 0.4 (the structural role changed).

---

## Similarity Score

```
ted_similarity(T1, T2) = 1.0 - edit_distance(T1, T2) / max(node_count(T1), node_count(T2))
```

Clamped to [0, 1].

---

## Application Constraints

- Only compute TED for expression pairs where **both** trees have node_count <= 50 (after CSE normalization).
- For larger expressions, omit TED from the fusion. The WL kernel and other channels provide sufficient discrimination.
---

## Integration with WL Screening

TED is a **refinement** channel. It takes the top candidates from WL screening (typically top-200 that pass the size constraint) and re-scores them:

```
function ted_rerank(query_tree, wl_candidates, max_nodes=50):
    if node_count(query_tree) > max_nodes:
        return []  # skip TED entirely for large queries
    eligible = [(id, tree) for (id, tree) in wl_candidates
                if node_count(tree) <= max_nodes]
    results = []
    for (id, tree) in eligible:
        sim = ted_similarity(query_tree, tree)
        results.append((id, sim))
    return results
```

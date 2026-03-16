# Channel 5: Const Name Jaccard

A lightweight channel that measures overlap between the sets of constant names in two expressions, ignoring structural shape.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Data structures: [data-structures.md](data-structures.md)
Used by: [fusion.md](fusion.md)

---

## Constant Extraction

```
function extract_consts(tree):
    consts = set()
    for node in tree (recursive):
        match node.label:
            LConst name  -> consts.add(name)
            LInd name    -> consts.add(name)
            LConstruct(name, _) -> consts.add(name)
            _ -> ()
    return consts
```

---

## Jaccard Similarity

```
function const_jaccard(tree1, tree2):
    c1 = extract_consts(tree1)
    c2 = extract_consts(tree2)
    if |c1 ∪ c2| == 0:
        return 0.0
    return |c1 ∩ c2| / |c1 ∪ c2|
```

---

## Usage

This channel is computed alongside TED or as a standalone lightweight signal. During fine ranking of WL candidates:

```
function const_jaccard_rank(query_tree, candidates):
    q_consts = extract_consts(query_tree)
    results = []
    for (id, tree) in candidates:
        c_consts = extract_consts(tree)
        score = jaccard(q_consts, c_consts)
        results.append((id, score))
    return results
```

See [fusion.md](fusion.md) for how this score is combined with WL, TED, and collapse-match in the fine-ranking weighted sum.

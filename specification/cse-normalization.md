# CSE Normalization

Common Subexpression Elimination reduces expression size by replacing repeated non-constant subexpressions with fresh variables, recovering the DAG structure lost during serialization.

Applied after [coq-normalization.md](coq-normalization.md), before any channel processing.

Parent architecture: [doc/architecture/coq-normalization.md](../doc/architecture/coq-normalization.md)
Data structures: [data-structures.md](data-structures.md)

Based on CSE normalization for tree-based premise selection (see [doc/background/tree-based-retrieval.md](../doc/background/tree-based-retrieval.md)).

---

## Algorithm

Three passes over the tree.

### Pass 1: Subexpression Hashing

Compute a content hash for every subtree, bottom-up.

```
function hash_subtree(node):
    if node is a leaf:
        return tag(node.label) + to_string(node.label)
    child_hashes = [hash_subtree(c) for c in node.children]
    return MD5(tag(node.label) + "-" + join(child_hashes, "-"))
```

Where `tag()` returns the constructor name as a short prefix string: `"Rel"`, `"Const"`, `"App"`, etc.

Store the hash on every node. Time: O(n) where n = node count.

### Pass 2: Frequency Counting

Build a frequency table `freq: hash -> int` counting how many times each subtree hash appears in the entire tree.

```
function count_frequencies(node, freq):
    freq[node.hash] += 1
    for c in node.children:
        count_frequencies(c, freq)
```

### Pass 3: Variable Replacement

Replace repeated non-constant subtrees with fresh CSE variables.

```
function cse_replace(node, freq, next_var_id, seen):
    if node.label is LConst or LInd or LConstruct:
        return node  # preserve constants — they carry semantic meaning

    if freq[node.hash] > 1:
        if node.hash in seen:
            return leaf(LCseVar(seen[node.hash]))
        else:
            seen[node.hash] = next_var_id
            next_var_id += 1
            # still process children for the first occurrence
            new_children = [cse_replace(c, freq, next_var_id, seen)
                            for c in node.children]
            return {node with children = new_children}
    else:
        new_children = [cse_replace(c, freq, next_var_id, seen)
                        for c in node.children]
        return {node with children = new_children}
```

---

## Key Invariant

Constants (`LConst`, `LInd`, `LConstruct`) are never replaced, even if duplicated. They carry the semantic identity of the expression.

---


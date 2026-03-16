# Coq Expression Normalization

Transformations applied during tree construction to normalize Coq's kernel term representation for the retrieval algorithms.

**Stories**: [Epic 4: Coq-Specific Normalization](../requirements/stories/tree-search-mcp.md#epic-4-coq-specific-normalization)
**Implementation spec**: [specification/coq-normalization.md](../../specification/coq-normalization.md)

---

## Normalization Pipeline

Applied to each extracted `Constr.t` term:

```
constr_t → constr_to_tree() → recompute_depths() → assign_node_ids() → normalized tree
```

During `constr_to_tree()`, the following adaptations are applied inline.

## Adaptations

| Concern | Problem | Transform |
|---------|---------|-----------|
| N-ary `App(f, args)` | Variable fan-out distorts WL and TED similarity | Currify to binary `App(App(f, a1), a2)` |
| `Cast` nodes | Computationally irrelevant; adds structural noise | Strip — recurse into inner expression, skip cast |
| Universe annotations | Two uses of the same constant at different universe levels should be identical | Erase `'univs` parameters from `Const`, `Ind`, `Construct` |
| `Proj` vs `Case` | Semantically identical, structurally different | MVP: keep `Proj` as special interior node with projection name in label |
| Notation | Surface syntax (`x + y`) differs from kernel term (`Nat.add x y`) | No action — coq-lsp/SerAPI extraction yields kernel terms |
| Name qualification | Same definition referenced by short, partial, or fully qualified name | Always use fully qualified canonical names |
| Section variables | Open-section definitions have free variables; closed form adds binders | Index only closed (post-section) forms from `.vo` files |

## CSE Normalization

After the Coq-specific pipeline, Common Subexpression Elimination reduces expression size by replacing repeated non-constant subexpressions with fresh `LCseVar` variables. Three passes: subexpression hashing, frequency counting, variable replacement.

Key invariant: constants (`LConst`, `LInd`, `LConstruct`) are never replaced — they carry semantic identity.

Typical effect: 2-10x node reduction on expressions with heavy type annotation repetition.

See [specification/cse-normalization.md](../../specification/cse-normalization.md) for the full algorithm.

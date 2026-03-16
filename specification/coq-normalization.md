# Coq-Specific Adaptations

Transformations applied during `to_expr_tree()` conversion, before any retrieval processing. They normalize Coq's kernel term representation to match the assumptions of the tree algorithms (which were designed for Lean 4's binary-application, no-cast representation).

Parent architecture: [doc/architecture/coq-normalization.md](../doc/architecture/coq-normalization.md)
Data structures: [data-structures.md](data-structures.md)
Next step: [cse-normalization.md](cse-normalization.md)

---

## Currification of N-ary Application

**Problem**: Coq represents application as `App(f, [|a1; a2; ...; an|])` — a single node with n+1 children. Lean uses binary application `App(App(f, a1), a2)`. The WL kernel and TED algorithms expect uniform tree structure; n-ary application creates variable fan-out that distorts similarity.

**Transform**: Convert n-ary `App` to nested binary `App` during tree construction.

```
function currify_app(f, args):
    (* args = [a1; a2; ...; an] *)
    result = f
    for a in args:
        result = {label=LApp, children=[result, a], depth=..., node_id=...}
    return result
```

Example: `App(f, [a; b; c])` becomes `App(App(App(f, a), b), c)`.

**Depth assignment**: After currification, recompute depths bottom-up. The outermost `App` inherits the original `App` node's depth; inner `App` nodes get increasing depths.

**Node count impact**: An n-ary application `App(f, [a1..an])` with 1 App node becomes n App nodes. This increases the total node count. The size filtering thresholds in WL screening are calibrated on the post-currification count.

---

## Cast Stripping

**Problem**: `Cast(expr, kind, type)` nodes are computationally irrelevant — they assert a type annotation but do not change the expression's meaning. Including them adds noise to structural comparison.

**Transform**: Replace every `Cast(expr, _, _)` with its inner `expr`, recursively.

```
function strip_casts(tree):
    match tree.label:
        LCast -> strip_casts(tree.children[0])  (* the inner expression *)
        _ -> {tree with children = [strip_casts(c) for c in tree.children]}
```

Note: `LCast` is not in the `node_label` type because it is stripped before the tree is constructed. During raw `Constr.t` traversal, when encountering a `Cast` node, simply recurse into the first child and ignore the cast kind and type arguments.

---

## Universe Erasure

**Problem**: Coq's universe-polymorphic constants carry universe instance annotations: `Const(name, [u1; u2; ...])`. These are structural noise for retrieval — two uses of the same constant at different universe levels should be treated identically.

**Transform**: When constructing `LConst`, `LInd`, or `LConstruct` nodes from `Constr.t`, discard the universe instance entirely. The node carries only the qualified name.

```
(* During Constr.t traversal: *)
| Constr.Const (name, _univs) -> {label = LConst(Names.Constant.to_string name); ...}
| Constr.Ind ((name, i), _univs) -> {label = LInd(Names.MutInd.to_string name); ...}
| Constr.Construct (((name, i), j), _univs) ->
    {label = LConstruct(Names.MutInd.to_string name, j); ...}
```

---

## Projection Normalization

**Problem**: Coq has two ways to project a field from a record: `Proj(projection, term)` and the equivalent `Case` elimination. These are semantically identical but structurally different.

**Transform**: Treat `Proj` as a special interior node with one child (the term being projected). The projection name goes into the label.

```
| Constr.Proj (proj, term) ->
    let proj_name = Names.Projection.to_string proj in
    {label = LProj(proj_name); children = [convert(term)]; ...}
```

This preserves the projection in the tree. Two uses of the same projection will match via WL labels.

---

## Notation Transparency

**Problem**: Coq's notation system allows expressions like `x + y` which are parsed into kernel terms like `Nat.add x y`. The search system must index kernel terms, not surface syntax, so that notation differences don't affect retrieval.

**Action**: No transform needed. Extraction produces kernel-level `Constr.t` terms, which are already notation-expanded. Index the kernel terms as-is. The pretty-printed surface form (with notation) is stored separately for display and full-text search.

---

## Fully Qualified Names

**Problem**: Coq's section and module system means the same definition can be referenced by short name (`add_comm`), partially qualified name (`Nat.add_comm`), or fully qualified name (`Coq.Arith.PeanoNat.Nat.add_comm`). The search index must use a canonical form.

**Action**: Always use fully qualified names in `LConst`, `LInd`, and `LConstruct` labels. During extraction, resolve all names to their fully qualified canonical form using the Coq environment.

```
(* Use the kernel's canonical name resolution: *)
let fqn = Names.Constant.to_string (Names.Constant.canonical const_name)
```

Store the fully qualified name in `declarations.name`. The shorter display name can be stored separately or computed on demand.

---

## Section Variable Abstraction

**Problem**: Definitions inside Coq sections reference section variables as free variables. When the section is closed, these become universally quantified parameters. The indexed form should be the closed (post-section) form.

**Action**: Index only the closed form of each definition. If extracting while a section is open, either:
- Wait for the section to close and extract the discharged form, or
- Manually abstract over section variables (adding `Prod` binders for each section variable)

When indexing from compiled `.vo` files, sections are already closed and no special handling is needed.

---

## Normalization Pipeline

The full normalization pipeline, applied to each extracted `Constr.t` term:

```
function coq_normalize(constr_t):
    tree = constr_to_tree(constr_t)     # raw conversion, handling:
                                         #   - Cast: skip, recurse into child
                                         #   - App: currify to binary
                                         #   - Const/Ind/Construct: erase universes, fully qualify
                                         #   - Proj: keep as LProj node
    tree = recompute_depths(tree)        # set depth field on all nodes
    tree = assign_node_ids(tree)         # set unique node_id on all nodes
    return tree
```

After `coq_normalize`, the tree is ready for CSE normalization (see [cse-normalization.md](cse-normalization.md)) and then channel processing.

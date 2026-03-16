# Core Data Structures

Shared types used by all retrieval channels. Every channel consumes `expr_tree` as input and produces `scored_result` as output.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)

---

## Expression Tree

The internal tree representation used by all retrieval channels. Every Coq `Constr.t` term is converted to this form after extraction.

```ocaml
type node_label =
  | LRel of int                  (* de Bruijn index *)
  | LVar of string               (* named variable *)
  | LSort of sort_kind           (* Prop | Set | Type *)
  | LProd                        (* forall / dependent product *)
  | LLambda                      (* fun / lambda *)
  | LLetIn                       (* let ... in *)
  | LApp                         (* application — always binary after currification *)
  | LConst of string             (* fully qualified constant name *)
  | LInd of string               (* inductive type name *)
  | LConstruct of string * int   (* constructor: inductive name, index *)
  | LCase                        (* match / pattern match *)
  | LFix of int                  (* fixpoint, mutual index *)
  | LCoFix of int                (* cofixpoint, mutual index *)
  | LProj of string              (* primitive projection name *)
  | LInt of int                  (* primitive integer *)
  | LCseVar of int               (* CSE-introduced variable, see cse-normalization.md *)

and sort_kind = Prop | Set | TypeUniv

type expr_tree = {
  label: node_label;
  children: expr_tree list;
  depth: int;          (* distance from root, set during construction *)
  node_id: int;        (* unique id within this tree, for WL bookkeeping *)
}
```

**Construction rule**: children are ordered left-to-right as they appear in the kernel term. For `Prod(name, ty, body)`, children are `[ty_tree; body_tree]`. For `App(f, a)` (after currification), children are `[f_tree; a_tree]`.

A tree's **node count** is the total number of nodes (interior + leaf). Store this on the declaration record for size filtering.

---

## WL Histogram

A sparse map from hashed labels to occurrence counts.

```ocaml
type wl_histogram = (string, int) Hashtbl.t
(* key: MD5 hex string of the WL label
   value: number of nodes carrying that label *)
```

Stored in SQLite as a JSON object `{"<md5>": count, ...}`. Typical size: 50-500 entries for a declaration of 20-200 nodes.

---

## Symbol Set and Frequency Table

```ocaml
type symbol = string  (* fully qualified constant/inductive/constructor name *)

type symbol_set = symbol list
(* Per-declaration: the set of distinct symbols appearing in the expression.
   Extracted during indexing. Stored as JSON array in declarations.symbol_set. *)
```

The global `symbol_freq` table maps each symbol to the number of declarations in the library that mention it. Built once during indexing; used by MePo weighting (see [channel-mepo.md](channel-mepo.md)).

---

## Search Result (Internal)

```ocaml
type scored_result = {
  decl_id: int;        (* declarations.id *)
  channel: string;     (* which channel produced this result *)
  rank: int;           (* 1-based rank within the channel *)
  raw_score: float;    (* channel-specific score *)
}
```

After fusion, results carry an `rrf_score` and a combined rank. See [fusion.md](fusion.md).

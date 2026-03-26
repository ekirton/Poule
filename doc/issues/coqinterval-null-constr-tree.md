# CoqInterval: NULL constr_tree for nth_map2_dflt

**Date:** 2026-03-26
**Database:** index-coqinterval.db (CoqInterval 4.11.4, Coq 9.1.1)
**Severity:** Low
**Affected declaration:** `Interval.Missing.MathComp.nth_map2_dflt` (id=1641)

---

## Problem

During extraction of CoqInterval 4.11.4, the declaration
`Interval.Missing.MathComp.nth_map2_dflt` was stored with a NULL `constr_tree`
blob, an empty `symbol_set`, a `node_count` of 1, and no WL vector row. This
is the only declaration out of 20,156 with a NULL tree.

Stored values:

| Column | Value |
|--------|-------|
| kind | lemma |
| module | Interval.Missing.MathComp |
| statement | Present (~7 KB expanded proof term) |
| type_expr | Present (correct type signature) |
| constr_tree | **NULL** |
| node_count | 1 |
| symbol_set | `[]` |
| has_proof_body | 1 |
| WL vector | **missing** |

## Root cause

The `statement` column contains the full expanded proof body (a deeply nested
`list_ind` / `match` / `eq_ind_r` term) rather than a compact
`Lemma name : type.` form. This indicates the backend's `Print` output returned
the proof term rather than just the type, which is the expected behavior for a
transparent lemma whose body is not hidden behind `Qed`.

The normalization pipeline (`coq_normalize` / `cse_normalize`) either failed or
was never invoked for this declaration. The most likely scenario:

1. The coq-lsp `Search` or `About` query returned metadata without a kernel
   `ConstrNode` (the declaration came through the metadata-only path).
2. Without a kernel term, tree normalization was skipped.
3. The pipeline stored a stub `constr_tree = NULL` and `node_count = 1`.
4. Because no tree was produced, `extract_consts()` returned an empty symbol
   set and no WL histogram was computed.

The `node_count = 1` with `constr_tree = NULL` is internally inconsistent: if
the tree is NULL the node count should reflect that (or the schema should
enforce `constr_tree IS NOT NULL`). The current `CHECK(node_count > 0)`
constraint prevents storing 0, so the pipeline appears to use 1 as a sentinel.

## Impact

- **Structure search:** This declaration will never appear in results from
  `search_by_structure` (tree-based similarity via WL kernel or TED).
- **Symbol search:** This declaration will never appear in `search_by_symbols`
  (MePo channel) because its symbol set is empty.
- **Type search:** Will not match type-based queries since there is no tree to
  compare against.
- **Name/FTS search:** Still works. Searching for "nth_map2_dflt" by name
  returns this declaration correctly.
- **Dependencies:** The declaration has no outgoing dependency edges (since
  symbol set is empty and Print Assumptions produced nothing resolvable
  within the library). It may still be a dependency target for other
  declarations.

Practical impact is negligible: this is 1 of 20,156 declarations (0.005%), in a
MathComp compatibility shim module (`Interval.Missing.MathComp`).

## Reproduction

```sql
SELECT id, name, kind, module, node_count, symbol_set,
       constr_tree IS NULL AS tree_null
FROM declarations
WHERE constr_tree IS NULL;
-- Returns: 1641 | Interval.Missing.MathComp.nth_map2_dflt | lemma | ... | 1 | [] | 1

SELECT COUNT(*) FROM wl_vectors WHERE decl_id = 1641;
-- Returns: 0
```

## Suggested resolution

1. **Investigate the backend path:** Determine why `list_declarations()` did not
   return a `ConstrNode` for this declaration. Check whether coq-lsp's `About`
   for `Interval.Missing.MathComp.nth_map2_dflt` returns a kernel term or only
   metadata. If it only returns metadata, the issue is upstream in coq-lsp.

2. **Fallback normalization:** If a kernel term is unavailable, consider parsing
   the `type_expr` string through the `TypeExprParser` to produce a partial
   tree. This would enable at least type-based search even without the full
   kernel term.

3. **Schema hardening:** Consider whether `constr_tree` should be `NOT NULL`
   with a well-defined stub tree for cases where normalization fails, or
   whether `node_count` should be allowed to be 0 (removing the
   `CHECK(node_count > 0)` constraint) to honestly represent the absence of
   tree data.

4. **Sentinel audit:** Search all databases for `node_count = 1` with empty
   `symbol_set` to detect other declarations that may have hit the same
   fallback path silently:
   ```sql
   SELECT COUNT(*) FROM declarations
   WHERE node_count = 1 AND symbol_set = '[]';
   ```

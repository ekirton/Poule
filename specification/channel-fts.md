# Channel 3: FTS5 Full-Text Search

Lexical search over declaration names, pretty-printed statements, and module paths using SQLite's built-in FTS5 engine with BM25 ranking.

Parent architecture: [doc/architecture/retrieval-pipeline.md](../doc/architecture/retrieval-pipeline.md)
Used by: [fusion.md](fusion.md)

---

## Index Construction

The FTS5 virtual table is defined in the schema (see design doc Section 8):

```sql
CREATE VIRTUAL TABLE declarations_fts USING fts5(
  name,
  statement,
  module,
  content=declarations,
  content_rowid=id,
  tokenize='porter unicode61 remove_diacritics 2'
);
```

**Tokenizer configuration**: `porter unicode61` applies Porter stemming and Unicode-aware tokenization. `remove_diacritics 2` handles accented characters. This means searching for "commut" will match "commutativity", "commutative", "Nat.add_comm", etc.

**Population** (run after all declarations are inserted):

```sql
INSERT INTO declarations_fts(declarations_fts) VALUES('rebuild');
```

---

## Online Query

```sql
SELECT d.id, d.name, d.statement, d.module, d.kind,
       bm25(declarations_fts, 10.0, 1.0, 5.0) AS score
FROM declarations_fts
JOIN declarations d ON d.id = declarations_fts.rowid
WHERE declarations_fts MATCH ?
ORDER BY score
LIMIT ?;
```

The `bm25()` weights `(10.0, 1.0, 5.0)` bias toward name matches (weight 10) over statement matches (weight 1), with module matches in between (weight 5). Tune these based on retrieval quality experiments.

---

## Query Preprocessing

Before passing to FTS5 MATCH:

1. If the input looks like a qualified name (`Nat.add_comm`, `List.rev_*`), convert to an FTS5 prefix query: `"Nat" AND "add" AND "comm"` or `"List" AND "rev" AND *`.
2. If the input is a natural-language fragment, pass it as-is (FTS5 handles implicit OR).
3. Escape FTS5 special characters (`*`, `"`, `(`, `)`) when they are not intentional wildcards.

---


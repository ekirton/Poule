# Storage

SQLite database schema for the search index. Single file, no external services.

**Stories**: [Epic 1: Library Indexing](../requirements/stories/tree-search-mcp.md#epic-1-library-indexing)

---

## Schema

```sql
-- Core declarations
CREATE TABLE declarations (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,          -- fully qualified
  module TEXT NOT NULL,
  kind TEXT NOT NULL,                 -- lemma, theorem, definition, ...
  statement TEXT NOT NULL,            -- pretty-printed
  type_expr TEXT NOT NULL,            -- pretty-printed type
  constr_tree BLOB,                   -- serialized CSE-normalized tree
  node_count INTEGER NOT NULL,
  symbol_set TEXT NOT NULL            -- JSON array of symbol names
);

-- Dependency edges
CREATE TABLE dependencies (
  src INTEGER REFERENCES declarations(id),
  dst INTEGER REFERENCES declarations(id),
  relation TEXT NOT NULL,             -- uses, instance_of, ...
  PRIMARY KEY (src, dst, relation)
);

-- Precomputed WL vectors (sparse histograms as JSON)
CREATE TABLE wl_vectors (
  decl_id INTEGER REFERENCES declarations(id),
  h INTEGER NOT NULL,                 -- WL iteration count
  histogram TEXT NOT NULL,            -- JSON {label: count}
  PRIMARY KEY (decl_id, h)
);

-- Symbol frequency table
CREATE TABLE symbol_freq (
  symbol TEXT PRIMARY KEY,
  freq INTEGER NOT NULL
);

-- Full-text search
CREATE VIRTUAL TABLE declarations_fts USING fts5(
  name, statement, module,
  content=declarations, content_rowid=id
);
```

## Design Decisions

**Single database file**: The entire index — declarations, dependencies, WL vectors, symbol frequencies, and FTS5 index — lives in one SQLite file. This makes the index portable (copy one file) and eliminates external service dependencies.

**JSON for sparse data**: WL histograms and symbol sets are stored as JSON text. This keeps the schema simple and avoids a separate table per histogram entry. At query time, histograms are loaded into memory as hash maps.

**Content-synced FTS5**: The `content=declarations` parameter makes FTS5 a content-synced index — it reads from the declarations table rather than storing a copy. The `content_rowid=id` maps FTS5 rowids to declaration IDs.

**WL vectors at multiple h values**: Storing histograms at h=1,3,5 allows experimentation with different WL iteration depths without re-extracting. h=3 is the primary query depth.

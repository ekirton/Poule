# Knowledge Graph for Coq Libraries

Design rationale for extending the search system with a knowledge graph over Coq library structure.

**Stories**: Future work beyond the initial tree-based MVP.

---

## Context

The current system stores dependency edges in a flat relational table (SQLite `dependencies` table). This document captures design decisions for evolving toward a richer knowledge graph that exploits Coq's type-theoretic structure for retrieval.

---

## Why a Knowledge Graph

The background research shows that graph structure encodes 25-34% additional retrieval signal beyond text embeddings:

- The RGCN-augmented system (Petrovcic et al., 2025) achieves +26% Recall@10 over ReProver by propagating information through a heterogeneous dependency graph.
- LeanExplore combines PageRank over the dependency graph with semantic and lexical signals.
- Graph2Tac (ICML 2024) demonstrates that GNN representations over Coq's dependency structure outperform CoqHammer, Proverbot9001, and transformer baselines.
- LeanHammer achieves +21% improvement by taking the union of neural and MePo (symbol-overlap) selections, confirming that heterogeneous signals are complementary.

Standard GraphRAG (entity-extraction → community-hierarchy → community-summary) is a poor fit: GraphRAG-Bench (2025) found that all GraphRAG methods degraded LLM accuracy on mathematical text. A formal-math knowledge graph must be constructed from the prover's kernel-level information, not from NLP-based entity extraction.

---

## Graph Structure

Based on patterns from MMLKG (the only published formal math knowledge graph, over Mizar), Graph2Tac, and the RGCN work:

### Nodes

Definitions, lemmas, theorems, tactics, modules, sections, type classes, instances, notations. Each node annotated with:
- Formal statement and type signature
- Source location
- Informalized description (LLM-generated, for neural retrieval)
- Embedding vector (when neural retrieval is added)
- Symbol set (for MePo-style retrieval)

### Edges (from kernel-level information)

| Edge Type | Source | Description |
|-----------|--------|-------------|
| `DEPENDS_ON` | Coq's dependency tracking | Definition X references definition Y |
| `PROVES_USING` | Premise annotations (if available) | Proof of X uses lemma Y |
| `HAS_TYPE` | Type checking | Term X has type T |
| `INSTANCE_OF` | Typeclass resolution | Instance X implements class C |
| `IN_MODULE` | Module system | Definition X belongs to module M |
| `REWRITES_TO` | Rewrite rules | Lemma X rewrites pattern P to Q |
| `UNFOLDS_TO` | Definitional equality | Definition X unfolds to body B |

---

## Hybrid Graph + Vector + Symbolic Retrieval

The most effective unexplored architecture combines three complementary signals:

1. **Vector retrieval** (embedding similarity) for semantic matching
2. **Graph traversal** (dependency walks, PageRank) for structural relevance
3. **Symbolic matching** (type unification, symbol overlap) for syntactic precision

Each signal captures relationships the others miss:
- Vector retrieval finds semantically related but syntactically dissimilar items
- Graph traversal finds structurally connected items regardless of text similarity
- Symbolic matching finds precise syntactic connections

Fusion options: reciprocal rank fusion (no training needed), learned score fusion (requires validation data), or LLM-based reasoning over multi-channel results (via MCP).

---

## Technology Considerations

| Option | Strengths | Weaknesses |
|--------|-----------|------------|
| **Neo4j** | Native vector search (5.x+), Cypher, MCP server exists | External service; heavyweight for single-user |
| **SQLite + custom graph layer** | No external dependencies; sufficient for corpus scale; already used | Limited graph query expressiveness |
| **In-memory graph + FAISS** | Fastest for small corpora | No persistence; memory bound |

At the 50-200K node scale of Coq libraries, the current SQLite-based dependency table may be sufficient with added graph query logic. A move to Neo4j is warranted only for multi-user or web-service deployment.

---

## Relationship to Current System

The current `dependencies` table already stores `DEPENDS_ON` edges. This feature extends that foundation:

1. **Phase 1 (current)**: Flat dependency table, used by `find_related` MCP tool
2. **Phase 2**: Add PageRank scoring over dependency graph as a retrieval signal in fusion
3. **Phase 3**: Add additional edge types (typeclass instances, rewrite rules) as Coq extraction capabilities improve
4. **Phase 4**: RGCN-style message passing for graph-augmented embeddings (requires neural retrieval from [neural-retrieval-evolution.md](neural-retrieval-evolution.md))

---

## References

See [background research index](../background/index.md), particularly:
- [Semantic search survey](../background/semantic-search.md) — Section 4 on knowledge graphs
- [Neural retrieval survey](../background/neural-retrieval.md) — Section 6 on hybrid retrieval
- [Vector DB and RAG survey](../background/vector-db-rag-formal-math-research.md) — ColBERT gap analysis

# Dependency Graph Extraction — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

Lineage: Poule already exposes `find_related` for navigating direct dependencies and `visualize_dependencies` for rendering subgraphs. This initiative wraps coq-dpdgraph to deliver richer transitive dependency analysis — full project-level dependency graphs, cycle detection, impact analysis, and module-level dependency summaries — as MCP tools.

## 1. Business Goals

Large Coq developments (CompCert, MathComp, Iris) contain thousands of interdependent definitions, lemmas, and modules. Understanding the dependency structure at scale is essential for safe refactoring, proof maintenance, and onboarding new contributors. Today, developers rely on manual inspection or ad-hoc scripts to answer questions like "what breaks if I change this definition?" or "which modules are tightly coupled?"

This initiative delivers dependency graph extraction and analysis capabilities that surface transitive dependency structure, identify architectural risks (cycles, high fan-in nodes), and quantify coupling at the module level. It builds on Poule's existing direct-dependency navigation and extends it into a complete dependency intelligence layer.

**Success metrics:**
- Compute the full transitive dependency closure for any definition in the Coq standard library in under 5 seconds
- Correctly identify all definitions affected by a change to any single definition in a project of ≥ 500 definitions
- Detect all dependency cycles in a project and report them with zero false positives
- Produce module-level dependency summaries that match hand-verified ground truth on a validation set of ≥ 3 projects
- Integrate with Poule's existing `visualize_dependencies` tool so that extracted graphs can be rendered without additional tooling

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq proof engineers | Understand what breaks before refactoring a definition or lemma; identify safe refactoring boundaries | Primary |
| Library maintainers | Detect dependency cycles, identify tightly coupled modules, plan modularization efforts | Primary |
| Onboarding developers | Explore unfamiliar codebases by understanding which modules depend on what, and which definitions are foundational | Secondary |
| AI researchers | Leverage dependency graph structure as features for premise selection and proof search models | Tertiary |

---

## 3. Competitive Context

**Existing Poule capabilities:**
- `find_related`: navigates direct (one-hop) dependencies of a given definition — useful for local exploration but insufficient for understanding transitive impact or architectural structure
- `visualize_dependencies`: renders a dependency subgraph as a visual diagram — currently limited to the subgraph already known to the user

**coq-dpdgraph (upstream tool):**
- Extracts full dependency graphs from compiled Coq developments as `.dot` files
- Provides transitive closure computation and cycle detection at the command line
- Not exposed as an interactive tool or MCP service; requires manual invocation and post-processing

**Gap this initiative fills:**
- No existing tool provides interactive, on-demand transitive dependency queries within an editing session
- No existing tool provides reverse-dependency (impact) analysis answering "what depends on X?"
- No existing tool provides module-level dependency summaries for architectural assessment
- Wrapping coq-dpdgraph behind MCP tools brings its capabilities into the Claude Code workflow without requiring users to learn its CLI or process its output formats

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R7-P0-1 | Compute the transitive dependency closure for a given definition, lemma, or theorem, returning the complete set of definitions it transitively depends on |
| R7-P0-2 | Compute reverse dependencies (impact analysis) for a given definition: return all definitions, lemmas, and theorems that transitively depend on it |
| R7-P0-3 | Detect all dependency cycles in a project and report each cycle as an ordered list of participants |
| R7-P0-4 | Expose dependency graph extraction and analysis as MCP tools callable from Claude Code |
| R7-P0-5 | Build on coq-dpdgraph output as the underlying data source for dependency graph construction |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R7-P1-1 | Produce module-level dependency summaries: for each module, list its inbound and outbound module-level dependencies with fan-in and fan-out counts |
| R7-P1-2 | Support filtering dependency queries by depth (e.g., "show only dependencies within 3 hops") |
| R7-P1-3 | Support filtering dependency queries by scope (e.g., "only dependencies within this module" or "exclude standard library") |
| R7-P1-4 | Integrate extracted dependency graphs with Poule's existing `visualize_dependencies` tool so that transitive closures and impact sets can be rendered visually |
| R7-P1-5 | Cache extracted dependency graphs per project to avoid redundant recomputation when multiple queries target the same project |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R7-P2-1 | Rank impact analysis results by a coupling metric (e.g., number of transitive dependents) to highlight the highest-risk definitions |
| R7-P2-2 | Identify strongly connected components in the dependency graph and report their sizes as an architectural health indicator |
| R7-P2-3 | Support incremental graph updates when individual source files change, without full project re-extraction |
| R7-P2-4 | Export dependency graphs in standard formats (DOT, JSON adjacency list) for consumption by external tools |

---

## 5. Scope Boundaries

**In scope:**
- Transitive dependency closure computation (forward and reverse)
- Cycle detection and reporting
- Module-level dependency summaries
- Depth and scope filtering for dependency queries
- MCP tool exposure for interactive use within Claude Code
- Integration with existing Poule visualization capabilities
- Caching of extracted graphs for query performance

**Out of scope:**
- Modification of coq-dpdgraph itself (this initiative wraps it, does not fork it)
- Dependency analysis for languages other than Coq/Rocq
- Proof trace extraction (covered by the Training Data Extraction initiative)
- Automated refactoring or code modification based on dependency analysis
- Web interface or standalone GUI for dependency visualization
- Build system integration or CI pipeline tooling

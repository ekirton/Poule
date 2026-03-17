# User Stories: Dependency Graph Extraction

Derived from [doc/requirements/dependency-graph-extraction.md](../dependency-graph-extraction.md).

---

## Epic 1: Transitive Dependency Closure

### 1.1 Compute Forward Transitive Closure

**As a** Coq proof engineer,
**I want to** query the full transitive dependency closure of a given definition,
**so that** I can understand everything a definition ultimately depends on before modifying upstream code.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a fully qualified definition name in a compiled Coq project WHEN the transitive closure tool is invoked THEN it returns the complete set of definitions, lemmas, axioms, and constructors that the target transitively depends on
- GIVEN a definition with no dependencies beyond itself WHEN the transitive closure tool is invoked THEN it returns an empty dependency set
- GIVEN a definition in the Coq standard library WHEN the transitive closure tool is invoked THEN it returns results in under 5 seconds

**Traces to:** R7-P0-1, R7-P0-4, R7-P0-5

### 1.2 Compute Reverse Dependencies (Impact Analysis)

**As a** Coq proof engineer planning a refactoring,
**I want to** query all definitions that transitively depend on a given definition,
**so that** I can assess the blast radius of a change before making it.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a fully qualified definition name WHEN the impact analysis tool is invoked THEN it returns all definitions, lemmas, and theorems in the project that transitively depend on the target
- GIVEN a definition that nothing depends on WHEN the impact analysis tool is invoked THEN it returns an empty set
- GIVEN a foundational definition used throughout a project WHEN the impact analysis tool is invoked THEN the result includes all transitive dependents, not just direct dependents

**Traces to:** R7-P0-2, R7-P0-4, R7-P0-5

---

## Epic 2: Cycle Detection

### 2.1 Detect Dependency Cycles

**As a** library maintainer,
**I want to** detect all dependency cycles in my Coq project,
**so that** I can identify and eliminate circular dependencies that complicate maintenance and compilation.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project with one or more dependency cycles WHEN the cycle detection tool is invoked THEN it returns each cycle as an ordered list of fully qualified participant names
- GIVEN a Coq project with no dependency cycles WHEN the cycle detection tool is invoked THEN it returns an empty result indicating no cycles were found
- GIVEN a project with multiple overlapping cycles WHEN the cycle detection tool is invoked THEN each distinct cycle is reported separately with zero false positives

**Traces to:** R7-P0-3, R7-P0-4, R7-P0-5

---

## Epic 3: Module-Level Dependency Summaries

### 3.1 Produce Module-Level Summaries

**As a** library maintainer assessing project architecture,
**I want to** see a module-level dependency summary listing inbound and outbound dependencies with fan-in and fan-out counts for each module,
**so that** I can identify tightly coupled modules and plan modularization efforts.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project WHEN the module summary tool is invoked THEN it returns a list of modules, each with its inbound dependencies (modules that depend on it) and outbound dependencies (modules it depends on)
- GIVEN a module summary entry WHEN it is inspected THEN it includes fan-in count (number of modules depending on this module) and fan-out count (number of modules this module depends on)
- GIVEN a project with a single module WHEN the module summary tool is invoked THEN it returns that module with zero inbound and zero outbound module-level dependencies

**Traces to:** R7-P1-1, R7-P0-4

---

## Epic 4: Filtering by Depth and Scope

### 4.1 Filter Dependencies by Depth

**As a** Coq proof engineer exploring a large codebase,
**I want to** limit dependency queries to a specified depth (number of hops),
**so that** I can focus on nearby dependencies without being overwhelmed by the full transitive closure.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a definition and a depth limit of N WHEN the transitive closure tool is invoked with depth=N THEN it returns only dependencies reachable within N hops
- GIVEN a depth limit of 1 WHEN the transitive closure tool is invoked THEN it returns only direct dependencies (equivalent to `find_related`)
- GIVEN a depth limit of 0 WHEN the transitive closure tool is invoked THEN it returns an empty dependency set

**Traces to:** R7-P1-2, R7-P0-4

### 4.2 Filter Dependencies by Scope

**As a** Coq proof engineer working within a specific module,
**I want to** restrict dependency queries to a given scope (e.g., within a module, excluding the standard library),
**so that** I can focus on project-internal dependencies relevant to my current task.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a scope filter restricting to a specific module WHEN a dependency query is invoked THEN only dependencies within that module are included in the result
- GIVEN a scope filter excluding the standard library WHEN a dependency query is invoked THEN no standard library definitions appear in the result
- GIVEN no scope filter WHEN a dependency query is invoked THEN all dependencies are included regardless of their module (default behavior)

**Traces to:** R7-P1-3, R7-P0-4

---

## Epic 5: Visualization Integration

### 5.1 Render Extracted Graphs with Existing Visualization

**As a** Coq proof engineer,
**I want to** visualize the results of transitive closure and impact analysis queries using Poule's existing `visualize_dependencies` tool,
**so that** I can see dependency structure graphically without switching to external tools.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a transitive closure result WHEN the user requests visualization THEN the result is rendered using Poule's `visualize_dependencies` tool
- GIVEN an impact analysis result WHEN the user requests visualization THEN the affected definitions are rendered as a dependency subgraph
- GIVEN a cycle detection result WHEN the user requests visualization THEN each cycle is highlighted in the rendered graph

**Traces to:** R7-P1-4, R7-P0-4

---

## Epic 6: Graph Caching

### 5.2 Cache Extracted Dependency Graphs

**As a** Coq proof engineer making multiple dependency queries against the same project,
**I want** extracted dependency graphs to be cached,
**so that** subsequent queries are fast without redundant recomputation.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project whose dependency graph has already been extracted WHEN a new dependency query is made against the same project THEN the cached graph is reused without re-extraction
- GIVEN a cached graph WHEN the underlying project source files have changed THEN the cache is invalidated and the graph is re-extracted on the next query
- GIVEN no prior extraction for a project WHEN a dependency query is made THEN the graph is extracted, the query is answered, and the graph is cached for future queries

**Traces to:** R7-P1-5

---

## Epic 7: Advanced Analysis

### 7.1 Rank Impact by Coupling Metric

**As a** library maintainer prioritizing technical debt,
**I want** impact analysis results ranked by a coupling metric such as transitive dependent count,
**so that** I can identify the highest-risk definitions that would cause the most breakage if changed.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN an impact analysis result WHEN ranking is requested THEN the results are sorted by number of transitive dependents in descending order
- GIVEN a ranked result WHEN it is inspected THEN each entry includes the coupling metric value alongside the definition name

**Traces to:** R7-P2-1

### 7.2 Identify Strongly Connected Components

**As a** library maintainer assessing architectural health,
**I want to** identify strongly connected components in the dependency graph and see their sizes,
**so that** I can locate clusters of mutual dependency that may warrant refactoring.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a Coq project WHEN strongly connected component analysis is invoked THEN it returns each component as a list of participant definitions with the component size
- GIVEN a project with no cycles WHEN the analysis is invoked THEN every strongly connected component has size 1

**Traces to:** R7-P2-2

### 7.3 Export Dependency Graphs

**As a** developer integrating with external analysis tools,
**I want to** export extracted dependency graphs in standard formats (DOT, JSON adjacency list),
**so that** I can use external visualization or analysis tools on the graph data.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN an extracted dependency graph WHEN export to DOT format is requested THEN the output is a valid DOT file loadable by Graphviz
- GIVEN an extracted dependency graph WHEN export to JSON adjacency list is requested THEN the output is valid JSON with each node listing its outbound edges

**Traces to:** R7-P2-4

# Compatibility Analysis

Dependency scanning, opam metadata resolution, constraint parsing, conflict detection, explanation building, and resolution suggestion for cross-library compatibility analysis of Coq projects.

**Architecture**: [compatibility-analysis.md](../doc/architecture/compatibility-analysis.md), [component-boundaries.md](../doc/architecture/component-boundaries.md)

---

## 1. Purpose

Define the compatibility analysis engine that extracts dependency declarations from Coq project files, queries opam repository metadata for version constraints across the full transitive dependency tree, determines whether a mutually satisfying combination of package versions exists, and produces structured conflict reports with plain-language explanations and resolution suggestions -- enabling the `/check-compat` slash command to surface dependency conflicts before the user attempts an installation.

## 2. Scope

**In scope**: Dependency scanning from `.opam`, `dune-project`, and `_CoqProject` files; hypothetical dependency addition; opam metadata resolution with transitive expansion; opam version constraint parsing and interval normalization; per-resource conflict detection via constraint intersection; minimal conflict set extraction; plain-language explanation building with transitive chain tracing; resolution suggestion (upgrade, downgrade, alternative); target Coq version pinning; package name validation against the opam repository.

**Out of scope**: `/check-compat` slash command orchestration (agentic, owned by Claude Code), MCP protocol handling (owned by mcp-server), build system detection logic (reused from build-system-integration, not duplicated), opam switch modification (all opam commands are read-only), dependency resolution for non-opam package managers, automatic application of fixes to project files.

## 3. Definitions

| Term | Definition |
|------|-----------|
| Shared resource | A package that appears as a dependency of more than one path through the constraint tree; Coq version is always a shared resource for Coq projects |
| Constraint intersection | The set of versions satisfying all constraints on a shared resource simultaneously; empty intersection means conflict |
| Minimal conflict set | The smallest subset of constraints on a shared resource that produce an empty intersection |
| Hypothetical addition | A package appended to the dependency set for analysis without modifying project files |
| Target Coq version | A user-specified Coq version that pins the Coq constraint during conflict detection |
| Version interval | A contiguous range of versions defined by lower and upper bounds, each optionally inclusive |
| Disjunctive normal form | A version constraint normalized to a union of intersections (list of intervals) |
| Tilde sort | Opam version ordering rule: tilde (`~`) sorts before any other character at the same position, so `8.18~` < `8.18` |

## 4. Behavioral Requirements

### 4.1 Dependency Scanning

#### scan_dependencies(project_dir, hypothetical_additions)

- REQUIRES: `project_dir` is an absolute path to an existing directory. `hypothetical_additions` is a list of package name strings, or empty.
- ENSURES: Detects the build system using the Build System Adapter's detection logic. Parses each located configuration file for dependency declarations. Merges declarations across files (union, with source tracking). Appends hypothetical additions (marked as `hypothetical = true`). Validates all package names against the opam repository. Returns a DependencySet.
- MAINTAINS: No project files are modified. Build system detection logic is reused, not duplicated.

When a `.opam` file is present, the scanner shall extract entries from the `depends` field.

When a `dune-project` file is present, the scanner shall extract entries from `(depends ...)` stanzas.

When a `_CoqProject` file is present, the scanner shall infer opam package names from `-Q` and `-R` logical path roots using the `coq-` prefix convention (e.g., logical root `Mathcomp` maps to `coq-mathcomp-ssreflect`). When inference is ambiguous, the scanner shall include all candidates and flag the ambiguity in the DependencySet.

When a package name is not found in the opam repository, the scanner shall add it to `unknown_packages` and continue scanning remaining packages.

When the same package appears in multiple files, the scanner shall retain one entry per file source (preserving source tracking).

> **Given** a project directory containing `mylib.opam` with `depends: ["coq" {>= "8.18"} "coq-mathcomp-ssreflect"]`
> **When** `scan_dependencies(project_dir, [])` is called
> **Then** the DependencySet contains two entries: `coq` with constraint `>= "8.18"` and `coq-mathcomp-ssreflect` with no constraint, both with `source_file` pointing to `mylib.opam`

> **Given** a project directory with `_CoqProject` containing `-Q src Mathcomp`
> **When** `scan_dependencies(project_dir, [])` is called
> **Then** the DependencySet contains an entry for `coq-mathcomp-ssreflect` inferred from the `Mathcomp` logical root

> **Given** a valid project and `hypothetical_additions = ["coq-equations"]`
> **When** `scan_dependencies(project_dir, ["coq-equations"])` is called
> **Then** the DependencySet contains `coq-equations` with `hypothetical = true`, in addition to all file-sourced dependencies

### 4.2 Opam Metadata Resolution

#### resolve_metadata(dependency_set)

- REQUIRES: `dependency_set` is a valid DependencySet with at least one dependency (excluding unknown packages). `opam` is on PATH.
- ENSURES: For each dependency, queries opam for the `depends`, `version`, and `all-versions` fields. Recursively resolves transitive dependencies with cycle detection. Caches opam show results within the analysis run (each package queried at most once). Returns a ResolvedConstraintTree.
- MAINTAINS: Only read-only opam commands are invoked (`opam show`). No opam switch state is modified. Each opam query spawns a fresh subprocess.

When a circular dependency is encountered in the opam metadata, the resolver shall record the cycle in the constraint tree and stop expanding that path. The cycle shall not block analysis of other paths.

When an opam subprocess times out, the resolver shall record the timeout for the affected package and continue resolving remaining packages.

> **Given** a DependencySet containing `coq-mathcomp-ssreflect`
> **When** `resolve_metadata(dependency_set)` is called
> **Then** the ResolvedConstraintTree contains `coq-mathcomp-ssreflect` as a root dependency, with its transitive dependencies (including `coq`) as nodes, and constraint edges carrying version constraints between them

> **Given** packages A depends on B, B depends on C, C depends on A (circular)
> **When** `resolve_metadata` encounters the cycle at C -> A
> **Then** the cycle is noted in the tree, expansion stops on that path, and analysis proceeds for all non-cyclic branches

> **Given** `opam show` for package X exceeds the subprocess timeout
> **When** `resolve_metadata` processes X
> **Then** X is recorded with an `OPAM_TIMEOUT` indication, and remaining packages are resolved normally

### 4.3 Constraint Parsing

#### parse_constraint(constraint_expression)

- REQUIRES: `constraint_expression` is a non-empty string containing an opam version constraint expression.
- ENSURES: Tokenizes the expression. Parses into an AST of comparisons (`=`, `!=`, `<`, `>`, `<=`, `>=`) and logical operators (`&`, `|`). Normalizes to disjunctive normal form. Returns a VersionConstraint (a set of version intervals).
- MAINTAINS: Parsing is deterministic -- the same constraint expression always produces the same VersionConstraint.

Version comparison shall follow opam ordering rules:

| Rule | Description |
|------|-------------|
| Numeric segments | Compared numerically (`8` < `18`) |
| String segments | Compared lexicographically |
| Tilde prefix | `~` sorts before any other character at the same position (`8.18~` < `8.18`) |
| Build suffix | `+` segments sort after the base version (`8.19` < `8.19+flambda`) |

When a constraint expression cannot be parsed, the parser shall return a `CONSTRAINT_PARSE_ERROR` with the raw text preserved.

> **Given** constraint expression `>= "8.18" & < "8.20~"`
> **When** `parse_constraint` is called
> **Then** a VersionConstraint is returned with one interval: lower bound `8.18` (inclusive), upper bound `8.20~` (exclusive)

> **Given** constraint expression `>= "8.16" & < "8.18" | >= "8.19" & < "8.20"`
> **When** `parse_constraint` is called
> **Then** a VersionConstraint is returned with two intervals (disjunctive normal form)

> **Given** a malformed constraint expression `>= "8.18" &&& < "8.20"`
> **When** `parse_constraint` is called
> **Then** a `CONSTRAINT_PARSE_ERROR` is returned with the raw text `>= "8.18" &&& < "8.20"`

### 4.4 Conflict Detection

#### detect_conflicts(constraint_tree)

- REQUIRES: `constraint_tree` is a valid ResolvedConstraintTree.
- ENSURES: Identifies all shared resources (packages constrained by more than one path). For each shared resource, collects all constraints, computes the constraint intersection, and checks whether any available version satisfies the intersection. When all shared resources are satisfiable, returns a CompatibleSet with the newest mutually compatible version of each dependency. When any shared resource has an empty intersection with no available version inside it, returns a ConflictSet with minimal conflict sets extracted for each conflict.
- MAINTAINS: The constraint tree is not modified.

When a target Coq version is specified, the detector shall pin the Coq version constraint to the specified version and check whether all other constraints are satisfiable against that pin.

The minimal conflict set extraction shall identify the smallest subset of constraints that are mutually unsatisfiable, excluding constraints not involved in the conflict.

> **Given** a constraint tree where `coq-mathcomp-ssreflect` requires `coq >= 8.18` and `coq-iris` requires `coq < 8.18`
> **When** `detect_conflicts(constraint_tree)` is called
> **Then** a ConflictSet is returned with one conflict on resource `coq`, containing the two constraints in its `minimal_constraint_set`

> **Given** a constraint tree where all dependencies are compatible with `coq` versions `8.18` and `8.19`
> **When** `detect_conflicts(constraint_tree)` is called
> **Then** a CompatibleSet is returned with `verdict = "compatible"`, `version_map` containing the newest compatible version for each dependency, and `coq_version_range` covering `8.18` to `8.19`

> **Given** a constraint tree and a target Coq version of `8.17`
> **When** `detect_conflicts(constraint_tree)` is called with the Coq pin
> **Then** the detector checks all constraints against `coq = 8.17` specifically, returning a ConflictSet if any dependency is incompatible with that version

### 4.5 Explanation Building

#### build_explanation(conflict)

- REQUIRES: `conflict` is a Conflict with a non-empty `minimal_constraint_set`.
- ENSURES: For each constraint in the minimal conflict set, traces the path from the user's direct dependency through transitive dependencies to the conflicting constraint. Composes a plain-language summary and constraint chains. Returns an ExplanationText.
- MAINTAINS: Explanations are deterministic -- the same conflict always produces the same explanation.

When the conflict involves only direct dependencies, the explanation shall name both packages and the resource they disagree on.

When the conflict involves transitive dependencies, the explanation shall include the full chain from the direct dependency through intermediates to the point of disagreement.

> **Given** a conflict where `coq-mathcomp-ssreflect` (direct) requires `coq >= 8.18` and `coq-iris` (direct) requires `coq < 8.18`
> **When** `build_explanation(conflict)` is called
> **Then** the summary states that the two packages disagree on the Coq version, and `constraint_chains` contains two entries, one per constraint path

> **Given** a conflict where `coq-my-lib` (direct) depends on `coq-util` (transitive), which requires `coq < 8.17`
> **When** `build_explanation(conflict)` is called
> **Then** the constraint chain traces `coq-my-lib` -> `coq-util` -> `coq < 8.17`, naming all intermediates

### 4.6 Resolution Suggestion

#### suggest_resolutions(conflict, constraint_tree)

- REQUIRES: `conflict` is a Conflict. `constraint_tree` is the ResolvedConstraintTree from the analysis.
- ENSURES: For each constraint in the minimal conflict set, checks whether a newer version of the constraining package relaxes the constraint (UPGRADE), whether an older version of the opposing package is compatible (DOWNGRADE), and whether alternative packages provide equivalent functionality with compatible constraints (ALTERNATIVE). Annotates each resolution with a trade-off description. When no resolution exists, emits a NO_RESOLUTION entry. Returns a list of Resolution sorted: upgrades first, then downgrades, then alternatives, then NO_RESOLUTION.
- MAINTAINS: Resolution suggestions are read-only -- no project files or opam state are modified.

When checking for UPGRADE resolutions, the suggester shall query opam for newer versions of the constraining package and parse their constraint metadata.

When checking for ALTERNATIVE resolutions, the suggester shall use a heuristic: packages with the same name prefix or in the same opam repository category.

When no resolution exists within available versions, the suggester shall emit exactly one NO_RESOLUTION entry with an explicit statement.

> **Given** a conflict on `coq` between `coq-lib-a` (requires `coq >= 8.18`) and `coq-lib-b` (requires `coq < 8.18`), and `coq-lib-b` has a newer version that accepts `coq >= 8.18`
> **When** `suggest_resolutions(conflict, constraint_tree)` is called
> **Then** an UPGRADE resolution is returned with `target_package = "coq-lib-b"` and the target version, with a trade-off noting potential API changes

> **Given** a conflict where no newer or older version of any involved package resolves the issue
> **When** `suggest_resolutions(conflict, constraint_tree)` is called
> **Then** a single NO_RESOLUTION entry is returned with `trade_off` stating that no compatible combination exists within available package versions

> **Given** a conflict with both an upgrade path for package A and a downgrade path for package B
> **When** `suggest_resolutions(conflict, constraint_tree)` is called
> **Then** the UPGRADE for A appears before the DOWNGRADE for B in the result list

## 5. Data Model

### DependencySet

| Field | Type | Constraints |
|-------|------|-------------|
| `dependencies` | ordered list of DeclaredDependency | Required; at least one entry for analysis to proceed |
| `project_dir` | string | Required; absolute path to the project directory |
| `build_system` | BuildSystem | Required; one of `COQ_MAKEFILE`, `DUNE`, `UNKNOWN` (reuses Build System Adapter's enumeration) |
| `unknown_packages` | ordered list of string | Required; package names not found in the opam repository; empty when all packages are valid |

### DeclaredDependency

| Field | Type | Constraints |
|-------|------|-------------|
| `package_name` | string | Required; non-empty; opam package name |
| `version_constraint` | string or null | Null when unconstrained |
| `source_file` | string | Required; absolute path to the file containing the declaration |
| `hypothetical` | boolean | Required; true when added for hypothetical analysis |

### ResolvedConstraintTree

| Field | Type | Constraints |
|-------|------|-------------|
| `root_dependencies` | ordered list of string | Required; the user's direct dependency package names |
| `nodes` | map of package name to PackageNode | Required; all packages in the transitive tree |
| `edges` | ordered list of ConstraintEdge | Required; directed edges carrying version constraints |

### PackageNode

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | Required; opam package name |
| `available_versions` | ordered list of string | Required; all available versions, descending order |
| `installed_version` | string or null | Null when not installed in the current switch |

### ConstraintEdge

| Field | Type | Constraints |
|-------|------|-------------|
| `from_package` | string | Required; package imposing the constraint |
| `to_package` | string | Required; package being constrained |
| `constraint` | VersionConstraint | Required; the parsed version constraint |
| `raw_constraint` | string | Required; original opam constraint expression |

### VersionConstraint

| Field | Type | Constraints |
|-------|------|-------------|
| `intervals` | ordered list of VersionInterval | Required; union of version intervals (disjunctive normal form); at least one interval |

### VersionInterval

| Field | Type | Constraints |
|-------|------|-------------|
| `lower` | VersionBound or null | Null means no lower bound |
| `upper` | VersionBound or null | Null means no upper bound |

### VersionBound

| Field | Type | Constraints |
|-------|------|-------------|
| `version` | string | Required; non-empty version string |
| `inclusive` | boolean | Required; true when the bound includes the version itself |

### ConflictSet

| Field | Type | Constraints |
|-------|------|-------------|
| `verdict` | string | Required; always `"incompatible"` |
| `conflicts` | ordered list of Conflict | Required; at least one entry |

### CompatibleSet

| Field | Type | Constraints |
|-------|------|-------------|
| `verdict` | string | Required; always `"compatible"` |
| `version_map` | map of package name to string | Required; newest mutually compatible version of each dependency |
| `coq_version_range` | VersionConstraint | Required; range of Coq versions satisfying all constraints |

### Conflict

| Field | Type | Constraints |
|-------|------|-------------|
| `resource` | string | Required; the shared resource package name (e.g., `"coq"`, `"ocaml"`) |
| `minimal_constraint_set` | ordered list of ConstraintEdge | Required; smallest set of constraints producing an empty intersection; at least two entries |
| `explanation` | ExplanationText | Required |
| `resolutions` | ordered list of Resolution | Required; empty only when no analysis has been performed yet |

### ExplanationText

| Field | Type | Constraints |
|-------|------|-------------|
| `summary` | string | Required; non-empty; one-sentence conflict summary in plain language |
| `constraint_chains` | ordered list of ordered list of string | Required; each inner list traces from a direct dependency through intermediates to the conflicting constraint; at least two chains per conflict |

### Resolution

| Field | Type | Constraints |
|-------|------|-------------|
| `strategy` | string | Required; one of `UPGRADE`, `DOWNGRADE`, `ALTERNATIVE`, `NO_RESOLUTION` |
| `target_package` | string | Required; package to change |
| `target_version` | string or null | Required for `UPGRADE` and `DOWNGRADE`; null for `ALTERNATIVE` and `NO_RESOLUTION` |
| `alternative_package` | string or null | Non-null only for `ALTERNATIVE` |
| `trade_off` | string | Required; non-empty; plain-language description of the trade-off |

## 6. Interface Contracts

### Slash Command -> Compatibility Analysis Engine

| Property | Value |
|----------|-------|
| Mechanism | In-process function calls, invoked by Claude Code during `/check-compat` execution |
| Direction | Request-response (each pipeline stage called independently) |
| Input | Stage 1: project directory + optional hypothetical additions. Stage 2: DependencySet. Stage 4: ResolvedConstraintTree. Stage 5: ConflictSet + ResolvedConstraintTree. |
| Output | DependencySet, ResolvedConstraintTree, ConflictSet or CompatibleSet, list of Resolution |
| Statefulness | Stateless -- no data persists between invocations |
| Concurrency | Serialized; one analysis pipeline at a time |
| Idempotency | All operations are idempotent given the same opam repository state |
| Error strategy | All errors returned as structured error values with error code and message; caller formats for user |

### Compatibility Analysis Engine -> opam (subprocess)

| Property | Value |
|----------|-------|
| Mechanism | Subprocess invocation (fresh process per query) |
| Direction | Request-response |
| Commands used | `opam show` (package metadata), `opam list` (installed packages) |
| Read-only | Yes -- no switch-modifying commands are ever invoked |
| Timeout | Configurable per subprocess; default 30 seconds |
| Caching | Results cached in-memory within a single analysis run; each package queried at most once |
| Environment | Inherited from the server process; includes PATH, OPAMSWITCH, OPAMROOT |

### Compatibility Analysis Engine -> Build System Adapter (shared logic)

| Property | Value |
|----------|-------|
| Mechanism | Shared build system detection function (in-process) |
| Direction | Call |
| Purpose | Locate `.opam`, `dune-project`, and `_CoqProject` files in the project directory |
| Scope | Detection only -- does not invoke build execution or dependency management functions |

## 7. Error Specification

### 7.1 Input Errors

| Condition | Error Code | Behavior |
|-----------|-----------|----------|
| `project_dir` does not exist | `PROJECT_NOT_FOUND` | Return error immediately; no analysis attempted |
| `project_dir` is not a directory | `PROJECT_NOT_FOUND` | Return error immediately |
| No dependency declarations found in any project file | `NO_DEPENDENCIES` | Return informational result; no conflicts possible |
| Empty `hypothetical_additions` entry (empty string) | `INVALID_PARAMETER` | Return error immediately |

### 7.2 Dependency Errors

| Condition | Error Code | Behavior |
|-----------|-----------|----------|
| `opam` not found on PATH | `TOOL_NOT_FOUND` | Return error naming `opam` as the missing tool |
| `opam show` fails for a package | `PACKAGE_NOT_FOUND` | Flag the package in `unknown_packages`; continue analysis for remaining packages |
| `opam show` subprocess exceeds timeout | `OPAM_TIMEOUT` | Return partial results with indication of which metadata was not retrieved |

### 7.3 State Errors

| Condition | Error Code | Behavior |
|-----------|-----------|----------|
| Version constraint expression cannot be parsed | `CONSTRAINT_PARSE_ERROR` | Report the unparseable constraint with raw text; skip this edge in conflict detection; continue analysis |

### 7.4 Invariant Violations

| Condition | Error Code | Behavior |
|-----------|-----------|----------|
| Circular dependency in opam metadata | (handled internally) | Cycle detection prevents infinite recursion; cycle is noted in the constraint tree; analysis continues |

### 7.5 Edge Cases

| Condition | Behavior |
|-----------|----------|
| All unknown packages (none resolved) | Return `NO_DEPENDENCIES` with all names in `unknown_packages` |
| Single dependency (no shared resources) | Return CompatibleSet with `verdict = "compatible"` and the newest available version |
| Hypothetical addition is already declared | Include both entries (file-sourced and hypothetical); no deduplication error |
| Constraint tree has no shared resources | Return CompatibleSet; no conflicts possible when no resources are shared |
| Multiple conflicts on the same resource | Report the single resource with the combined minimal conflict set |
| Conflict on `ocaml` version (not `coq`) | Treated identically to `coq` version conflicts; resource name is `"ocaml"` |

## 8. Non-Functional Requirements

- Dependency scanning shall complete within 2 seconds for projects with up to 50 declared dependencies.
- Each `opam show` subprocess shall complete within 30 seconds (configurable timeout).
- Transitive metadata resolution shall complete within 60 seconds for dependency trees with up to 100 unique packages.
- Constraint parsing shall process a single constraint expression in under 5 ms.
- Conflict detection (constraint intersection across all shared resources) shall complete within 500 ms for trees with up to 100 packages and 500 constraint edges.
- Explanation building shall complete within 100 ms per conflict.
- Resolution suggestion shall complete within 30 seconds per conflict (additional opam queries for newer versions).
- The engine shall not maintain in-memory state between invocations; each analysis pipeline is self-contained.
- In-memory cache of opam show results within a single run shall not exceed 50 MB for trees with up to 100 packages.

## 9. Examples

### Compatible dependencies

```
scan_dependencies("/home/user/my-coq-project", [])
resolve_metadata(dependency_set)
detect_conflicts(constraint_tree)

Project depends on: coq-mathcomp-ssreflect (>= 2.0), coq-equations (>= 1.3)
Both compatible with coq 8.18 and 8.19.

Result:
{
  "verdict": "compatible",
  "version_map": {
    "coq": "8.19.0",
    "coq-mathcomp-ssreflect": "2.2.0",
    "coq-equations": "1.3.1"
  },
  "coq_version_range": {
    "intervals": [
      {"lower": {"version": "8.18", "inclusive": true},
       "upper": {"version": "8.20~", "inclusive": false}}
    ]
  }
}
```

### Incompatible dependencies with resolution

```
scan_dependencies("/home/user/my-coq-project", [])
resolve_metadata(dependency_set)
detect_conflicts(constraint_tree)

Project depends on: coq-mathcomp-ssreflect (>= 2.0), coq-iris (>= 4.0)
coq-mathcomp-ssreflect requires coq >= 8.18.
coq-iris 4.0 requires coq < 8.18.
coq-iris 4.1 accepts coq >= 8.18.

Result:
{
  "verdict": "incompatible",
  "conflicts": [
    {
      "resource": "coq",
      "minimal_constraint_set": [
        {"from_package": "coq-mathcomp-ssreflect", "to_package": "coq",
         "raw_constraint": ">= \"8.18\""},
        {"from_package": "coq-iris", "to_package": "coq",
         "raw_constraint": "< \"8.18\""}
      ],
      "explanation": {
        "summary": "coq-mathcomp-ssreflect requires Coq 8.18 or later, but coq-iris requires Coq earlier than 8.18 -- there is no Coq version that satisfies both.",
        "constraint_chains": [
          ["coq-mathcomp-ssreflect", "requires coq >= 8.18"],
          ["coq-iris", "requires coq < 8.18"]
        ]
      },
      "resolutions": [
        {
          "strategy": "UPGRADE",
          "target_package": "coq-iris",
          "target_version": "4.1.0",
          "alternative_package": null,
          "trade_off": "Requires updating coq-iris from 4.0 to 4.1, which may introduce API changes."
        }
      ]
    }
  ]
}
```

### Hypothetical addition check

```
scan_dependencies("/home/user/my-coq-project", ["coq-equations"])
resolve_metadata(dependency_set)
detect_conflicts(constraint_tree)

Existing dependencies are compatible. Adding coq-equations is also compatible.

Result:
{
  "verdict": "compatible",
  "version_map": {
    "coq": "8.19.0",
    "coq-mathcomp-ssreflect": "2.2.0",
    "coq-equations": "1.3.1"
  },
  "coq_version_range": {
    "intervals": [
      {"lower": {"version": "8.18", "inclusive": true},
       "upper": {"version": "8.20~", "inclusive": false}}
    ]
  }
}
```

### Unknown package detection

```
scan_dependencies("/home/user/my-coq-project", ["coq-nonexistent-lib"])

Result (DependencySet):
{
  "dependencies": [
    {"package_name": "coq", "version_constraint": ">= 8.18",
     "source_file": "/home/user/my-coq-project/mylib.opam", "hypothetical": false}
  ],
  "project_dir": "/home/user/my-coq-project",
  "build_system": "DUNE",
  "unknown_packages": ["coq-nonexistent-lib"]
}
```

## 10. Language-Specific Notes (Python)

- Package location: `src/poule/compat/`.
- Use `asyncio.create_subprocess_exec` for opam subprocess management, consistent with the Build System Adapter's subprocess pattern.
- Use `asyncio.wait_for` for per-subprocess timeout enforcement.
- Cache opam show results in a `dict[str, OpamShowResult]` scoped to the analysis run (not persisted).
- Entry points:
  - `async def scan_dependencies(project_dir: Path, hypothetical_additions: list[str] | None = None) -> DependencySet`
  - `async def resolve_metadata(dependency_set: DependencySet, timeout: int = 30) -> ResolvedConstraintTree`
  - `def parse_constraint(expression: str) -> VersionConstraint`
  - `def detect_conflicts(tree: ResolvedConstraintTree, target_coq_version: str | None = None) -> ConflictSet | CompatibleSet`
  - `def build_explanation(conflict: Conflict) -> ExplanationText`
  - `async def suggest_resolutions(conflict: Conflict, tree: ResolvedConstraintTree) -> list[Resolution]`
- Data structures (DependencySet, ResolvedConstraintTree, ConflictSet, CompatibleSet, Conflict, Resolution, etc.) shall be `dataclasses.dataclass` with `frozen=True`.
- VersionConstraint interval arithmetic: implement `intersect(a: VersionConstraint, b: VersionConstraint) -> VersionConstraint` and `is_empty(vc: VersionConstraint) -> bool` as standalone functions.
- Version comparison: implement opam ordering rules (numeric segments, lexicographic segments, tilde, build suffix) in a `compare_versions(a: str, b: str) -> int` comparator function.
- Constraint parsing: use a recursive descent parser for the opam constraint grammar. Tokenize with `re` module using compiled patterns.
- Build System Adapter reuse: import and call `detect_build_system` from `src/poule/build/`; do not duplicate detection logic.

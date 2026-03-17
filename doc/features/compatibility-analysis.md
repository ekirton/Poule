# Cross-Library Compatibility Analysis

Dependency hell is one of the most cited pain points in the Coq ecosystem. When a project depends on multiple libraries, each constraining the Coq version, OCaml version, and shared transitive dependencies, version conflicts are inevitable — but today they surface only when `opam install` fails with opaque solver output that most users cannot interpret. Cross-Library Compatibility Analysis is a `/check-compat` slash command that detects these conflicts before the user ever hits a build failure. It queries opam metadata, reasons about Coq version constraints across the full dependency tree, explains conflicts in plain language, and suggests concrete resolution paths. The user experience shifts from "run the solver, wait, fail, guess, repeat" to "ask whether my dependencies are compatible and get a clear answer."

**Stories**: [Epic 1: Dependency Scanning](../requirements/stories/compatibility-analysis.md#epic-1-dependency-scanning), [Epic 2: Constraint Analysis](../requirements/stories/compatibility-analysis.md#epic-2-constraint-analysis), [Epic 3: Conflict Detection](../requirements/stories/compatibility-analysis.md#epic-3-conflict-detection), [Epic 4: Conflict Explanation and Reporting](../requirements/stories/compatibility-analysis.md#epic-4-conflict-explanation-and-reporting), [Epic 5: Resolution Suggestions](../requirements/stories/compatibility-analysis.md#epic-5-resolution-suggestions)

---

## Problem

A Coq developer adds `coq-mathcomp-ssreflect` and `coq-iris` to their project, runs `opam install`, and waits. Minutes later the solver reports failure in a wall of constraint expressions that reference internal package variables, version ranges, and resolution attempts. The developer does not know which two packages disagree, which version of Coq each one needs, or what to change. They try pinning a Coq version, re-run the solver, wait again, and get a different wall of text. This cycle repeats — sometimes for hours — before the developer either finds a working combination by trial and error or gives up and drops a dependency.

The problem is not that the information is unavailable. Opam metadata contains every version constraint for every package. The problem is that no tool synthesizes that information into a verdict the user can act on. The opam solver is optimized for finding solutions, not for explaining failures. And the constraint relationships span a dependency tree that no human should be expected to traverse manually.

What's missing is a way for the user to ask "are these dependencies compatible?" and get a plain-language answer — before they commit to an installation attempt.

## Solution

The `/check-compat` command lets the user request a compatibility analysis of their project's declared dependencies at any time. It reads dependency declarations from the project's build files, queries opam metadata for version constraints across the full dependency tree, determines whether a mutually satisfying combination of versions exists, and reports the result in plain language.

### Proactive Conflict Detection

Rather than waiting for a build attempt to fail, the user invokes `/check-compat` to learn about conflicts immediately. The command examines every declared dependency and its transitive constraints, checking whether the full set can be simultaneously satisfied. When dependencies are compatible, the command confirms it and reports the range of Coq versions that work. When they are not, it identifies exactly which packages conflict and which shared resource — Coq version, OCaml version, or a transitive dependency — they disagree on.

The user can also check hypothetical changes without modifying project files: "would adding `coq-equations` break anything?" or "are my dependencies compatible with Coq 8.19?" These questions are answered from opam metadata, so the user can evaluate options before committing to them.

### Plain-Language Explanations

Every conflict is explained in terms the user can understand without knowledge of opam's internal constraint language. Instead of a raw constraint expression, the user sees an explanation like: "`coq-mathcomp-ssreflect` requires Coq 8.18 or later, but `coq-iris` requires Coq 8.17 or earlier — there is no Coq version that satisfies both." Transitive conflicts trace the chain from the user's direct dependencies through intermediate packages to the point of disagreement, so the user sees the full picture rather than a symptom.

### Resolution Suggestions

Knowing what is broken is only half the problem; the user also needs to know what to do about it. When a conflict is detected, the command suggests concrete resolution strategies: upgrade one package, downgrade another, use an alternative, or relax a constraint. When multiple resolutions are viable, it lists them with trade-offs so the user can make an informed choice. When no resolution exists within available package versions, it says so directly — which is itself valuable information that prevents further wasted effort.

### Compatibility Summary

Every analysis produces a structured summary: an overall verdict (compatible or incompatible), a list of any conflicts with their explanations, and confirmation of which dependency pairs are compatible. When everything works, the summary includes the newest mutually compatible version of each dependency, so the user can keep their project up to date within the constraints that exist.

## Scope

Cross-Library Compatibility Analysis provides:

- Extraction of dependency declarations from `.opam`, `dune-project`, and `_CoqProject` files
- Analysis of the full dependency tree including transitive constraints
- Detection of mutually incompatible dependency sets with identification of the specific conflicting packages and constraints
- Plain-language explanations of every detected conflict
- Resolution suggestions for each conflict, with concrete version targets and trade-offs
- Hypothetical dependency addition analysis without modifying project files
- Compatibility checking against a user-specified target Coq version
- Detection of unavailable or misspelled package names
- A compatibility summary with an overall verdict and the newest mutually compatible versions

Cross-Library Compatibility Analysis does not provide:

- Modifications to opam, the opam solver, or opam repository infrastructure
- Automatic application of fixes to project files — the command reports and suggests, the user decides
- Dependency resolution for non-opam package managers (Nix, esy, manual builds)
- Diagnosis of build failures unrelated to version constraints (missing C libraries, compiler flags, API incompatibilities)
- Management of opam switches or opam repository configuration
- Runtime compatibility testing beyond version constraints

---

## Design Rationale

### Why a proactive check rather than better error reporting

The fundamental problem is not that opam's error messages are hard to read — though they are. The problem is that the user should not have to attempt an installation to discover that their dependencies are incompatible. An installation attempt is slow, it may modify the opam switch state, and its failure output is designed for the solver's internal logic rather than for human consumption. A proactive check runs before any installation is attempted, uses the same metadata the solver would use, and produces output designed entirely for the user. This shifts conflict detection from build time to planning time.

### Why plain language over structured constraint output

Opam's constraint language is precise and machine-readable, but most Coq users are mathematicians, not package manager experts. A constraint like `"coq" {>= "8.18" & < "8.20~"}` is meaningful to opam developers but opaque to the majority of users who encounter it in error output. Plain-language explanations sacrifice some precision for dramatically better accessibility. The user who reads "these two packages disagree on the Coq version" can act on that information immediately; the user who reads a raw constraint expression often cannot.

### Why suggest resolutions rather than apply them automatically

Dependency conflicts rarely have a single correct resolution. Upgrading one package may introduce API changes that require proof rewrites. Downgrading another may lose a feature the user depends on. Choosing an alternative package may change the project's theoretical foundations. These are decisions that require project context and human judgment. The command provides the information needed to make the decision — which versions resolve the conflict, what the trade-offs are — but leaves the decision to the user.

### Why support hypothetical additions

One of the most common triggers for dependency conflicts is adding a new library. The user wants to use `coq-equations` but does not know whether it is compatible with their existing setup. Today, the only way to find out is to add it to the project file, run `opam install`, and see what happens. Supporting hypothetical additions lets the user evaluate compatibility before modifying any files, which is faster, non-destructive, and encourages exploration of the ecosystem rather than conservative avoidance of new dependencies.

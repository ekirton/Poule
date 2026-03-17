# Build System Integration

Unified management of Coq's three build tools — `coq_makefile`, Dune, and opam — through MCP tools that Claude Code can invoke to generate project configuration files, run builds, interpret errors in plain language, and manage package dependencies. Instead of requiring developers to learn three separate configuration formats and debug opaque error messages, the build system integration handles the mechanical details so the developer can focus on their Coq code.

**Stories:** [Epic 1: Project File Generation](../requirements/stories/build-system-integration.md#epic-1-project-file-generation), [Epic 2: Build Execution and Error Interpretation](../requirements/stories/build-system-integration.md#epic-2-build-execution-and-error-interpretation), [Epic 3: Package and Dependency Management](../requirements/stories/build-system-integration.md#epic-3-package-and-dependency-management), [Epic 4: Configuration Maintenance](../requirements/stories/build-system-integration.md#epic-4-configuration-maintenance)

---

## Problem

Coq's build story is fragmented across three tools that evolved independently, each with its own configuration format, conventions, and failure modes.

`coq_makefile` is the traditional option: a `_CoqProject` file lists source directories and logical path mappings, and `coq_makefile` generates a Makefile from it. It is simple but limited — no dependency management, no cross-project builds, and the `_CoqProject` must be maintained by hand as the project grows. Dune is more powerful (multi-library projects, incremental builds, cross-project dependencies) but introduces its own complexity: `dune-project` files, per-directory `dune` files, and Coq-specific stanzas (`coq.theory`) with semantics that differ from the OCaml stanzas most Dune documentation covers. opam handles package installation and dependency resolution, but requires `.opam` files written in a domain-specific constraint language and an understanding of version pinning, repository configuration, and switch management.

For newcomers, this fragmentation is a wall. Before writing a single proof, a new Coq developer must choose a build system, learn its configuration format, set up opam correctly, and resolve any dependency version mismatches — all tasks that require expertise they do not yet have. Even experienced developers lose time to misconfigured `_CoqProject` files, missing Dune stanzas, and broken dependency pins. And when builds fail, the error messages from `coqc`, Dune, and opam are terse and assume familiarity with the tool's internal model, making diagnosis slow and frustrating.

## Solution

### Project File Generation

Given a Coq project's directory structure, the build system integration generates the correct configuration files for the developer's chosen build system. For `coq_makefile` projects, this means a `_CoqProject` file with source directories, logical path mappings (`-Q` and `-R` flags), and any required Coq flags. For Dune projects, this means a `dune-project` file and per-directory `dune` files with correct `coq.theory` stanzas, including library names, logical paths, and inter-library dependency declarations. For packages intended for distribution, this means a valid `.opam` file with metadata, dependency declarations with appropriate version constraints, and build instructions.

The generated files are immediately valid — they pass `coq_makefile`, `dune build`, and `opam lint` without manual correction. When the project structure changes (new files, new directories, new dependencies), the configuration can be updated in place, preserving any custom flags or comments the developer has added.

For projects that have outgrown `coq_makefile` and want to adopt Dune, the integration reads an existing `_CoqProject` and generates equivalent Dune configuration, reporting any flags that cannot be directly translated.

### Build Execution and Error Interpretation

The integration runs builds within the conversational workflow — `make` via `coq_makefile`-generated Makefiles or `dune build` — and captures the complete output. When the build succeeds, the developer sees confirmation. When the build fails, each error is interpreted in plain language: what went wrong, why, and what to do about it.

A "Cannot find a physical path bound to logical path" error becomes an explanation that a logical path mapping is missing, with a specific suggestion to add the right `-Q` flag or `theories` entry. A "Required library not found" error becomes an identification of the missing dependency and the opam package that provides it. When builds produce multiple errors, each receives its own explanation and fix suggestion rather than a wall of undifferentiated compiler output.

### Package and Dependency Management

The integration queries opam to report what packages are installed in the current switch and what versions are available in configured repositories. When the developer wants to add a dependency, the integration updates the `.opam` or `dune-project` file with the new package and appropriate version constraints, avoiding duplicates.

Before installation is attempted, the integration checks whether a set of desired dependencies has version conflicts — identifying the specific packages and their incompatible constraints so the developer can resolve the issue proactively rather than waiting for a failed `opam install` and parsing its output.

## Design Rationale

### Why three tools, not one

Coq's build ecosystem is not going to consolidate into a single tool in the near term. `coq_makefile` remains the default for simple projects and much existing documentation. Dune is the direction the ecosystem is moving for serious development. opam is the only package manager. Covering all three is not a design choice — it is a recognition of the ecosystem as it exists. Developers need help with whichever tool they are using, and many projects use all three simultaneously.

### Why Lean's Lake is the competitive benchmark

Lake demonstrates what a well-integrated build and package management experience looks like for a proof assistant. A single `lakefile.lean` configures builds, dependencies, and targets. Lean users rarely struggle with project setup. The gap between Lake's experience and Coq's fragmented toolchain is the single largest developer-experience disadvantage Coq faces relative to Lean. This integration does not unify Coq's tools — that is beyond scope — but it gives developers a single point of interaction (Claude Code) that absorbs the complexity on their behalf, closing the experiential gap.

### What this does not cover

This feature does not manage opam switches — creating, deleting, or switching between them. Switch management is an environment-level concern that interacts with system configuration in ways that are risky to automate without explicit user control.

This feature does not generate continuous integration configuration (GitHub Actions, GitLab CI, etc.). CI pipelines depend on organizational preferences, runner infrastructure, and deployment workflows that vary too widely to address within a build system integration.

This feature does not support build systems other than `coq_makefile` and Dune (e.g., Nix-based Coq builds), does not publish packages to the opam repository, and does not integrate with IDE-specific build features (VS Code tasks, Emacs compile mode).

# Build System Integration — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Setting up and maintaining build configurations is one of the most significant pain points in the Coq/Rocq ecosystem. New users must navigate a fragmented landscape of build tools — `coq_makefile`, Dune, and opam — each with its own configuration format, conventions, and failure modes. Build errors are opaque and rarely actionable without prior expertise. Dependency management requires familiarity with opam's constraint language, repository structure, and version resolution behavior. Even experienced developers lose time to misconfigured `_CoqProject` files, missing Dune stanzas, and broken dependency pins.

This initiative wraps `coq_makefile`, Dune, and opam as MCP tools so that Claude Code can generate project configuration files (`_CoqProject`, `dune-project`, `.opam`), run builds, interpret build errors in plain language, and manage package dependencies — all within the conversational workflow. By automating the mechanical aspects of project setup and build management, this initiative removes the barrier that prevents newcomers from reaching productive Coq development and reduces friction for experienced developers maintaining complex projects.

**Success metrics:**
- Generated `_CoqProject`, `dune-project`, and `.opam` files pass validation by their respective tools without manual correction in ≥ 90% of cases
- Build error interpretations include an actionable fix suggestion in ≥ 80% of cases
- Users report measurable reduction in time spent on project setup and build configuration in qualitative evaluation
- Dependency version conflict detection correctly identifies the conflicting constraints in ≥ 85% of cases

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Coq newcomers using Claude Code | Guided project setup without needing to learn build tool syntax or opam conventions | Primary |
| Coq developers maintaining multi-file projects | Automated generation and maintenance of build configurations as project structure evolves | Primary |
| Coq developers debugging build failures | Plain-language interpretation of build errors with actionable fix suggestions | Primary |
| Coq library authors publishing packages | Correct `.opam` file generation and dependency compatibility checking before release | Secondary |

---

## 3. Competitive Context

**Lean ecosystem (comparative baseline):**
- Lake: Lean's unified, declarative build system and package manager. A single `lakefile.lean` configures builds, dependencies, and targets. Lake is tightly integrated with the Lean toolchain and provides a consistent, well-documented experience. Lean users rarely struggle with project setup.

**Coq ecosystem (current state):**
- `coq_makefile`: The traditional build tool. Requires a `_CoqProject` file listing source directories and flags. Generates a Makefile. Simple but limited — no dependency management, no cross-project builds, manual maintenance as projects grow.
- Dune: A general OCaml/Coq build system. More powerful than `coq_makefile` (supports multi-library projects, cross-project dependencies, incremental builds) but adds complexity: `dune-project`, `dune` files per directory, Coq-specific stanzas (`coq.theory`) with their own semantics.
- opam: The OCaml/Coq package manager. Handles dependency resolution and installation but requires `.opam` files with a domain-specific constraint language. Version pinning, repository management, and switch handling are non-trivial.
- No existing tool provides AI-assisted generation or interpretation of Coq build configurations. Developers must read documentation and debug configurations manually.

**Gap:** Lean's Lake provides a single, coherent build and package management experience. Coq's fragmented toolchain requires developers to understand three separate tools with different configuration formats. This initiative bridges that gap by giving Claude Code the ability to manage all three on the user's behalf.

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R-P0-1 | Given a Coq project directory structure, generate a valid `_CoqProject` file that lists source directories, logical path mappings (`-Q` and `-R` flags), and any required Coq flags |
| R-P0-2 | Given a Coq project using Dune, generate valid `dune-project` and per-directory `dune` files with correct `coq.theory` stanzas, including library name, logical path, and dependency declarations |
| R-P0-3 | Given a Coq package, generate a valid `.opam` file with correct metadata fields, dependency declarations, and build instructions |
| R-P0-4 | Run a Coq build (`make` via `coq_makefile` or `dune build`) and capture the complete build output including any errors |
| R-P0-5 | Given build output containing errors, interpret each error in plain language, identify the likely cause, and suggest a concrete fix |
| R-P0-6 | Query the list of opam packages currently installed in the active switch, including their versions |
| R-P0-7 | Expose all build system tools as MCP tools compatible with Claude Code (stdio transport) |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R-P1-1 | Given a package name, check whether it is available in the configured opam repositories and report available versions |
| R-P1-2 | Add a dependency to an existing `.opam` or `dune-project` file, including appropriate version constraints |
| R-P1-3 | Given a set of desired dependencies with version constraints, detect version conflicts before attempting installation |
| R-P1-4 | Given an existing `_CoqProject` file, update it when new source files or directories are added to the project |
| R-P1-5 | Support migration from `coq_makefile` to Dune by reading an existing `_CoqProject` and generating equivalent Dune configuration files |
| R-P1-6 | Run opam install for a specified package and report success or failure with interpreted error output |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R-P2-1 | Given a Coq project, recommend whether `coq_makefile` or Dune is more appropriate based on project size and structure |
| R-P2-2 | Validate an existing `_CoqProject`, `dune-project`, or `.opam` file and report any issues |
| R-P2-3 | Generate a complete project scaffold (directory structure, build files, and opam file) from a project name and description |
| R-P2-4 | Pin a dependency to a specific version in the opam switch and update build configuration files accordingly |

---

## 5. Scope Boundaries

**In scope:**
- Generation and maintenance of `_CoqProject`, `dune-project`, `dune`, and `.opam` configuration files
- Running builds via `coq_makefile`-generated Makefiles and Dune, with output capture
- Plain-language interpretation of build errors with fix suggestions
- Querying installed packages and available package versions via opam
- Dependency conflict detection
- MCP tool exposure for Claude Code integration (stdio transport)

**Out of scope:**
- Hosting or mirroring opam repositories
- Modifying the Coq compiler or build tools themselves
- Supporting build systems other than `coq_makefile` and Dune (e.g., Nix-based Coq builds)
- Managing opam switches (creation, deletion, switching between switches)
- Continuous integration configuration (GitHub Actions, GitLab CI, etc.)
- IDE-specific build integration (VS Code tasks, Emacs compile mode)
- Publishing packages to the opam repository

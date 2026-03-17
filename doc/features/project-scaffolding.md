# Project Scaffolding

Starting a new Coq project means navigating a maze of interrelated configuration decisions — build system choice, directory layout, logical path mappings, opam metadata, CI setup — before writing a single line of proof. Project Scaffolding eliminates this barrier with a `/scaffold` slash command that generates a complete, buildable project skeleton from a project name and a brief conversation about the developer's needs. What takes hours of boilerplate assembly today becomes a two-minute interaction.

**Stories**: [Epic 1: Core Project Generation](../requirements/stories/project-scaffolding.md#epic-1-core-project-generation), [Epic 2: Build File Generation](../requirements/stories/project-scaffolding.md#epic-2-build-file-generation), [Epic 3: CI Configuration](../requirements/stories/project-scaffolding.md#epic-3-ci-configuration), [Epic 4: Opam Integration](../requirements/stories/project-scaffolding.md#epic-4-opam-integration), [Epic 5: Documentation Templates](../requirements/stories/project-scaffolding.md#epic-5-documentation-templates), [Epic 6: Slash Command Orchestration](../requirements/stories/project-scaffolding.md#epic-6-slash-command-orchestration)

---

## Problem

The Coq ecosystem has no project generator. Before a developer can write their first theorem, they must create and correctly populate configuration files for at least one build system (`dune-project` and per-directory `dune` files, or `_CoqProject` and a `Makefile`), set up logical path mappings, add opam packaging metadata in yet another format, write CI configuration YAML with the right Docker images or opam setup steps, and create a `.gitignore` that covers Coq's many build artifacts. Each of these files has its own syntax and conventions, and none of them generate the others.

Lean solved this problem with Lake: `lake init` produces a complete, buildable project in seconds. Coq developers have no equivalent. Newcomers frequently abandon Coq at the project setup stage — not because the proof assistant is too hard, but because the tooling around it is. Experienced developers fare better but still waste time recreating boilerplate they have written many times before, often by copying from old projects and adapting by hand.

Community template repositories exist but are static snapshots that grow stale and require manual adaptation. They cannot adapt to a specific developer's choices about build system, dependencies, or project structure.

## Solution

Project Scaffolding provides a `/scaffold` slash command that generates everything a developer needs to start a new Coq project. The developer provides a project name and answers a few questions; the command produces a complete directory tree with build files, boilerplate source modules, CI configuration, opam metadata, and documentation templates — all tailored to the developer's choices and all following current Coq community conventions.

### Interactive Parameter Collection

Rather than requiring developers to memorize command flags or configuration schemas, `/scaffold` works conversationally. It asks about the project name, preferred build system, initial dependencies, whether CI is desired, and other optional parameters. Sensible defaults are provided at every step — a developer who simply provides a project name and accepts defaults gets a working Dune-based project without making any other decisions.

### Complete Project Generation

The generated skeleton includes everything needed for a successful first build: directory structure following community conventions, build system configuration (Dune or `coq_makefile`), a root module that compiles without errors, and correctly wired logical path mappings. When the developer requests it, the scaffold also includes opam packaging metadata, GitHub Actions CI workflows, a Coq-appropriate `.gitignore`, and a README with build instructions matching the chosen build system. If the developer specifies dependencies — MathComp, Equations, or others — those dependencies appear in the build files, opam metadata, and import statements consistently.

### Adaptability Over Templates

Unlike static templates, `/scaffold` adapts its output to the developer's specific parameters. A newcomer who wants the simplest possible setup gets a minimal Dune project. An experienced developer building a multi-library package with MathComp dependencies and CI gets a more elaborate scaffold with correct inter-library dependency declarations, opam version constraints, and a CI workflow that installs the right packages. The same command serves both cases because it responds to what the developer asks for rather than stamping out a fixed template.

## Scope

Project Scaffolding provides:

- A `/scaffold` slash command that collects project parameters conversationally
- Directory structure generation following Coq community conventions
- Dune build file generation (`dune-project`, per-directory `dune` files with `coq.theory` stanzas)
- `coq_makefile` build file generation (`_CoqProject`, `Makefile`) as an alternative
- Boilerplate root modules that compile without errors on first build
- opam file generation with correct metadata and dependency declarations
- GitHub Actions CI workflow generation
- Coq-appropriate `.gitignore` generation
- README generation with build instructions matching the chosen build system
- Dependency specification reflected consistently across all generated files
- Multi-library project structures with correct inter-library dependencies

Project Scaffolding does not provide:

- Substantive proof content or theorem statements — the scaffold produces compilable boilerplate only
- Support for build systems other than Dune and `coq_makefile`
- Git repository initialization or remote configuration
- Publishing scaffolded projects to opam repositories
- Ongoing project maintenance after initial scaffolding (see [Build System Integration](build-system-integration.md) for post-setup workflows)
- IDE-specific configuration files
- Static template hosting or distribution outside of Claude Code

---

## Design Rationale

### Why a slash command rather than a standalone tool

Project scaffolding is inherently a multi-step workflow: collect parameters, generate files across multiple directories, validate consistency, and report results. A slash command lets Claude orchestrate this workflow conversationally — asking clarifying questions, confirming choices before generating, and explaining what was created. A single MCP tool call cannot support this kind of back-and-forth interaction. The slash command also reuses the Build System Integration MCP tools as building blocks, ensuring that the generated files are consistent with what those tools produce individually.

### Why interactive parameter collection

Coq project setup involves choices that interact with each other: the build system affects the directory layout, the dependency set affects both build files and opam metadata, and CI configuration depends on all of the above. Presenting these as a flat list of command-line flags would recreate the very complexity the feature aims to eliminate. A conversational interaction lets Claude explain each choice, offer sensible defaults, and adapt later questions based on earlier answers. A newcomer who does not know what Dune is can accept the default; an expert can specify exactly what they want.

### Why Dune as the default build system

Dune is the recommended build system for new Coq projects as of Coq 8.x and the Rocq transition. It provides reproducible builds, better dependency tracking, and is the expected build system for opam packaging. While `coq_makefile` remains widely used in existing projects, steering new projects toward Dune aligns with the direction of the Coq ecosystem. Developers who prefer `coq_makefile` can still select it explicitly.

### Why this matters more than it appears

Project setup is not just an inconvenience — it is an adoption filter. Developers who cannot get a project building in their first session often do not return. Lean's Lake eliminated this problem for Lean, and Lean's rapid adoption growth is partly attributable to the smoothness of the first-project experience. By providing a comparable (and in some ways superior, because it adapts to user choices) experience for Coq, this feature addresses one of the most significant practical barriers to Coq adoption.

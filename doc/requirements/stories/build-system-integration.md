# User Stories: Build System Integration

Derived from [doc/requirements/build-system-integration.md](../build-system-integration.md).

---

## Epic 1: Project File Generation

### 1.1 Generate _CoqProject File

**As a** Coq newcomer using Claude Code,
**I want** Claude to generate a `_CoqProject` file for my project based on its directory structure,
**so that** I can build my project without learning `_CoqProject` syntax.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project directory containing `.v` files in subdirectories WHEN project file generation is invoked THEN a `_CoqProject` file is produced listing all source directories with correct `-Q` or `-R` flag mappings
- GIVEN a generated `_CoqProject` file WHEN `coq_makefile -f _CoqProject -o Makefile` is run THEN it succeeds without errors
- GIVEN a project with a single top-level source directory WHEN generation is invoked THEN the logical path mapping uses the directory name as the logical prefix

**Traces to:** R-P0-1

### 1.2 Generate Dune Build Files

**As a** Coq developer setting up a Dune-based project,
**I want** Claude to generate `dune-project` and per-directory `dune` files with correct `coq.theory` stanzas,
**so that** I do not need to memorize Dune's Coq-specific configuration syntax.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project directory structure WHEN Dune file generation is invoked THEN a `dune-project` file and per-directory `dune` files are produced with correct `coq.theory` stanzas
- GIVEN generated Dune files WHEN `dune build` is run THEN it succeeds without configuration errors
- GIVEN a project with inter-library dependencies WHEN generation is invoked THEN the `(theories ...)` field in each `dune` file correctly lists the dependencies

**Traces to:** R-P0-2

### 1.3 Generate .opam File

**As a** Coq library author preparing a package for distribution,
**I want** Claude to generate a valid `.opam` file with correct metadata and dependency declarations,
**so that** I can publish my package without mastering opam's file format.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a Coq project with known dependencies WHEN `.opam` generation is invoked THEN the produced file includes correct `depends`, `build`, `synopsis`, and `maintainer` fields
- GIVEN a generated `.opam` file WHEN `opam lint` is run against it THEN no errors are reported
- GIVEN a project that depends on `coq-mathcomp-ssreflect` version 2.x WHEN generation is invoked THEN the `depends` field includes the constraint `"coq-mathcomp-ssreflect" {>= "2.0.0"}`

**Traces to:** R-P0-3

---

## Epic 2: Build Execution and Error Interpretation

### 2.1 Run a Build

**As a** Coq developer using Claude Code,
**I want** Claude to run my project's build and capture the full output,
**so that** I can build my project without leaving the conversational workflow.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project with a `_CoqProject` file WHEN a build is requested THEN `coq_makefile` generates a Makefile and `make` is executed, with the complete stdout and stderr captured
- GIVEN a project with a `dune-project` file WHEN a build is requested THEN `dune build` is executed, with the complete stdout and stderr captured
- GIVEN a successful build WHEN the result is returned THEN it indicates success and includes the build output
- GIVEN a failed build WHEN the result is returned THEN it includes the complete error output

**Traces to:** R-P0-4

### 2.2 Interpret Build Errors

**As a** Coq newcomer encountering a build failure,
**I want** Claude to explain each build error in plain language and suggest a concrete fix,
**so that** I can resolve build problems without deciphering cryptic compiler messages.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN build output containing a "Cannot find a physical path bound to logical path" error WHEN interpretation is invoked THEN the explanation identifies the missing logical path mapping and suggests adding the correct `-Q` or `-R` flag to `_CoqProject` or the correct `(theories ...)` entry in `dune`
- GIVEN build output containing a "Required library" not-found error WHEN interpretation is invoked THEN the explanation identifies the missing dependency and suggests the opam package to install
- GIVEN build output containing multiple errors WHEN interpretation is invoked THEN each error receives a separate explanation with a specific fix suggestion

**Traces to:** R-P0-5

---

## Epic 3: Package and Dependency Management

### 3.1 Query Installed Packages

**As a** Coq developer using Claude Code,
**I want** Claude to list the opam packages installed in my current switch with their versions,
**so that** I can understand what is available in my environment without running opam commands manually.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active opam switch WHEN installed package listing is requested THEN the result includes each installed package name and its version
- GIVEN an active opam switch with `coq` version 8.19.0 installed WHEN the listing is inspected THEN it includes `coq 8.19.0`
- GIVEN the installed package listing WHEN it is returned THEN packages are sorted alphabetically by name

**Traces to:** R-P0-6

### 3.2 Add a Dependency

**As a** Coq developer adding a library dependency to my project,
**I want** Claude to update my `.opam` or `dune-project` file with the new dependency and appropriate version constraints,
**so that** I do not need to manually edit configuration files when my dependency set changes.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project with an existing `.opam` file WHEN a dependency on `coq-equations` is added THEN the `depends` field is updated to include `"coq-equations"` with an appropriate version constraint
- GIVEN a project with an existing `dune-project` file WHEN a dependency is added THEN the `(depends ...)` stanza is updated accordingly
- GIVEN an add-dependency request WHEN the package is already listed as a dependency THEN the tool reports that the dependency already exists rather than duplicating it

**Traces to:** R-P1-2

### 3.3 Detect Version Conflicts

**As a** Coq developer adding a new dependency,
**I want** Claude to check whether my desired dependencies have version conflicts before I attempt installation,
**so that** I can resolve constraint issues proactively rather than waiting for a failed `opam install`.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a set of dependencies where package A requires `coq >= 8.18` and package B requires `coq < 8.18` WHEN conflict detection is invoked THEN the result identifies the conflicting `coq` version constraints from packages A and B
- GIVEN a set of dependencies with no conflicts WHEN conflict detection is invoked THEN the result reports that all constraints are satisfiable
- GIVEN a conflict detection result WHEN it identifies a conflict THEN it names the specific packages and their incompatible constraints

**Traces to:** R-P1-3

### 3.4 Check Package Availability

**As a** Coq developer looking for a library,
**I want** Claude to check whether a package is available in opam and report its available versions,
**so that** I can find the right package and version without browsing the opam repository manually.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a package name that exists in the configured opam repositories WHEN availability is checked THEN the result lists all available versions of that package
- GIVEN a package name that does not exist WHEN availability is checked THEN the result reports that the package was not found
- GIVEN a package with multiple versions WHEN availability is checked THEN the versions are listed in descending order (newest first)

**Traces to:** R-P1-1

---

## Epic 4: Configuration Maintenance

### 4.1 Update _CoqProject on File Addition

**As a** Coq developer who has added new source files or directories to my project,
**I want** Claude to update my `_CoqProject` file to reflect the new project structure,
**so that** my build configuration stays in sync with my source tree without manual editing.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a project with an existing `_CoqProject` and a newly added subdirectory containing `.v` files WHEN update is invoked THEN the `_CoqProject` is updated with the new directory's logical path mapping
- GIVEN an update request WHEN the existing `_CoqProject` contains custom flags or comments THEN those are preserved in the updated file
- GIVEN a project where no new files or directories have been added WHEN update is invoked THEN the `_CoqProject` is not modified

**Traces to:** R-P1-4

### 4.2 Migrate from coq_makefile to Dune

**As a** Coq developer with an existing `coq_makefile`-based project,
**I want** Claude to read my `_CoqProject` and generate equivalent Dune configuration files,
**so that** I can migrate to Dune without manually translating my build configuration.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a project with a `_CoqProject` file containing `-Q` and `-R` mappings WHEN migration is invoked THEN equivalent `dune-project` and `dune` files are generated with matching `coq.theory` stanzas
- GIVEN a migrated project WHEN `dune build` is run THEN it builds the same set of `.vo` files that `make` produced under the original configuration
- GIVEN a `_CoqProject` with flags not representable in Dune WHEN migration is invoked THEN the tool reports which flags could not be migrated

**Traces to:** R-P1-5

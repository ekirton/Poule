# Coq-to-Rocq Migration

The Coq proof assistant is being officially renamed to Rocq. This rename is rolling out across multiple releases, touching namespaces, module paths, tactic names, command names, and build system references throughout the ecosystem. Every Coq project must eventually migrate, and doing so manually is tedious and error-prone: deprecated names are scattered across dozens of files, the correct replacements are not always obvious, and a single missed rename can break the build. Coq-to-Rocq Migration provides a `/migrate-rocq` slash command that handles the entire process — scanning a project for deprecated names, suggesting replacements, applying bulk renames, and verifying the result — so users can migrate with confidence instead of grep and hope.

**Stories**: [Epic 1: Deprecated Name Scanning](../requirements/stories/rocq-migration.md#epic-1-deprecated-name-scanning), [Epic 2: Replacement Suggestion](../requirements/stories/rocq-migration.md#epic-2-replacement-suggestion), [Epic 3: Bulk Rename Application](../requirements/stories/rocq-migration.md#epic-3-bulk-rename-application), [Epic 4: Build Verification](../requirements/stories/rocq-migration.md#epic-4-build-verification), [Epic 5: Rollback Safety](../requirements/stories/rocq-migration.md#epic-5-rollback-safety)

---

## Problem

The Coq-to-Rocq rename is not a single event — it unfolds incrementally across releases as deprecated names are phased out. Users face a compounding problem: they must track which names have been deprecated in their target version, locate every occurrence across source files and build configuration, determine the correct Rocq replacement for each, apply changes without breaking proofs, and verify correctness by building. Miss one name and the build fails. Rename a string in a comment and the diff is noisy. Forget a module path in a `From ... Require` statement and imports break silently.

Today, users rely on compiler deprecation warnings (which report one occurrence at a time during a build), community `sed` scripts (which do not understand Coq's namespace semantics and cannot distinguish identifiers from comments), or manual search-and-replace (which does not scale). None of these approaches scan a project comprehensively, suggest replacements, apply them safely, and verify the result. The migration remains a manual, file-by-file slog that discourages adoption of the new naming and leaves projects accumulating deprecation warnings.

## Solution

Coq-to-Rocq Migration lets a user point Claude at their project and say "migrate this to Rocq naming." Claude scans the codebase, identifies every deprecated Coq name, shows the user what it plans to change, and — once the user approves — applies all renames and confirms the project still builds.

### Comprehensive Scanning

The migration scans all Coq source files in a project for deprecated names that have Rocq replacements. It covers not just identifier names within proofs and definitions, but also module paths in `Require Import` and `From ... Require` statements, and references in build system files like `_CoqProject`, `dune`, and `.opam`. Users with large codebases can scope the scan to specific files or directories to migrate incrementally.

### Context-Aware Renaming

Not every occurrence of a deprecated string should be renamed. A name appearing in a comment or string literal is not a reference to the deprecated identifier. The migration distinguishes identifier references from coincidental matches, so renames are applied only where they are semantically meaningful. This avoids noisy diffs and prevents changes that would alter documentation or output strings unintentionally.

### Review Before Commit

Before any files are modified, the user sees a complete summary of every proposed change — which files, which lines, which names, and what each will become. Nothing is applied until the user confirms. This gives the user full visibility and control, especially important for large projects where hundreds of renames might be proposed.

### Build Verification

After renames are applied, the migration runs the project's build to confirm that the changes are correct. If the build succeeds, the user knows the migration is safe. If the build fails, the migration distinguishes between failures caused by the rename and pre-existing issues, so the user knows what to fix and what was already broken.

### Rollback Safety

Every change made by the migration can be reverted. If the user is unsatisfied with the result or the build fails unexpectedly, they can return to their pre-migration state without risk of lost work. The migration does not create commits automatically, so standard version control tools remain available for reviewing and reverting changes.

## Scope

Coq-to-Rocq Migration provides:

- Scanning of Coq source files for deprecated names with known Rocq replacements
- Coverage of module paths in `Require Import` and `From ... Require` statements
- Scanning of build system files (`_CoqProject`, `dune`, `.opam`) for deprecated references
- Context-aware renaming that skips comments and string literals
- Incremental migration scoped to specific files or directories
- A change summary for user review before any files are modified
- Bulk rename application across multiple files in a single operation
- Build verification after renames are applied
- Rollback of all migration changes
- A migration report suitable for commit messages or changelogs

Coq-to-Rocq Migration does not provide:

- Modifications to the Coq/Rocq compiler or standard library
- Migration of third-party plugin internals — only references to plugins are covered
- Semantic verification beyond build success (e.g., confirming that renamed lemmas have identical types)
- Support for Coq versions that predate the rename initiative
- Resolution of breaking changes unrelated to the rename, such as API or tactic behavior changes between versions
- Automatic commits — the user controls when and how changes are committed

---

## Design Rationale

### Why a slash command

The Coq-to-Rocq migration is a multi-step workflow — scan, review, apply, verify — that the user initiates with a single intent: "migrate my project." A slash command (`/migrate-rocq`) captures that intent directly and lets Claude orchestrate the steps without the user needing to invoke individual tools manually. This matches how users think about the task: not "scan for deprecated names, then suggest replacements, then apply renames, then build" but "migrate this project to Rocq."

### Why review before apply

Bulk renaming across a codebase is a high-stakes operation. A single incorrect rename can break proofs in ways that are difficult to diagnose. Requiring user confirmation before applying changes ensures that the user retains control and can catch edge cases — such as identifiers that are intentionally kept at the old name for compatibility, or names that the rename map handles incorrectly. The cost of an extra confirmation step is small; the cost of an unwanted bulk rename is large.

### Why build verification matters

Renaming identifiers in a proof assistant is not like renaming variables in a typical programming language. Coq's type system and tactic machinery mean that a rename can fail in subtle ways — a tactic that resolved a name by its old path may not find it under the new one, or a notation that depended on a specific identifier may break. The only reliable way to confirm that a migration is correct is to build the project afterward. Integrating build verification into the workflow closes the loop: the user does not need to remember to build, and failures are surfaced immediately with context about whether they are migration-related.

### Why incremental migration

Large Coq projects — especially libraries with many interdependent modules — cannot always be migrated in a single pass. Dependencies may not yet support Rocq naming, or the user may want to test changes in isolation before migrating the entire codebase. Supporting file-level and directory-level scoping lets users migrate at their own pace, tackling one module at a time and verifying each step before moving on.

### Why this is time-sensitive

The Coq-to-Rocq rename is happening now. Deprecated names are already generating compiler warnings, and future Rocq releases will remove them entirely. Every Coq user will need to migrate eventually, and the longer they wait, the more deprecated names accumulate. Providing migration tooling now — while the rename is actively unfolding — captures users at the moment of highest need and prevents the ecosystem from fragmenting between old and new naming conventions.

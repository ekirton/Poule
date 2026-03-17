# Literate Documentation

Coq proof scripts become self-contained, interactive documents that any reader can explore in a browser — no IDE, no local Coq installation required. Claude generates these documents on demand from `.v` files by invoking Alectryon, turning opaque tactic sequences into browsable pages where every proof step reveals its resulting proof state on hover or click.

**Stories**: [Epic 1: Single-File Documentation Generation](../requirements/stories/literate-documentation.md#epic-1-single-file-documentation-generation), [Epic 2: Proof-Scoped Documentation](../requirements/stories/literate-documentation.md#epic-2-proof-scoped-documentation), [Epic 3: Batch Documentation Generation](../requirements/stories/literate-documentation.md#epic-3-batch-documentation-generation), [Epic 4: Output Customization](../requirements/stories/literate-documentation.md#epic-4-output-customization), [Epic 5: Error Handling and Dependency Detection](../requirements/stories/literate-documentation.md#epic-5-error-handling-and-dependency-detection)

---

## Problem

Proof scripts are opaque without an interactive IDE. A `.v` file opened in a text editor or code review tool shows tactic invocations but not the proof states they produce — the reader must mentally replay each step or open the file in CoqIDE or Proof General to understand what is happening. This makes proof scripts difficult to teach from, difficult to review, and difficult to publish as explanatory material.

Sharing proof understanding today requires copy-pasting fragments from an IDE into a document, losing interactivity and context in the process. An educator preparing lecture materials must screenshot proof states. A reviewer must install Coq tooling and replay the proof locally. A library author publishing documentation settles for coqdoc output that shows definitions and comments but never the proof states that make a proof comprehensible.

## Solution

### Single-File Generation

Given a `.v` file, Claude produces a complete interactive HTML page where every Coq sentence is paired with the proof state it produces. The output is self-contained — all styles and scripts are embedded — so the file can be opened directly in any modern browser with no additional setup. The user can specify where the HTML file is written, placing it directly into a project's documentation directory for publication.

### Proof-Scoped Generation

When the user is interested in a single proof rather than an entire file, Claude generates documentation scoped to a named theorem, lemma, or definition and its immediately surrounding context. Every tactic step within the proof shows its resulting proof state. This lets a reviewer focus on the proof under discussion without wading through an entire development, and lets an educator extract a single proof as a teaching artifact.

### Batch Generation

For project-wide documentation, Claude processes all `.v` files in a directory tree, preserving the project's directory structure in the output. The result includes cross-file navigation links so readers can browse between modules, and an index page that serves as the entry point for the entire documentation set. If individual files fail to compile, documentation is still generated for the files that succeed — failures are reported without aborting the batch.

### Output Customization

The generated documentation can take several forms depending on the user's needs: a standalone HTML page for direct viewing, an HTML fragment suitable for embedding into an existing website or slide deck, or LaTeX output for printed materials. Users with specific formatting preferences can pass custom Alectryon flags to control behavior such as line wrapping thresholds and caching.

## Design Rationale

### Why Alectryon

Alectryon is the mature, actively maintained tool for this job. It captures Coq's output sentence by sentence and produces interactive HTML with inline proof state display. It supports both reStructuredText and Markdown literate styles and is already used by major teaching materials including Software Foundations. Wrapping an established tool avoids reinventing proof state capture and HTML generation, and ensures the output is compatible with what the Coq community already uses and expects.

### Why this complements Poule's other tools

Literate documentation generation is a natural endpoint for workflows that begin with other Poule tools. After proof search finds a proof, the user can immediately generate browsable documentation for it. After semantic lemma search identifies relevant results, the user can produce a documented overview of how those lemmas are used in a development. Documentation generation turns Poule's interactive proof capabilities into shareable artifacts — the proof understanding that Claude helps build during a session can be captured and published rather than lost when the conversation ends.

### Graceful handling when Alectryon is not installed

Alectryon is not bundled with Poule — it is a Python package that users install separately. When Alectryon is not found on the system, the tool reports a clear error with installation instructions rather than failing with a cryptic message. When an outdated version is detected, the tool identifies the installed version and the minimum required version. This keeps the dependency boundary clean: Poule wraps Alectryon but does not own it, and users are guided toward resolving any installation issues themselves.

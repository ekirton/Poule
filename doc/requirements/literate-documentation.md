# Literate Documentation Generation — Product Requirements Document

Cross-reference: see [coq-ecosystem-gaps.md](coq-ecosystem-gaps.md) for ecosystem context.

## 1. Business Goals

Coq proof scripts are opaque outside of an IDE. A `.v` file read in a text editor or code review tool shows tactic invocations but not the proof states they produce — the reader must mentally replay each step or open the file in CoqIDE/Proof General to understand what is happening. This makes proof scripts difficult to teach from, difficult to review, and difficult to publish as explanatory material.

Alectryon solves this by capturing Coq's output for every sentence in a source file and interleaving it with the proof script to produce interactive HTML pages. Readers can hover or click to reveal proof states inline, turning a static script into a self-contained, readable document. Alectryon is mature, actively maintained, and supports both reStructuredText and Markdown literate styles.

This initiative wraps Alectryon as a set of MCP tools so that Claude can generate interactive proof documentation on demand. An educator preparing lecture materials can ask Claude to produce a browsable HTML page from a `.v` file. A reviewer can request documentation for a single proof to understand its structure without opening an IDE. A library author can batch-generate documentation for an entire project for publication.

**Success metrics:**
- Generate valid interactive HTML documentation from a single `.v` file with ≥ 95% success rate for files that compile without errors
- Generate documentation scoped to a single named proof within a file
- Batch-generate documentation for a multi-file Coq project with correct cross-file linking
- Documentation generation latency under 30 seconds per file on a standard development machine (excluding Coq compilation time)
- Generated HTML is self-contained and viewable in any modern browser without additional dependencies

---

## 2. Target Users

| Segment | Needs | Priority |
|---------|-------|----------|
| Educators teaching formal verification | Generate browsable proof documentation from `.v` files for use in lectures, assignments, and course websites | Primary |
| Proof reviewers and collaborators | Produce readable documentation for specific proofs under review without requiring the reviewer to install Coq tooling | Primary |
| Coq library authors and maintainers | Batch-generate project-wide documentation for publication alongside source releases | Secondary |
| Students learning Coq | Request documentation for example files to study proof structure interactively at their own pace | Tertiary |

---

## 3. Competitive Context

**Alectryon (the wrapped tool):**
- Captures Coq sentence-by-sentence output and produces interactive HTML with inline proof state display. Supports reStructuredText and Markdown literate programming. Mature and actively maintained. Used by Software Foundations and other teaching materials.
- Not integrated into AI-assisted workflows. Invocation requires command-line familiarity and local installation. No on-demand generation from within an LLM conversation.

**coqdoc (Coq built-in):**
- Extracts documentation comments from `.v` files and produces HTML or LaTeX. Does not capture or display proof states. Output is a reference manual, not an interactive proof walkthrough. Limited formatting control.

**Lean doc-gen4:**
- Generates API documentation for Lean 4 projects (analogous to Rustdoc or Javadoc). Focuses on declaration signatures and docstrings, not on proof state interleaving. Not applicable to Coq.

**Key differentiator of the MCP wrapper approach:**
- On-demand generation: Claude can produce documentation as part of a conversation, without the user invoking command-line tools
- Scoped output: generate documentation for an entire file, a single proof, or a whole project depending on the request
- Accessible to non-experts: users who cannot install or configure Alectryon directly can still obtain its output through Claude
- Composable with other Poule tools: documentation generation can follow proof development, search, or visualization in the same workflow

---

## 4. Requirement Pool

### P0 — Must Have

| ID | Requirement |
|----|-------------|
| R-LD-P0-1 | Expose an MCP tool that accepts a path to a `.v` file and returns interactive HTML documentation with inline proof states for every sentence in the file |
| R-LD-P0-2 | The generated HTML must be self-contained (all CSS and JavaScript inlined or embedded) so it can be viewed by opening the file in a browser with no additional setup |
| R-LD-P0-3 | Expose an MCP tool that accepts a `.v` file path and a proof name and returns interactive HTML documentation scoped to that specific proof and its surrounding context |
| R-LD-P0-4 | Report clear, actionable errors when the input `.v` file fails to compile, including Coq's error output and the location of the failure |
| R-LD-P0-5 | Report a clear, actionable error when Alectryon is not installed or not found on the system PATH, including installation instructions |
| R-LD-P0-6 | Support output as an HTML file written to a specified path or returned as HTML content |

### P1 — Should Have

| ID | Requirement |
|----|-------------|
| R-LD-P1-1 | Expose an MCP tool that accepts a project directory and generates documentation for all `.v` files in the project, with cross-file navigation links |
| R-LD-P1-2 | Support customizing the output format: standalone HTML page, HTML fragment suitable for embedding, or LaTeX output |
| R-LD-P1-3 | Support passing custom Alectryon flags (e.g., `--long-line-threshold`, `--cache-directory`) to control generation behavior |
| R-LD-P1-4 | Batch generation must produce an index page listing all documented files with links |

### P2 — Nice to Have

| ID | Requirement |
|----|-------------|
| R-LD-P2-1 | Support Alectryon's literate programming mode, accepting `.v.rst` or `.v.md` files that interleave prose and Coq code |
| R-LD-P2-2 | Support custom CSS themes for the generated HTML to match institutional or project branding |
| R-LD-P2-3 | Cache compilation artifacts to accelerate repeated documentation generation for the same file |
| R-LD-P2-4 | Generate a summary alongside the documentation listing the number of theorems, lemmas, and definitions documented |

---

## 5. Scope Boundaries

**In scope:**
- MCP tools that invoke Alectryon to produce interactive proof documentation
- Single-file documentation generation
- Single-proof documentation generation
- Batch documentation generation for multi-file projects
- Output format options (HTML standalone, HTML fragment, LaTeX)
- Error reporting for compilation failures and missing dependencies

**Out of scope:**
- Bundling or installing Alectryon itself (users must have Alectryon installed; the tools detect and report its absence)
- Modifying Alectryon's source code or forking it
- Real-time incremental documentation updates as a file is edited
- Hosting or serving generated documentation (output is files; serving is the user's concern)
- PDF generation (LaTeX compilation to PDF is a separate toolchain concern)
- Proof editing, tactic suggestion, or any modification of the input `.v` files
- Custom Alectryon driver development or plugin authoring

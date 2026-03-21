# Spec-Driven Development with Claude Code

This guide explains how to use Claude Code with the project's Spec-Driven Development (SDD) workflow. SDD enforces a chain of authority across documentation layers so that requirements flow downward through features, architecture, specifications, tests, and implementation — and each layer is protected from unauthorized modification by layers below it.

## The SDD Layers

| Layer | Directory | What belongs here |
|-------|-----------|-------------------|
| 1. Requirements | `doc/requirements/` | Business goals, user needs, constraints (PRDs) |
| 2. Features | `doc/features/` | What the system does and why, acceptance criteria |
| 3. Architecture | `doc/architecture/` | How it works at design level, data models |
| 4. Specifications | `specification/` | Implementable contracts (Design by Contract) |
| 5. Tasks | `tasks/` | Detailed implementation breakdown |
| 6. Tests | `test/` | Test suite derived from specifications |
| 7. Implementation | `src/`, `commands/` | Code, slash command prompts |

Each layer is **derived from** the one above and **authoritative for** the one below. The core discipline: while working at one layer, do not edit layers above it.

## Phase Commands

Claude Code enforces the SDD discipline through **phase commands**. Each phase restricts which directories Claude can edit:

| Command | Purpose |
|---------|---------|
| `/diagnose` | Investigate a bug report: find root cause, trace it up the authority chain, recommend which layer to fix |
| `/triage` | Quick audit when you already know the root cause: trace it up the authority chain |

| Command | Editable directories | Blocked from |
|---------|---------------------|-------------|
| `/requirements` | `doc/requirements/` | everything else |
| `/features` | `doc/features/` | everything else |
| `/architecture` | `doc/architecture/` | everything else |
| `/specification` | `specification/` | everything else |
| `/tasks` | `tasks/` | everything else |
| `/tests` | `test/` | everything else |
| `/implementation` | `src/`, `commands/`, `tasks/` | `test/`, `specification/`, `doc/` |
| `/free` | anything | nothing blocked |

**Default phase is `free`** — no restrictions. Enter a phase when you want discipline enforced.

### Example session

```
You:  /specification "add caching to retrieval pipeline"
      → Claude enters SPECIFICATION phase
      → Claude reads the architecture doc, writes to specification/
      → If Claude tries to edit doc/architecture/: BLOCKED with feedback message

You:  /implementation "implement caching per spec"
      → Claude enters IMPLEMENTATION phase
      → Claude reads spec and tests, writes to src/
      → If Claude tries to edit specification/: BLOCKED

You:  /free
      → All restrictions lifted
```

## How Enforcement Works

Enforcement uses three mechanisms — none of which consume context tokens:

### PreToolUse hook (`.claude/hooks/layer-guard.sh`)

Runs before every `Edit` or `Write` operation. Reads the current phase from `.claude/sdd-layer`, checks whether the target file is in an allowed directory, and blocks the operation (exit code 2) with a descriptive error message if not.

### PostToolUse hook (`.claude/hooks/post-edit.sh`)

Runs after every `Edit` or `Write` operation. If the edited file is under `src/` or `test/`, automatically runs `pytest` and injects the results into Claude's context.

### Phase state file (`.claude/sdd-layer`)

A single-line file containing the current phase name (`free`, `requirements`, `features`, etc.). Written by the slash commands, read by the hook. Gitignored — it's transient session state.

## The Feedback Mechanism

When Claude encounters a problem in an upstream layer, it must not edit that layer directly. Instead, it writes a feedback file:

| Working in | Problem found in | Write feedback to |
|-----------|-----------------|------------------|
| `specification/` | `doc/architecture/` | `doc/architecture/feedback/` |
| `test/` | `specification/` | `specification/feedback/` |
| `src/` | `test/` | `test/feedback/` |
| `src/` | `specification/` | `specification/feedback/` |

After writing feedback, Claude notifies you and stops. You then decide whether to resolve the upstream issue before continuing.

## Writing Guideline Skills

Detailed writing standards for each layer are available as on-demand skills (not loaded every session):

| Skill | Invoke with | Covers |
|-------|------------|--------|
| `writing-specs` | `/writing-specs` | Document structure, EARS template, Design by Contract, state machines |
| `writing-tests` | `/writing-tests` | Formula-derived bounds, mock discipline, contract tests |
| `writing-tasks` | `/writing-tasks` | Task structure template, completion rules |
| `writing-architecture` | `/writing-architecture` | Architecture doc format, component boundaries, data models |

## Autonomy Rules

Not all layers require the same level of human involvement:

| Layer | Autonomy | When human approval is needed |
|-------|----------|-------------------------------|
| `doc/requirements/` | Human-in-the-loop | Always, unless propagating from a clear user request |
| `doc/features/` | Human-in-the-loop | When originating changes; autonomous when propagating from requirements |
| `doc/architecture/` | Human-in-the-loop | When originating changes or making design decisions; autonomous when propagating from features |
| `specification/` | Fully autonomous | Never — Claude proceeds without asking |
| `test/` | Fully autonomous | Never |
| `src/` | Fully autonomous | Never |

**Originating vs. propagating:** If Claude is flowing downward through the pipeline (requirements→features→architecture), it propagates autonomously. If Claude needs to change a doc/ layer for other reasons (fixing a gap found during triage, making a design decision not prescribed by the layer above), it presents options with analysis and waits for approval.

**Feedback loop cap:** Claude tracks feedback resolution cycles (spec→tests→implementation→feedback→repeat). After 3 cycles, it stops and asks for direction rather than looping indefinitely.

## Full Pipeline: `/sdd`

To build a feature end-to-end through all SDD layers, use:

```
You:  /sdd "add caching to the retrieval pipeline"
```

This runs the full pipeline — requirements through implementation — setting the correct phase at each stage, handling feedback loops, and stopping when it needs your input.

### Starting from a specific layer

You can skip earlier stages by providing a starting layer as the first argument:

```
/sdd specification "fix MePo zero-frequency handling"   → starts at Stage 4
/sdd implementation "fix the weight calculation"         → starts at Stage 8
/sdd tests "add edge case coverage for empty input"      → starts at Stage 5
```

This is the typical flow after a bug fix: `/diagnose` finds the root cause and identifies the layer, then `/sdd <layer> "description"` executes the fix downward through implementation.

## Bug Fix Workflow

When fixing a bug, the issue usually doesn't start at requirements. Here is a step-by-step walkthrough.

### Step 1: Diagnose with `/diagnose`

Pass the bug report directly to `/diagnose`. It investigates the code, finds the root cause, and traces it up the authority chain — all in one step, without editing any files:

```
You:  /diagnose "impact_analysis returns only root node with 0 edges for
      stdlib lemmas (Nat.add_comm, Nat.add_0_r) — reverse dependency
      edges not populated"
```

Claude searches the codebase, traces the code path, reads the relevant spec and architecture docs, and reports:

```
Root cause: impact_analysis in src/poule/server/handlers.py queries the
dependency graph but the index only stores forward edges (A depends on B),
not reverse edges (B is depended on by A). The handler at line 245 calls
reader.get_dependents() which returns an empty list because reverse edges
were never populated during extraction.

| Layer          | Document                        | Status | Finding                              |
|----------------|---------------------------------|--------|--------------------------------------|
| Requirements   | doc/requirements/search.md      | OK     | Impact analysis is a P1 requirement  |
| Features       | doc/features/dependency.md      | OK     | Specifies reverse dependency lookup  |
| Architecture   | doc/architecture/retrieval.md   | GAP    | No mention of reverse edge storage   |
| Specification  | specification/storage.md        | GAP    | No reverse edge schema defined       |
| Tests          | test/test_impact.py             | GAP    | No test for stdlib reverse deps      |
| Implementation | src/poule/extraction/pipeline.py| ERROR  | Only writes forward edges            |

Recommendation: /sdd architecture "add reverse dependency edge storage"
```

If you already know the root cause and just need the triage, use `/triage` instead — it skips the investigation and goes straight to the authority chain audit.

### Step 2: Execute with `/sdd`

Use `/sdd` with the starting layer from the triage recommendation. It handles all downstream stages automatically — specs, tests, implementation, and feedback loops:

```
You:    /sdd specification "fix MePo zero-frequency handling"
        → Claude fixes the spec (Stage 4)
        → Claude updates tests (Stage 5)
        → Claude fixes the implementation (Stage 8)
        → PostToolUse hook runs pytest automatically
        → Claude reports completion
```

Or if the triage shows the problem is purely in implementation:

```
You:    /sdd implementation "fix MePo weight calculation to match spec"
```

### Step 3: Handle feedback loops

`/sdd` handles feedback loops automatically — if it encounters an upstream problem, it writes a feedback file and stops. Review the feedback and decide:

- **Feedback is valid**: run `/sdd` again starting at the upstream layer (e.g., `/sdd architecture "fix the design issue"`)
- **Feedback is invalid**: delete the feedback file and re-run `/sdd` from where it stopped

### Quick reference: what to say to Claude

| Situation | What to say |
|-----------|-------------|
| You have a bug report | `/diagnose "bug description"` |
| Claude found a root cause, wants to execute a plan | `/triage "description of the issue"` |
| Diagnosis/triage done, ready to fix | `/sdd <layer> "fix description"` |
| New feature, full pipeline | `/sdd "feature description"` |
| Claude wants to edit tests during implementation | "Don't modify tests. If the test is wrong, file feedback in `test/feedback/`." |
| You want to work without restrictions | `/free` |
| Claude wrote feedback and stopped | Review the feedback, then: `/sdd <upstream-layer> "fix the issue"` |

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

Pass the bug report directly to `/diagnose`. It investigates the code (using a subagent to keep context clean), finds the root cause, traces it up the authority chain, and then **acts on the result**:

- **Fix is at `specification/` or below** (all doc/ layers OK): Claude automatically proceeds to `/sdd` and fixes the bug without waiting. You'll see the triage table followed by the fix.
- **Fix requires `doc/` changes** (architecture, features, or requirements): Claude reports the triage table and presents options for your approval.

```
You:  /diagnose "MePo symbol_weight raises KeyError for zero-frequency symbols"

      → Claude investigates (subagent reads src/, test/, spec)
      → Triage: all doc/ layers OK, spec has a gap
      → Auto-fix: invokes /sdd specification "add zero-frequency edge case"
      → Claude fixes spec, updates tests, fixes implementation
      → Done
```

When the fix requires doc/ changes, Claude stops and asks:

```
You:  /diagnose "impact_analysis returns 0 edges for stdlib lemmas"

      → Triage: architecture has a GAP (no reverse edge storage)
      → Claude presents options:
        1. Add reverse edge table to storage architecture
        2. Compute reverse edges at query time (no schema change)
        3. ...
      → Waits for your approval before proceeding
```

If you already know the root cause and just need the triage, use `/triage` instead — it skips the investigation and goes straight to the authority chain audit (runs in an isolated context, read-only).

### Step 2: Handle the result

If `/diagnose` auto-fixed the bug (autonomous layers), you're done.

If `/diagnose` stopped for approval (doc/ layers), review the options and tell Claude which to proceed with. Claude will then run `/sdd` from the appropriate layer:

```
You:    Option 1 — add reverse edge table.
        → Claude runs /sdd architecture "add reverse dependency edge storage"
        → Proceeds autonomously through spec, tests, implementation
```

You can also invoke `/sdd` directly if you prefer:

```
You:    /sdd architecture "add reverse dependency edge storage"
```

### Step 3: Handle feedback loops

`/sdd` handles feedback loops automatically — if it encounters an upstream problem, it writes a feedback file and stops. Review the feedback and decide:

- **Feedback is valid**: run `/sdd` again starting at the upstream layer (e.g., `/sdd architecture "fix the design issue"`)
- **Feedback is invalid**: delete the feedback file and re-run `/sdd` from where it stopped

### Quick reference: what to say to Claude

| Situation | What to say |
|-----------|-------------|
| You have a bug report | `/diagnose "bug description"` (auto-fixes if spec or below) |
| Claude found a root cause, wants to execute a plan | `/triage "description"` (read-only audit) |
| `/diagnose` stopped for approval on doc/ changes | Choose an option; Claude proceeds with `/sdd` |
| New feature, full pipeline | `/sdd "feature description"` |
| You want to work without restrictions | `/free` |
| Claude wrote feedback and stopped | Review the feedback, then: `/sdd <upstream-layer> "fix the issue"` |

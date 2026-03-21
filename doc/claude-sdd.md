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
| 6. Implementation | `src/`, `test/`, `commands/` | Code, tests, slash command prompts |

Each layer is **derived from** the one above and **authoritative for** the one below. The core discipline: while working at one layer, do not edit layers above it.

## Phase Commands

Claude Code enforces the SDD discipline through **phase commands**. Each phase restricts which directories Claude can edit:

| Command | Purpose |
|---------|---------|
| `/triage` | Read-only audit: trace a root cause up the authority chain, report which layer to fix first |

| Command | Editable directories | Blocked from |
|---------|---------------------|-------------|
| `/requirements` | `doc/requirements/` | everything else |
| `/features` | `doc/features/` | everything else |
| `/architecture` | `doc/architecture/` | everything else |
| `/specification` | `specification/` | everything else |
| `/tasks` | `tasks/` | everything else |
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

This is the typical flow after a bug fix: `/triage` identifies the layer, then `/sdd <layer> "description"` executes the fix from that layer downward through implementation.

## Bug Fix Workflow

When fixing a bug, the issue usually doesn't start at requirements. Here is a step-by-step walkthrough.

### Step 1: Diagnose

Ask Claude to find the root cause. No phase needed — diagnosis is read-only.

```
You:  Tests in test_mepo.py are failing with "KeyError: 'weight'". Find the root cause.
```

Claude investigates and identifies the root cause.

### Step 2: Triage with `/triage`

When Claude has identified the root cause and is ready to fix, **don't let it execute yet**. Instead, run `/triage` to have Claude trace the problem up the authority chain and determine which layer to start at:

```
Claude: I've identified the root cause: the MePo symbol weighting doesn't
        handle zero-frequency symbols. Here's my plan... Ready to proceed?

You:    /triage "MePo zero-frequency symbol handling"
```

Claude reads (without editing) the relevant documents at each layer and reports a table:

```
| Layer          | Document                        | Status | Finding                              |
|----------------|---------------------------------|--------|--------------------------------------|
| Requirements   | doc/requirements/search.md      | OK     | No gap                               |
| Features       | doc/features/premise-search.md  | OK     | Mentions symbol weighting             |
| Architecture   | doc/architecture/retrieval.md   | OK     | Delegates formula to spec             |
| Specification  | specification/channels.md       | GAP    | No zero-frequency edge case defined   |
| Tests          | test/test_mepo.py               | GAP    | No test for zero-frequency input      |
| Implementation | src/poule/channels/mepo.py      | ERROR  | KeyError when frequency is 0          |

Recommendation: Start with /specification to add the zero-frequency edge case,
then /implementation to fix the code.
```

This tells you the fix starts at the specification layer, not just at the code.

### Step 3: Execute with `/sdd`

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

### Step 4: Handle feedback loops

`/sdd` handles feedback loops automatically — if it encounters an upstream problem, it writes a feedback file and stops. Review the feedback and decide:

- **Feedback is valid**: run `/sdd` again starting at the upstream layer (e.g., `/sdd architecture "fix the design issue"`)
- **Feedback is invalid**: delete the feedback file and re-run `/sdd` from where it stopped

### Quick reference: what to say to Claude

| Situation | What to say |
|-----------|-------------|
| Claude found a root cause, wants to execute a plan | `/triage "description of the issue"` |
| Triage done, fix is in code only | `/sdd implementation "fix description"` |
| Triage done, fix starts at spec | `/sdd specification "fix description"` |
| New feature, full pipeline | `/sdd "feature description"` |
| Claude wants to edit tests during implementation | "Don't modify tests. If the test is wrong, file feedback in `test/feedback/`." |
| You want to work without restrictions | `/free` |
| Claude wrote feedback and stopped | Review the feedback, then: `/sdd <upstream-layer> "fix the issue"` |

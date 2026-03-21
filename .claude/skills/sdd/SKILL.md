---
name: sdd
description: Run the Spec-Driven Development pipeline for a feature or change. Walks through SDD stages in order with enforced layer boundaries and feedback loops. Use when asked to build a feature end-to-end, propagate a change, fix a bug through SDD, or follow the SDD process. Accepts an optional starting layer as the first argument (e.g., "/sdd specification fix the caching bug").
disable-model-invocation: true
argument-hint: "[starting-layer] <description>"
---

# Spec-Driven Development Pipeline

Execute the SDD pipeline for: $ARGUMENTS

## Determine the starting stage

Parse the first word of the arguments. If it matches a layer name, start at that stage and skip earlier stages. Otherwise, start at Stage 1.

| First word | Start at |
|-----------|----------|
| `requirements` | Stage 1 |
| `features` | Stage 2 |
| `architecture` | Stage 3 |
| `specification` | Stage 4 |
| `tests` | Stage 5 |
| `implementation` | Stage 8 |
| *(anything else)* | Stage 1 (full pipeline) |

Work through the stages below **starting from the determined stage**. At each stage, set the phase to enforce layer boundaries. Do not invent requirements or infer unnecessary details — ask the user when ambiguities exist.

## Autonomy rules

**Human-in-the-loop layers** (`doc/requirements/`, `doc/features/`, `doc/architecture/`):
- **Propagating downward** from the stage above (e.g., requirements→features, features→architecture): proceed autonomously.
- **Originating changes** (writing initial content, fixing a gap found during triage, or making changes NOT derived from the stage immediately above): present 2-3 options with critical analysis and a recommendation. Wait for the user to approve before editing.

**Autonomous layers** (`specification/`, `test/`, `src/`):
- Proceed without human intervention.
- Track the number of feedback resolution cycles (Stage 5 → Stage 6/7 → back to Stage 5 counts as one cycle).
- **After 3 feedback cycles, stop and present the situation to the user.** This prevents infinite loops. Summarize what was attempted, what keeps failing, and ask for direction.

## Stage 1: Requirements

1. Run: `echo "requirements" > .claude/sdd-layer`
2. If propagating from a user request that clearly defines the requirements, write or update the PRD in `doc/requirements/` autonomously.
3. If the requirements already exist and are sufficient, confirm with the user and skip to Stage 2.
4. If the change requires judgment (e.g., scope decisions, priority trade-offs), present options with analysis and a recommendation. Wait for approval.

## Stage 2: Features

1. Run: `echo "features" > .claude/sdd-layer`
2. If propagating from Stage 1 (requirements just written or confirmed), propagate to `doc/features/` autonomously.
3. If this is the starting stage (no prior stage ran), or if the change requires judgment beyond what the requirements prescribe, present options with analysis and a recommendation. Wait for approval.
4. If a problem with the requirements is detected, do **not** edit requirements — surface the issue to the user and **stop**.

## Stage 3: Architecture

1. Run: `echo "architecture" > .claude/sdd-layer`
2. Read `doc/architecture/data-models/expression-tree.md` and `doc/architecture/data-models/index-entities.md`.
3. If propagating from Stage 2 (features just written or confirmed), propagate to `doc/architecture/` autonomously.
4. If this is the starting stage, or if the change involves design decisions not prescribed by the feature doc (e.g., choosing between data structures, adding new components), present options with analysis and a recommendation. Wait for approval.
5. If a problem is found in upstream documents, do **not** edit them — surface the issue to the user and **stop**.

## Stage 4: Specifications

*Autonomous — proceed without human intervention.*

1. Run: `echo "specification" > .claude/sdd-layer`
2. Read the parent architecture document.
3. Propagate architecture down to `specification/`.
4. If a problem is identified with the architecture, write a detailed description to `doc/architecture/feedback/` and **stop**. Notify the user — architecture changes require human approval.
5. When modifying existing specifications, note the blast radius (which specs changed).

## Stage 5: Tests

*Autonomous — proceed without human intervention.*

1. Run: `echo "tests" > .claude/sdd-layer`
2. Update tests within the blast radius and create tests for new specifications.
3. Do **not** change the specifications. If a problem is discovered, write to `specification/feedback/` instead.
4. Run `python -m pytest test/ -x -q` to confirm the new tests fail (they should — implementation doesn't exist yet).

## Stage 6: Specification Feedback Resolution

*Autonomous — but count this as a feedback cycle.*

1. Check if any `specification/feedback/` files exist. If none, skip to Stage 7.
2. Run: `echo "specification" > .claude/sdd-layer`
3. For each feedback item:
   - If **valid**: fix the specification.
   - If **invalid and the test is the problem**: run `echo "tests" > .claude/sdd-layer` and fix the test.
   - If **invalid and the architecture is the problem**: write to `doc/architecture/feedback/`, notify the user, and **stop**. Architecture changes require human approval.
4. Delete resolved feedback files.
5. If any architecture feedback was written, notify the user and **stop**.
6. Otherwise, return to Stage 5.

## Stage 7: Test Feedback Resolution

*Autonomous — but count this as a feedback cycle.*

1. Check if any `test/feedback/` files exist. If none, skip to Stage 8.
2. Run: `echo "tests" > .claude/sdd-layer`
3. For each feedback item:
   - If **valid**: fix the test.
   - If **invalid**: write to `specification/feedback/`, notify the user, and **stop**.
4. Delete resolved feedback files.

## Stage 8: Implementation

*Autonomous — proceed without human intervention.*

1. Run: `echo "implementation" > .claude/sdd-layer`
2. Read the relevant specifications and test files.
3. Write the implementation to make tests pass. Do **not** change tests or specifications.
4. If a problem is encountered, use the feedback mechanism:
   - Spec problem → write to `specification/feedback/`
   - Test problem → write to `test/feedback/`
5. Run `python -m pytest test/ -x -q` after each significant change.
6. After implementing as much as possible:
   - If any specification feedback was written, go to Stage 6.
   - If any test feedback was written, go to Stage 7.
7. **If 3 feedback cycles have been reached**, stop and present the situation to the user: summarize what was attempted, what keeps failing, and ask for direction.

## Stage 9: Completion

1. Run: `echo "free" > .claude/sdd-layer`
2. Check off completed tasks in `tasks/` (update `- [ ]` to `- [x]`).
3. If any feedback files still exist, notify the user and **stop**.
4. Report what was done and which files were changed.
5. Do **not** make a PR — the user decides when the branch is ready.

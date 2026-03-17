# Proof State Observation

Read-only access to proof states within an active session — the current state, a state at any step, or the full proof trace.

**Stories**: [Epic 2: Proof State Observation](../requirements/stories/proof-interaction-protocol.md#epic-2-proof-state-observation)

---

## Problem

Coq proof states are transient — they exist during interactive proving but are not preserved or queryable after the fact. An AI researcher building a training dataset must manually step through each proof and copy states by hand. A tool builder implementing proof search has no programmatic access to the state at each step.

## Solution

Three levels of observation granularity:

1. **Current state** — observe the live proof state at the session's current step position
2. **State at step k** — random-access read of the proof state after any tactic step in a completed proof
3. **Full trace** — extract all N+1 states and N tactics in a single call for efficient bulk collection

All observations return the same ProofState schema (see [proof-mcp-tools.md](proof-mcp-tools.md#proof-state-response-format)).

## Proof State Contents

Each proof state includes:
- All open goals, with the focused goal identified
- For each goal: the goal type and its local hypotheses
- The current step index (0 = initial state before any tactic)

This is the information a human sees in CoqIDE or Proof General at each step — the observation API makes it programmatically accessible.

## Full Trace Extraction

The full trace is the primary data product for AI researchers. A single call returns:
- The initial proof state (step 0)
- Each tactic applied and the resulting state (steps 1 through N)
- Metadata: proof name, file path, total step count

This avoids N+1 round trips for collecting training data. For a proof with 20 tactics, one call replaces 21 separate requests.

## Design Rationale

### Why three granularities instead of just "get state"

Different use cases have different access patterns:

- **Interactive exploration** (tool builders, Claude Code users): needs current state only, called after each tactic submission. Low latency, single state.
- **Analysis and debugging** (tool builders): needs random access to compare states at different steps. May jump to step 5, then step 12, without traversing the intermediate states.
- **Dataset collection** (AI researchers): needs the complete trace. Making N+1 separate calls would dominate collection time with round-trip overhead.

### Why step 0 is the initial state (before any tactic)

The initial proof state — the goal as stated in the theorem — is a critical piece of training data. It establishes the starting point. Numbering from 0 follows the convention that step k is "state after k tactics have been applied."

### Why full trace returns tactics alongside states

A proof state alone is not training data. The (state, tactic, next_state) triple is the fundamental unit of proof-step prediction. Returning tactics inline with states avoids clients needing to correlate two separate sequences.

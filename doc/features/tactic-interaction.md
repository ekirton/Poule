# Tactic Interaction

Submit tactics to the Coq proof engine and navigate through the proof script, forming the observe-submit-feedback loop that enables programmatic proof exploration.

**Stories**: [Epic 3: Tactic Interaction](../requirements/stories/proof-interaction-protocol.md#epic-3-tactic-interaction)

---

## Problem

Interacting with the Coq proof engine programmatically requires low-level SerAPI or coq-lsp protocol manipulation. There is no simple "submit a tactic, get the result" interface for external tools. Tool builders and AI researchers who want to implement proof search algorithms must build their own Coq integration from scratch.

## Solution

Four interaction primitives within an active session:

1. **Submit tactic** — send a single tactic string, receive the resulting proof state or a structured error
2. **Step backward** — undo the last tactic, returning to the previous proof state
3. **Step forward** — replay the next tactic from the original proof script (for completed proofs)
4. **Submit batch** — send multiple tactics in one request, receiving state after each step

These primitives support two distinct workflows: exploratory proving (submit + backward) and proof replay (step forward).

## Submit–Observe Loop

The core interaction pattern:

1. Observe the current proof state (goals, hypotheses)
2. Submit a tactic
3. Observe the resulting state (success) or read the error (failure)
4. If the approach is wrong, step backward and try a different tactic

On success, the proof state advances: goals may be closed, new goals may appear, hypotheses may change. On failure, the proof state is unchanged — the tactic is rejected, and the error message from Coq is returned in a structured format.

When a tactic closes all remaining goals, the response indicates the proof is complete.

## Stepping Through Existing Proofs

For completed proofs, step-forward replays the original proof script one tactic at a time. This is distinct from submit — the tactic comes from the recorded script, not from the client. Step-forward is useful for:

- Observing state transitions in existing proofs without manually copying each tactic
- Building training data from existing proof scripts
- Understanding how a proof works step by step

## Batch Submission

Batch tactic submission reduces round-trip overhead when a client has a sequence of tactics to try. The server processes tactics sequentially, returning the state after each step. If a tactic fails, processing stops: earlier successful results are returned, the failing tactic gets a structured error, and remaining tactics are not executed.

This is not parallel execution — tactics are inherently sequential (each depends on the state left by the previous one). Batch submission is an optimization for reducing network round trips, not for parallelism.

## Design Rationale

### Why separate submit from step-forward

Submit and step-forward serve different purposes: submit is for exploration (the client chooses the tactic), step-forward is for replay (the tactic comes from the script). Conflating them into one operation would require the client to pass the original tactic text even when replaying, which is error-prone and defeats the purpose.

### Why step-backward undoes exactly one step

Multi-step undo adds complexity (which state do you go back to?) and the single-step model composes naturally: call step-backward N times to go back N steps. For random access to an earlier state, use the observation API (get state at step k) instead.

### Why batch stops on first failure

The alternative — skip failures and continue — would produce a non-linear tactic history that is hard to reason about. Stopping on first failure matches the semantics of running tactics interactively: if a tactic fails, you fix it before proceeding.

### Why batch is P1 (should-have) rather than P0

The submit + step-backward primitives are sufficient for all use cases. Batch is a performance optimization for clients that know their tactic sequence in advance — primarily automated proof search. Interactive use rarely needs it.

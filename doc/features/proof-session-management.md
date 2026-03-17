# Proof Session Management

Interactive proof sessions that allow external tools to observe and interact with Coq proof states over time. Each session encapsulates a single proof within a single .v file, maintaining independent state from other sessions.

**Stories**: [Epic 1: Session Management](../requirements/stories/proof-interaction-protocol.md#epic-1-session-management), [Epic 7: Error Handling and Resilience](../requirements/stories/proof-interaction-protocol.md#epic-7-error-handling-and-resilience)

---

## Problem

Coq's existing external interfaces (SerAPI, coq-lsp) are designed for single-client IDE workflows. There is no protocol for multiple independent tools to interact with proof states concurrently. A tool builder who wants to explore two alternative proof strategies in parallel must manually manage separate processes and reconstruct state from scratch.

## Solution

A session-based interaction model where each session:
- Is opened by specifying a .v file and a named proof
- Returns a unique session ID used for all subsequent operations
- Maintains its own proof state, tactic history, and step position
- Is explicitly closed when no longer needed, or auto-closed after inactivity

Multiple sessions can be open simultaneously, including on the same proof — each with fully independent state.

## Session Lifecycle

### Opening

A session is opened by specifying a .v file path and the name of a proof within it. The server loads the file, positions at the proof, and returns the initial proof state along with a session ID. If the file does not exist or the proof name is not found, a structured error is returned immediately.

### Active Use

While active, a session accepts tactic submissions, state observations, step navigation, and trace extraction. Each operation references the session by its ID. The session tracks the full tactic history and allows stepping forward and backward through it.

### Closing

A session is explicitly closed by the client, releasing all resources (Coq backend processes, in-memory state). After closing, any operation referencing that session ID returns a structured error.

### Listing

Clients can enumerate all active sessions to discover their metadata: session ID, file path, proof name, current step index, and creation timestamp.

## Concurrency Model

Sessions are fully isolated. Actions in one session never affect the state of another, even when multiple sessions are open on the same proof in the same file. This isolation extends to error conditions — a crash in one session's Coq backend does not affect other sessions.

The target is at least 3 concurrent sessions without state interference.

## Resilience

### Session Timeout

Sessions that receive no tool calls for 30 minutes are automatically closed and their resources released. This prevents abandoned sessions from leaking memory or processes in long-running server deployments. The timeout duration is a server-side default, not configurable per-session in the initial release.

### Backend Crash Isolation

Each session's Coq backend process is isolated. If one crashes — due to a pathological tactic, out-of-memory, or a Coq bug — the failure is contained to that session. Other sessions continue normally. The crashed session returns a structured error on the next tool call referencing it.

## Design Rationale

### Why session-based rather than stateless

Coq proof interaction is inherently stateful — each tactic changes the proof state, and stepping backward requires remembering the history. A stateless API would force clients to replay the full tactic sequence on every request, which is too slow for interactive use (tactic execution takes 10s–100s of milliseconds each).

### Why explicit session IDs rather than implicit state

Explicit session IDs allow clients to manage multiple concurrent proof explorations and to hand off session references between components. An implicit "current session" model would not support the concurrent use case that AI researchers need for parallel proof search.

### Why auto-close on timeout rather than relying on explicit close

Tools crash. Network connections drop. AI research scripts abort. Without a timeout, every abnormal termination would leak a Coq backend process. The 30-minute timeout is generous enough that no normal interactive use will hit it, but short enough to bound resource leakage.

### Why crash isolation per session

The primary users (AI researchers running parallel proof search) will submit speculative, potentially pathological tactics. A crash in one exploration branch must not invalidate other branches. Process-level isolation is the simplest mechanism that provides this guarantee.

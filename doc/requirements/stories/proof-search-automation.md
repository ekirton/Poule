# User Stories: Proof Search & Automation

Derived from [doc/requirements/proof-search-automation.md](../proof-search-automation.md).

---

## Epic 1: Proof Search

### 1.1 Best-First Proof Search

**As a** Coq developer using Claude Code,
**I want** Claude to invoke an algorithmic proof search tool that systematically explores tactic sequences and verifies each against Coq,
**so that** routine proof obligations can be discharged automatically, faster than conversational back-and-forth.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a proof session with an open goal WHEN proof search is invoked THEN it explores a tree of tactic sequences using best-first search, verifying each candidate tactic against Coq before expanding further
- GIVEN a successful proof search WHEN the result is returned THEN it includes the complete verified proof script with each tactic and the proof state after each step
- GIVEN a proof search that does not find a complete proof within the timeout WHEN the result is returned THEN it includes the deepest partial proof achieved and the number of states explored

**Traces to:** R4-P0-1, R4-P0-2, R4-P0-3

### 1.2 Proof Search MCP Tool

**As a** Coq developer using Claude Code,
**I want** proof search exposed as an MCP tool,
**so that** Claude can invoke it during our conversational workflow without requiring manual setup.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a running MCP server WHEN the proof search tool is invoked with a proof session ID THEN it attempts to find a complete proof for the current proof state
- GIVEN the proof search tool WHEN it is invoked without a timeout parameter THEN the default timeout of 30 seconds is applied
- GIVEN the proof search tool WHEN it is invoked with a custom timeout THEN that timeout is respected
- GIVEN the MCP server WHEN its tool list is inspected THEN a proof search tool is present with a documented schema

**Traces to:** R4-P0-4, R4-P0-5

### 1.3 Search State Caching

**As a** Coq developer waiting for proof search results,
**I want** the search to detect and prune duplicate proof states reached by different tactic sequences,
**so that** the search budget is spent on genuinely new states rather than redundant exploration.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a proof search WHEN two different tactic sequences lead to the same proof state THEN the system recognizes the duplicate and does not re-explore from that state
- GIVEN a proof search with caching WHEN it completes THEN the total number of Coq verification calls is strictly less than the total number of candidate tactics considered

**Traces to:** R4-P0-6

### 1.4 Configurable Search Parameters

**As a** Coq developer or AI researcher,
**I want to** configure search depth, breadth limits, and timeout,
**so that** I can trade off between search thoroughness and time budget.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a proof search request with a specified maximum search depth WHEN search runs THEN it does not explore tactic sequences longer than the specified depth
- GIVEN a proof search request with a specified breadth limit WHEN search runs THEN it does not expand more than the specified number of candidate tactics at each node
- GIVEN a proof search request with a specified timeout WHEN the timeout elapses THEN search terminates and returns the best partial progress

**Traces to:** R4-P1-3

---

## Epic 2: Tactic Candidate Generation

### 2.1 Premise-Augmented Candidate Generation

**As a** Coq developer with indexed libraries,
**I want** proof search to retrieve relevant lemmas from Semantic Lemma Search and include them in the tactic generation prompt,
**so that** search candidates can reference lemmas I might not know about.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an indexed library database and a proof state WHEN proof search generates tactic candidates THEN relevant premises are retrieved and included as context for candidate generation
- GIVEN no indexed library database is available WHEN proof search generates candidates THEN candidates are generated using only the proof state and local context
- GIVEN retrieved premises WHEN candidates are generated THEN some candidates reference retrieved lemmas (e.g., `apply retrieved_lemma`, `rewrite retrieved_lemma`)

**Traces to:** R4-P0-7, R4-P0-8, R4-P0-9

### 2.2 Neuro-Symbolic Interleaving

**As a** Coq developer,
**I want** proof search to include symbolic automation tactics (CoqHammer, `auto`, `omega`, `lia`) alongside LLM-generated candidates at each node,
**so that** mechanical sub-goals are discharged by fast solvers rather than consuming LLM budget.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a proof search node WHEN candidates are generated THEN the candidate set includes both LLM-generated tactics and invocations of symbolic solvers
- GIVEN a proof state that is dischargeable by `omega` or `auto` WHEN proof search encounters it THEN the solver tactic is tried and, if successful, used to close the sub-goal without an LLM call
- GIVEN a completed proof found by search WHEN it is inspected THEN it may contain a mix of LLM-generated and solver tactics

**Traces to:** R4-P1-1

### 2.3 Diversity-Aware Candidate Selection

**As a** Coq developer waiting for proof search results,
**I want** the search to filter near-duplicate tactic candidates before verifying them against Coq,
**so that** the search budget is spent on genuinely different proof directions.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a set of tactic candidates for a proof state WHEN candidates are selected for verification THEN near-duplicate candidates (syntactically or semantically equivalent) are filtered or de-prioritized
- GIVEN diversity-aware selection WHEN proof search completes THEN the explored tactic sequences cover a broader range of proof strategies compared to non-diverse selection

**Traces to:** R4-P1-2

### 2.4 Few-Shot Context from Training Data

**As a** Coq developer,
**I want** proof search to retrieve similar proof states and their successful tactics from extracted training data and use them as few-shot context,
**so that** tactic candidate generation benefits from patterns in existing Coq proof developments.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN extracted training data for a Coq project WHEN proof search generates candidates for a proof state THEN similar proof states and their successful tactics are retrieved and included as few-shot context
- GIVEN few-shot examples WHEN they are used THEN search success rate improves compared to search without few-shot context (measured on a held-out evaluation set)

**Traces to:** R4-P1-4

---

## Epic 3: Fill Admits

### 3.1 Fill-Admits Tool

**As a** Coq developer with a partially complete proof,
**I want** Claude to invoke a tool that scans my proof script for `admit` calls and attempts to discharge each one using proof search,
**so that** I can sketch a proof with placeholders and have the routine parts filled in automatically.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a proof script file containing `admit` calls WHEN fill-admits is invoked THEN it identifies each `admit` and invokes proof search on the corresponding sub-goal
- GIVEN a fill-admits run WHEN it completes THEN the result indicates which admits were successfully filled and which remain open
- GIVEN a successfully filled admit WHEN the replacement is inspected THEN it is a Coq-verified tactic sequence that closes the sub-goal

**Traces to:** R4-P1-5

### 3.2 Fill-Admits MCP Tool

**As a** Coq developer using Claude Code,
**I want** fill-admits exposed as an MCP tool,
**so that** Claude can invoke it when I ask to fill in the holes in my proof.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a running MCP server WHEN the fill-admits tool is invoked with a file path THEN it processes the file and returns results for each `admit`
- GIVEN the MCP server WHEN its tool list is inspected THEN a fill-admits tool is present with a documented schema

**Traces to:** R4-P1-6

### 3.3 Sketch-Then-Prove

**As a** Coq developer working on a complex proof,
**I want** to write a proof sketch with `admit` stubs as intermediate subgoals and have proof search attempt to fill each stub independently,
**so that** complex proofs can be decomposed into manageable sub-problems.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a proof script with `admit` stubs as intermediate subgoals WHEN sketch-then-prove is invoked THEN proof search is applied independently to each stub
- GIVEN a partially filled sketch WHEN the result is returned THEN it indicates which stubs were successfully filled and which remain open
- GIVEN all stubs successfully filled WHEN the combined script is inspected THEN the complete proof is valid according to Coq

**Traces to:** R4-P1-7

---

## Epic 4: Search Telemetry and Difficulty Estimation

### 4.1 Pluggable Candidate Generation Backends

**As an** AI researcher evaluating different models for Coq proof search,
**I want** the search tool to support pluggable tactic candidate generation backends beyond Claude,
**so that** I can compare model performance or use open-source models for offline search.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a search configuration WHEN a non-default candidate generation backend is specified THEN the search uses that backend for tactic generation
- GIVEN a pluggable backend WHEN it is used THEN the verification, caching, and search strategy remain the same

**Traces to:** R4-P2-1

### 4.2 Proof Difficulty Estimation

**As a** Coq developer deciding whether to invoke proof search,
**I want** the system to estimate the difficulty and likely proof distance for a goal,
**so that** Claude and I can make informed decisions about whether automated search is likely to succeed.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a proof state WHEN difficulty estimation is requested THEN the system returns an estimated difficulty level and approximate number of remaining proof steps
- GIVEN the estimation WHEN it is presented THEN it includes a confidence indicator

**Traces to:** R4-P2-2

### 4.3 Subgoal Decomposition

**As a** Coq developer working on a complex goal,
**I want** the search to break the goal into a sequence of intermediate subgoals and attempt each independently,
**so that** complex goals can be tackled incrementally even when full search times out.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a complex proof goal WHEN subgoal decomposition is requested THEN the system proposes a sequence of intermediate subgoals
- GIVEN proposed subgoals WHEN they are attempted THEN each is attempted independently using proof search
- GIVEN a decomposition attempt WHEN it completes THEN the result indicates which subgoals were discharged and which remain open

**Traces to:** R4-P2-3

### 4.4 Search Telemetry

**As an** AI researcher improving proof search strategies,
**I want** search to collect telemetry (states explored, time per candidate, success rate by tactic type),
**so that** I can analyze search behavior and identify bottlenecks.

**Priority:** P2
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a completed proof search WHEN telemetry is inspected THEN it includes total states explored, unique states explored, time per candidate verification, and success rate by tactic type
- GIVEN telemetry data WHEN it is serialized THEN it uses a structured JSON format

**Traces to:** R4-P2-4

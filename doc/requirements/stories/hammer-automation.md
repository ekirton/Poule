# User Stories: Automated Proving via Hammer

Derived from [doc/requirements/hammer-automation.md](../hammer-automation.md).

---

## Epic 1: Hammer Invocation

### 1.1 Invoke Hammer in an Active Proof Session

**As a** Coq developer using Claude Code,
**I want to** ask Claude to try hammer on my current proof goal,
**so that** the goal is discharged automatically without me needing to know CoqHammer syntax.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active proof session with an open goal WHEN hammer automation is invoked THEN the `hammer` tactic is submitted through the proof interaction protocol and the result is returned
- GIVEN no active proof session WHEN hammer automation is invoked THEN a clear error is returned indicating that a proof session must be active
- GIVEN a proof session with multiple open goals WHEN hammer automation is invoked THEN it targets the current focused goal

**Traces to:** RH-P0-1

### 1.2 Invoke sauto and qauto Variants

**As a** Coq developer using Claude Code,
**I want to** ask Claude to try `sauto` or `qauto` on my current proof goal,
**so that** I can use lighter-weight automation when full hammer is unnecessary or too slow.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active proof session with an open goal WHEN `sauto` automation is invoked THEN the `sauto` tactic is submitted through the proof interaction protocol and the result is returned
- GIVEN an active proof session with an open goal WHEN `qauto` automation is invoked THEN the `qauto` tactic is submitted through the proof interaction protocol and the result is returned
- GIVEN a choice between `sauto` and `qauto` WHEN the user does not specify which to use THEN Claude can choose based on context or try both

**Traces to:** RH-P0-2

### 1.3 Expose as Mode of Existing Tools

**As a** Coq developer using Claude Code,
**I want** hammer automation to be available through existing proof interaction tools rather than as separate top-level tools,
**so that** the MCP tool count stays within the budget that ensures Claude's accuracy.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN the MCP server's tool list WHEN it is inspected THEN hammer automation does not appear as a new top-level tool
- GIVEN an existing proof interaction tool WHEN it is invoked with a hammer mode or tactic parameter THEN it executes the hammer tactic and returns the result
- GIVEN a user who has never used CoqHammer WHEN they ask Claude to "try to prove this automatically" THEN Claude can invoke hammer through the existing tool interface without additional setup

**Traces to:** RH-P0-6

---

## Epic 2: Result Handling

### 2.1 Handle Success — Return Verified Proof Script

**As a** Coq developer using Claude Code,
**I want** hammer to return the verified proof script when it succeeds,
**so that** I can insert the proof into my development with confidence that it is correct.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a hammer invocation that succeeds WHEN the result is returned THEN it includes the complete tactic script that closes the goal
- GIVEN a successful proof script returned by hammer WHEN it is submitted to Coq independently THEN it is accepted without error
- GIVEN a successful `hammer` invocation WHEN it finds a proof via ATP reconstruction THEN the returned script uses only Coq-native tactics (the reconstruction, not the ATP proof)

**Traces to:** RH-P0-3

### 2.2 Handle Failure — Return Diagnostics

**As a** Coq developer using Claude Code,
**I want** hammer to return structured diagnostic information when it fails,
**so that** Claude can explain why automation did not work and suggest what to try next.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a hammer invocation that fails WHEN the result is returned THEN it includes a structured failure reason (e.g., timeout, no proof found, reconstruction failure)
- GIVEN a hammer failure due to timeout WHEN the diagnostic is returned THEN it indicates that the timeout was reached and reports the timeout value used
- GIVEN a hammer failure WHEN the diagnostic is returned THEN it includes any partial progress information available (e.g., ATP solver found a proof but reconstruction failed)

**Traces to:** RH-P0-4

---

## Epic 3: Configuration

### 3.1 Configure Timeout

**As a** Coq developer using Claude Code,
**I want to** configure the timeout for hammer invocations,
**so that** I can balance between giving hammer enough time and not waiting too long on hopeless goals.

**Priority:** P0
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a hammer invocation with a specified timeout WHEN the tactic runs THEN it respects the specified timeout
- GIVEN a hammer invocation without a specified timeout WHEN the tactic runs THEN a sensible default timeout is applied
- GIVEN a timeout value WHEN it is specified THEN it is passed through to the underlying CoqHammer tactic

**Traces to:** RH-P0-5

### 3.2 Configure sauto and qauto Options

**As a** Coq developer using Claude Code,
**I want to** pass options to `sauto` and `qauto` (e.g., search depth, unfolding hints),
**so that** I can tune automation when the defaults do not work for my particular goal.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a `sauto` invocation with a search depth parameter WHEN the tactic runs THEN the specified depth limit is applied
- GIVEN a `qauto` invocation with unfolding hints WHEN the tactic runs THEN the specified definitions are unfolded during search
- GIVEN a `sauto` or `qauto` invocation without options WHEN the tactic runs THEN sensible defaults are applied

**Traces to:** RH-P1-4

---

## Epic 4: Multi-Strategy Automation

### 4.1 Try Multiple Strategies Sequentially

**As a** Coq developer using Claude Code,
**I want** Claude to try multiple hammer strategies in sequence (e.g., `hammer`, then `sauto`, then `qauto`) and return the first success,
**so that** I do not need to know which variant is most likely to work for my goal.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN an active proof session with an open goal WHEN multi-strategy automation is invoked THEN `hammer`, `sauto`, and `qauto` are tried in sequence
- GIVEN a multi-strategy invocation WHEN one of the tactics succeeds THEN the successful result is returned immediately without trying remaining tactics
- GIVEN a multi-strategy invocation WHEN all tactics fail THEN the result includes diagnostics from each attempt
- GIVEN a multi-strategy invocation WHEN the combined time exceeds the timeout THEN the sequence is terminated and the diagnostics collected so far are returned

**Traces to:** RH-P1-1

### 4.2 Pass Lemma Hints to Hammer

**As a** Coq developer using Claude Code,
**I want to** supply lemma hints to hammer tactics when I or Claude know which lemmas might be relevant,
**so that** hammer can find proofs that require specific lemmas it might not discover on its own.

**Priority:** P1
**Stability:** Stable

**Acceptance criteria:**
- GIVEN a hammer invocation with specified lemma hints WHEN the tactic runs THEN the hints are passed to the underlying CoqHammer tactic
- GIVEN a `sauto` invocation with lemma hints WHEN the tactic runs THEN the hints are included in the search
- GIVEN a hammer invocation without hints WHEN the tactic runs THEN it proceeds with CoqHammer's default premise selection

**Traces to:** RH-P1-2

### 4.3 Return Both ATP and Reconstructed Proof

**As a** Coq developer using Claude Code,
**I want** to see both the high-level proof found by the ATP solver and the low-level reconstructed Coq tactic script when hammer succeeds,
**so that** I can choose which form to keep in my development.

**Priority:** P1
**Stability:** Draft

**Acceptance criteria:**
- GIVEN a successful `hammer` invocation that used an ATP solver WHEN the result is returned THEN it includes the reconstructed Coq tactic script
- GIVEN a successful `hammer` invocation WHEN the ATP-level proof is available THEN it is also included in the result alongside the reconstructed script
- GIVEN a successful `sauto` or `qauto` invocation WHEN the result is returned THEN only the Coq tactic script is included (no ATP proof exists)

**Traces to:** RH-P1-3

# Coq Proof Backend

Per-session coqtop process wrapper providing bidirectional, stateful proof interaction.

**Architecture**: [proof-session.md](../doc/architecture/proof-session.md) (CoqBackend Interface, Process Isolation, Crash Detection), [component-boundaries.md](../doc/architecture/component-boundaries.md) (Proof Session Manager → Coq Backend Processes)
**Data models**: [proof-types.md](../doc/architecture/data-models/proof-types.md)

---

## 1. Purpose

Define the `CoqBackend` protocol and the `create_coq_backend` factory function that the Proof Session Manager uses to spawn and communicate with per-session coqtop processes. The backend provides a uniform async interface for file loading, proof positioning, tactic execution, state observation, undo, premise extraction, and process shutdown — all through a single coqtop subprocess per session.

## 2. Scope

**In scope**: `CoqBackend` protocol definition, `create_coq_backend` factory, coqtop process spawning and communication (sentinel-based framing), `.v` file loading and proof positioning, tactic execution and state translation (parsing `Show.` output), tactic boundary detection (sentence splitting), undo mechanism, premise extraction via proof term diffing (`Show Proof.`), vernacular command execution, process shutdown and crash detection, error translation.

**Out of scope**: Session registry and lifecycle management (owned by proof-session), proof state serialization (owned by proof-serialization), MCP protocol handling (owned by mcp-server), extraction of declarations from `.vo` files (owned by extraction — uses coq-lsp, a separate backend with a different interface).

## 3. Definitions

| Term | Definition |
|------|-----------|
| CoqBackend | An async protocol wrapping a single coqtop subprocess for interactive proof exploration |
| Backend factory | An async callable `(file_path: str) -> CoqBackend` that spawns a new coqtop process |
| Proof positioning | Loading a `.v` file prelude and navigating to a named proof, making its initial state observable |
| Original script | The sequence of tactic strings comprising a completed proof's body, extracted by sentence splitting |
| Sentence splitter | A regex-based parser that segments a proof body into individual tactic commands |
| Sentinel framing | An output boundary detection mechanism using a probe command (`Check __POULE_SENTINEL__.`) whose known error response marks the end of the previous command's output |
| Proof term diffing | Extracting per-tactic premise annotations by comparing the `Show Proof.` output before and after each tactic step |

## 4. Behavioral Requirements

### 4.1 CoqBackend Protocol

The `CoqBackend` protocol defines 10 async operations. All operations except `shutdown` may raise exceptions on failure. Every `CoqBackend` instance is bound to a single coqtop process — it is not reusable across processes.

#### load_file(file_path)

- REQUIRES: `file_path` is a non-empty string pointing to a `.v` source file.
- ENSURES: The backend reads the `.v` file and sends all content preceding the target proof to the coqtop process: `Require Import` directives, module headers, prior definitions, and notation declarations. After successful return, the file's context is loaded and proofs are available for positioning. The backend retains the file path and parsed prelude for the lifetime of the process.
- On file not found or unreadable: raises `FileNotFoundError` or `OSError`.
- On Coq check failure (syntax error, dependency missing): raises an exception with the Coq error message.

The prelude is extracted from the source file using the same `_extract_prelude_up_to_proof` mechanism currently used by `ProofTermResolver`: all content from the file start up to (but not including) the first proof-mode-entering command is sent to coqtop sentence by sentence.

> **Given** a valid `.v` file with no Coq errors
> **When** `load_file(path)` is called
> **Then** the call returns successfully and proofs in the file are available for positioning

> **Given** a path to a file that does not exist
> **When** `load_file(path)` is called
> **Then** `FileNotFoundError` is raised

> **Given** a `.v` file with a syntax error in its prelude
> **When** `load_file(path)` is called
> **Then** an exception is raised containing the Coq error diagnostic

#### position_at_proof(proof_name)

- REQUIRES: `load_file` has been called successfully. `proof_name` is a non-empty string.
- ENSURES: The backend sends the named proof's theorem statement and `Proof.` command to coqtop, entering proof mode. It queries `Show.` for the initial proof state and parses the output into a `ProofState`. If the proof has an existing tactic script, the backend makes it accessible via `original_script`. During positioning, the backend caches the proof state text and proof term text at each step of the original script replay (see `original_states`).
- On proof not found: raises `ValueError`, `KeyError`, or `LookupError`.

The backend locates the proof in the source file using the proof name and extracts the theorem statement. For proofs that follow a previous proof in the same file, the backend sends all intervening vernacular (definitions, imports, etc.) to coqtop before the theorem statement.

The returned `ProofState` shall have:
- `schema_version`: the current schema version (1)
- `session_id`: empty string (the session manager stamps the real session ID)
- `step_index`: 0
- `is_complete`: false (the proof has at least one goal at step 0)
- `focused_goal_index`: 0 (the first goal is focused)
- `goals`: at least one Goal with the proof statement as its type

> **Given** a loaded file containing `Lemma add_comm : forall n m, n + m = m + n.`
> **When** `position_at_proof("add_comm")` is called
> **Then** the returned ProofState has step_index=0, is_complete=false, and goals[0].type contains "forall n m, n + m = m + n" (or the Coq-normalized form)

> **Given** a loaded file that does not contain a proof named "nonexistent"
> **When** `position_at_proof("nonexistent")` is called
> **Then** a `ValueError`, `KeyError`, or `LookupError` is raised

#### original_script (attribute)

- REQUIRES: `position_at_proof` has been called successfully.
- ENSURES: A `list[str]` containing the tactic strings from the proof's existing script, in order. Empty list if the proof has no script (e.g., opened interactively without a body).
- Each string is a single tactic command as it appears in the source, including the trailing period (e.g., `"intros n m."`).
- Tactic boundaries shall be derived from a sentence splitter that segments the proof body text (between the `Proof.` keyword and the `Qed`/`Defined`/`Admitted`/`Abort` terminator) into individual sentences.

The sentence splitter shall handle:
- **Standard period-terminated sentences**: Split on `.` followed by whitespace or EOF.
- **Bullet markers** (`-`, `+`, `*`, `--`, `++`, `**`): Each bullet at line start is a separate sentence. Split before each bullet.
- **Braces** (`{`, `}`): Each brace is its own sentence.
- **Periods inside comments** (`(* ... *)`): Strip comments before splitting.
- **Periods inside strings** (`"..."`): Skip string literals.
- **ssreflect tactic chains** (`move=> /eqP H; rewrite H.`): The period ends the chain; semicolons are internal. This parses correctly with period-based splitting.
- **Numeric literals** (`1`, `2.5`): Not a concern — Coq tactic-mode periods are always followed by whitespace or EOF.

> **Given** a proof with body `intros n m. ring.`
> **When** `original_script` is accessed after `position_at_proof`
> **Then** it returns `["intros n m.", "ring."]`

> **Given** a proof with no existing body (just `Proof.` with no tactics)
> **When** `original_script` is accessed
> **Then** it returns `[]`

> **Given** a proof with body `intros n. - simpl. ring. - reflexivity.` (using bullet markers)
> **When** `original_script` is accessed after `position_at_proof`
> **Then** each bullet marker and its tactic are correctly split as separate sentences

> **Given** a proof without an explicit `Proof.` keyword where tactics begin directly after the statement (e.g., `Lemma foo : P. intros. auto. Qed.`)
> **When** `original_script` is accessed after `position_at_proof`
> **Then** it returns the tactic list (same as if `Proof.` were present)

#### original_states (attribute)

- REQUIRES: `position_at_proof` has been called successfully.
- ENSURES: A `list` of cached state records, one per successfully replayed step of the original script (index 0 = initial state before any tactic, index k = state after tactic k). Each record contains the parsed proof state text (`Show.` output) and the proof term text (`Show Proof.` output) at that step.
- During `position_at_proof`, the backend replays the original script by sending each tactic to coqtop and caching `Show.` and `Show Proof.` output at each step. If a tactic fails at step k, the list contains states 0..k-1 (the successfully replayed prefix).
- The session manager uses `original_states` to provide proof states and premise annotations without requiring a second replay.

> **Given** a proof with 5 tactics that all replay successfully
> **When** `original_states` is accessed after `position_at_proof`
> **Then** it contains 6 cached state records (initial + one per tactic)

> **Given** a proof with 5 tactics where tactic 3 fails during replay
> **When** `original_states` is accessed after `position_at_proof`
> **Then** it contains 3 cached state records (initial + states after tactics 1 and 2)

#### execute_tactic(tactic)

- REQUIRES: A proof is active (either via `position_at_proof` or a previous `execute_tactic` that did not complete the proof). `tactic` is a non-empty string.
- ENSURES: The tactic is sent to coqtop for execution. On success, queries `Show.` and parses the output into a `ProofState`. On Coq-level failure (invalid tactic, type mismatch, etc.), raises an exception containing the Coq error message; the backend's internal state is unchanged (the failed tactic is not applied).

The returned `ProofState` shall have:
- `step_index`: the value the session manager will assign (the backend may return 0; the session manager overwrites this)
- `is_complete`: true if no goals remain after the tactic (coqtop prints `No more goals.` or `No more subgoals.`)
- `focused_goal_index`: the index of the focused goal, or null if complete
- `goals`: the updated goal list

> **Given** a proof at step 0 with goal `forall n m, n + m = m + n`
> **When** `execute_tactic("intros n m.")` succeeds
> **Then** the returned ProofState has goals with hypotheses `n : nat` and `m : nat`, and the goal type is `n + m = m + n`

> **Given** a proof at step 1
> **When** `execute_tactic("invalid_not_a_tactic.")` is called and Coq rejects it
> **Then** an exception is raised with the Coq error message, and the backend state remains at step 1

> **Given** a proof with one remaining goal
> **When** `execute_tactic("reflexivity.")` closes the last goal
> **Then** the returned ProofState has `is_complete = true`, `focused_goal_index = null`, and `goals = []`

#### get_proof_state()

- REQUIRES: A proof is active.
- ENSURES: Sends `Show.` to coqtop and parses the output into a `ProofState`.

#### undo()

- REQUIRES: A proof is active and at least one tactic has been executed.
- ENSURES: Sends `Undo.` to coqtop. The last applied tactic is undone. coqtop supports `Undo` natively, so this is a single command.
- On failure: may raise an exception. The session manager treats undo failure as best-effort.

> **Given** a proof at step 3 after executing tactics T1, T2, T3
> **When** `undo()` is called
> **Then** the backend state is equivalent to the state after T1 and T2 (step 2)

#### get_proof_term()

- REQUIRES: A proof is active.
- ENSURES: Sends `Show Proof.` to coqtop and returns the raw proof term text. The text contains the proof term built so far, with `?Goal` placeholders for unsolved goals and fully qualified constant references (e.g., `@Nat.add_comm`).
- On coqtop failure: returns an empty string.

> **Given** a proof at step 0 (initial state)
> **When** `get_proof_term()` is called
> **Then** the returned text contains only `?Goal` (no constants yet)

> **Given** a proof where the last tactic was `apply Nat.add_comm.`
> **When** `get_proof_term()` is called
> **Then** the returned text contains `@Nat.add_comm` (or its fully qualified form)

#### get_premises()

- REQUIRES: `position_at_proof` has been called and the proof has been fully replayed (all steps in `original_states` are cached).
- ENSURES: Returns a `list[list[dict]]` of per-step premise annotations, computed by diffing proof terms from `original_states`. Each inner list contains `{"name": str, "kind": "lemma"}` dicts for the constants introduced at that step.
- The diffing uses `extract_constants_from_proof_term` (see §4.3) on each consecutive pair of cached proof terms.

> **Given** a proof with 3 steps where step 2 introduces `Nat.add_comm`
> **When** `get_premises()` is called
> **Then** the result is `[[], [{"name": "Nat.add_comm", "kind": "lemma"}], [...]]`

#### submit_command(command)

- REQUIRES: The coqtop process is running.
- ENSURES: Sends the command to coqtop and returns the output as a string. This captures the output of vernacular commands (Print, Check, About, Locate, Search, Compute, Eval) directly — coqtop returns command output on stdout, unlike coq-lsp which does not expose vernacular output.

> **Given** an active backend with a loaded file
> **When** `submit_command("Print nat.")` is called
> **Then** the output contains the definition of `nat`

#### shutdown()

- REQUIRES: None (may be called at any time, including on a crashed or already-shut-down backend).
- ENSURES: The coqtop process is terminated. All associated resources (file handles, pipes, memory) are released. After shutdown, no other operation may be called. Shutdown shall not raise exceptions — it always succeeds (kills the process if necessary).

> **Given** an active backend with a running coqtop process
> **When** `shutdown()` is called
> **Then** the process is terminated and resources are released

> **Given** a backend whose process has already exited (crashed)
> **When** `shutdown()` is called
> **Then** the call succeeds without error (idempotent cleanup)

### 4.2 Backend Factory

The system shall provide an async factory function:

#### create_coq_backend(file_path, watchdog_timeout=None, load_paths=None)

- REQUIRES: `file_path` is a non-empty string. `watchdog_timeout` is a positive float (seconds) or `None`. `load_paths` is an optional list of `(directory, logical_prefix)` tuples specifying recursive load path bindings (equivalent to coqtop `-R` flags).
- ENSURES: Spawns a new coqtop process with `-quiet` flag. When `load_paths` is provided, the process is started with the corresponding `-R` flags so that bare `Require Import` directives in source files resolve correctly. Returns a `CoqBackend` instance connected to that process with the given `watchdog_timeout` configured. The process is ready for `load_file` to be called.
- On process spawn failure (coqtop not installed, binary not found): raises an exception with a descriptive message.

The factory is the only way to create `CoqBackend` instances. The session manager receives it as a constructor parameter, enabling test injection of mock backends.

#### Load path configuration

Libraries installed under `user-contrib/` are automatically available for fully-qualified imports (e.g., `From Flocq.Core Require Import Zaux`). However, some libraries use bare imports (e.g., `Require Import Zaux`) that rely on recursive load path bindings set during the library's original build. These bare imports fail without the corresponding `-R` flags.

The `load_paths` parameter provides these bindings. For a library installed at `<user-contrib>/<Lib>` with module prefix `<Lib>.`, the binding is `(<user-contrib>/<Lib>, <Lib>)`. The campaign orchestrator derives this from the project path and module prefix.

> **Given** coqtop is installed and available on PATH
> **When** `create_coq_backend("/path/to/file.v")` is called
> **Then** a CoqBackend instance is returned with a running coqtop process

> **Given** coqtop is installed and a watchdog_timeout of 600
> **When** `create_coq_backend("/path/to/file.v", watchdog_timeout=600)` is called
> **Then** a CoqBackend instance is returned with watchdog_timeout=600 configured

> **Given** coqtop is installed and load_paths=[("/opt/coq/user-contrib/Flocq", "Flocq")]
> **When** `create_coq_backend("/opt/coq/user-contrib/Flocq/Core/Raux.v", load_paths=[...])` is called
> **Then** a CoqBackend instance is returned and `load_file` succeeds (bare `Require Import Zaux` resolves via the `-R` flag)

> **Given** coqtop is not installed
> **When** `create_coq_backend("/path/to/file.v")` is called
> **Then** an exception is raised indicating no Coq backend is available

### 4.3 Proof Term Diffing

#### extract_constants_from_proof_term(proof_term_text)

- REQUIRES: `proof_term_text` is a string produced by `Show Proof.`.
- ENSURES: Returns a `set[str]` of fully qualified constant names found in the proof term. Extracts names matching the pattern `@Qualified.Name` or bare `Qualified.Name` where `Qualified.Name` contains at least one dot separator. Local variables, de Bruijn indices, and `?Goal` placeholders are excluded.

> **Given** proof term text `"(fun n : nat => @Nat.add_comm n 0)"`
> **When** `extract_constants_from_proof_term` is called
> **Then** the result includes `"Nat.add_comm"` and excludes `"n"`, `"nat"`, `"fun"`

#### resolve_step_premises(step, previous_constants, current_proof_term_text)

- REQUIRES: `step` is a positive integer. `previous_constants` is the set of constants from the proof term at step-1. `current_proof_term_text` is the `Show Proof.` output at step.
- ENSURES: Returns a list of `{"name": str, "kind": "lemma"}` dicts for constants that are in the current proof term but not in `previous_constants`. This is the set of constants the tactic at step `step` introduced.

> **Given** `previous_constants = {"Nat.add_0_r"}` and current proof term containing `{"Nat.add_0_r", "Nat.add_comm"}`
> **When** `resolve_step_premises` is called
> **Then** the result is `[{"name": "Nat.add_comm", "kind": "lemma"}]`

### 4.4 ProofState Translation

The backend shall parse coqtop's `Show.` output into the `ProofState` type defined in [proof-types.md](../doc/architecture/data-models/proof-types.md).

coqtop's `Show.` output has the following structure:

```
N goal(s)

  h1[, h2, ...] : type
  h3 := body : type
  ============================
  goal_type

  ============================
  goal_type_2
```

The parser (`parse_coqtop_goals`) shall handle:
- **Header line**: `"N goal(s)"`, `"1 goal"`, or `"No more goals."` / `"No more subgoals."`
- **Hypothesis block**: Indented lines before `====...`, each with format `name[, name...] : type` or `name := body : type`
- **Multi-line hypothesis types**: Continuation lines are indented further than the name line
- **Let-bound hypotheses**: `name := body : type` — the body is stored in `Hypothesis.body`
- **Hypotheses with multiple names**: `n, m : nat` expands to two Hypothesis objects
- **Goal separator**: `====...` (4+ equals signs)
- **Multiple goals**: Subsequent goals may have their own hypothesis blocks or share the context
- **Unicode and notation**: Types may contain Unicode characters and Coq notation; they are stored verbatim

| Coq concept | ProofState field |
|-------------|-----------------|
| Proof obligation / subgoal | `Goal` object |
| Goal conclusion type | `Goal.type` (pretty-printed as a Coq expression string) |
| Local context entry (variable or assumption) | `Hypothesis` object |
| Let-binding in local context | `Hypothesis` with `body` set to the definition term |
| Focused goal (first goal in output) | `focused_goal_index = 0` |
| No remaining goals | `is_complete = true`, `goals = []` |

Goals shall be ordered by their index as coqtop presents them. Hypotheses within each goal shall be ordered as coqtop presents them in the local context (typically oldest-first).

The backend shall use Coq's pretty-printer for type and body strings. The same Coq version on the same input shall produce identical strings (determinism requirement from proof-serialization spec §4.13).

### 4.5 Premise Classification

Proof term diffing produces fully qualified constant names. All constants extracted from proof terms are classified as `kind = "lemma"` — proof term constants are always global references (lemmas, theorems, definitions used as lemmas). Local hypotheses do not appear as `@`-prefixed constants in proof terms; they appear as bound variables.

> **Given** a tactic `apply Nat.add_comm.` where `Nat.add_comm` is a global lemma
> **When** premises are extracted via proof term diffing
> **Then** the premise has `name = "Nat.add_comm"` and `kind = "lemma"`

### 4.6 Vernacular Output Capture

The `CoqBackend` provides vernacular command execution via `submit_command`. coqtop returns the output of Print, Check, About, Locate, Search, Compute, and Eval commands directly on stdout. This eliminates the coq-lsp limitation where successful vernacular queries produced no capturable output.

The session manager may use the backend's `submit_command` directly for vernacular queries instead of spawning a separate coqtop subprocess.

> **Given** a coqtop backend with a loaded file
> **When** `submit_command("Print nat.")` is called
> **Then** the output contains the definition of `nat` (e.g., `"Inductive nat : Set := O : nat | S : nat -> nat."`)

## 5. Data Model

The `CoqBackend` protocol has no persistent data model — it is a stateful process wrapper. Its inputs and outputs use the types defined in [proof-types.md](../doc/architecture/data-models/proof-types.md):

| Operation | Returns |
|-----------|---------|
| `position_at_proof` | `ProofState` |
| `execute_tactic` | `ProofState` |
| `get_proof_state` | `ProofState` |
| `get_proof_term` | `str` (proof term text) |
| `get_premises` | `list[list[dict]]` with `{"name": str, "kind": str}` entries |
| `submit_command` | `str` (command output) |

The `original_script` attribute is a `list[str]` — plain tactic strings, not a domain type.
The `original_states` attribute is a `list` of cached state records (implementation-defined), each containing parsed proof state and proof term text.

## 6. Interface Contracts

### Session Manager → CoqBackend

The session manager is the sole consumer of the `CoqBackend` protocol. The contract is defined in [proof-session.md](../doc/architecture/proof-session.md) and [specification/proof-session.md](proof-session.md) §6.

| Operation | Input | Output | Error |
|-----------|-------|--------|-------|
| `load_file(path)` | File path string | None | `FileNotFoundError`, `OSError`, or Coq check error |
| `position_at_proof(name)` | Proof name string | `ProofState` (initial state) | `ValueError`, `KeyError`, `LookupError` |
| `execute_tactic(tactic)` | Tactic string | `ProofState` (new state) | Exception with Coq error message |
| `get_proof_state()` | None | `ProofState` | None |
| `get_proof_term()` | None | `str` (proof term text) | Returns empty string on failure |
| `undo()` | None | None | Backend-dependent; may fail |
| `get_premises()` | None | `list[list[dict]]` of per-step premise annotations | Backend-dependent |
| `submit_command(cmd)` | Command string | `str` (output text) | Exception on coqtop error |
| `shutdown()` | None | None | Never raises |

Concurrency: each `CoqBackend` instance is used by exactly one session. The session manager's per-session lock ensures that operations on a single backend are serialized. No concurrent calls to the same backend instance.

### CoqBackend → Coq Process

| Property | Value |
|----------|-------|
| Transport | stdin/stdout pipes via `asyncio.subprocess` |
| Protocol | Line-buffered stdin/stdout with sentinel-based output framing |
| Direction | Bidirectional, stateful |
| Cardinality | One coqtop process per CoqBackend instance |
| Lifecycle | Process spawned by `create_coq_backend`, terminated by `shutdown` |
| Stderr | Merged with stdout via `stderr=subprocess.STDOUT` |

#### Sentinel-based output framing

coqtop does not provide explicit end-of-output markers. The backend uses a sentinel command after each real command to detect when output is complete:

1. Send the real command (e.g., `intros n.`).
2. Send a sentinel: `Check __POULE_SENTINEL__.`
3. Read stdout until the sentinel's known error message appears (`Error: The reference __POULE_SENTINEL__ was not found`).
4. Everything before the sentinel error is the real command's output.

This mechanism is proven in the existing `ProofTermResolver` implementation.

#### Stderr handling

The coqtop subprocess stderr shall be merged with stdout via `stderr=subprocess.STDOUT`. This ensures all output — including warnings and error messages — appears on a single stream, preventing pipe buffer deadlocks. The sentinel framing mechanism works on the merged stream.

#### Prompt stripping

coqtop prefixes output lines with prompts (e.g., `Coq < `, `Name < `). The backend shall strip these prompts from all output before parsing. The prompt regex strips patterns matching `^[A-Za-z_]+ < ` from each line.

## 7. State and Lifecycle

### 7.1 Backend State Machine

| Current State | Event | Guard | Action | Next State |
|--------------|-------|-------|--------|------------|
| — | `create_coq_backend` | coqtop binary available | Spawn process | `spawned` |
| — | `create_coq_backend` | coqtop binary not found | Raise exception | — |
| `spawned` | `load_file` | File exists, Coq accepts prelude | Send prelude to process | `file_loaded` |
| `spawned` | `load_file` | File error | Raise exception | `spawned` |
| `file_loaded` | `position_at_proof` | Proof found | Send theorem + Proof, parse Show, cache states | `proof_active` |
| `file_loaded` | `position_at_proof` | Proof not found | Raise exception | `file_loaded` |
| `proof_active` | `execute_tactic` | Tactic succeeds | Apply tactic, parse Show | `proof_active` |
| `proof_active` | `execute_tactic` | Tactic fails | Raise exception, state unchanged | `proof_active` |
| `proof_active` | `execute_tactic` | Tactic closes all goals | Apply tactic, parse Show | `proof_complete` |
| `proof_active` | `undo` | Has previous state | Send Undo. | `proof_active` |
| `proof_active` | `get_premises` | States cached | Diff proof terms, return | `proof_active` |
| `proof_active` | `submit_command` | — | Send command, return output | `proof_active` |
| `proof_complete` | `undo` | Has previous state | Send Undo. | `proof_active` |
| `proof_complete` | `get_premises` | States cached | Diff proof terms, return | `proof_complete` |
| `proof_complete` | `submit_command` | — | Send command, return output | `proof_complete` |
| Any | `shutdown` | — | Kill process, release resources | `shut_down` (terminal) |
| Any | Process exits unexpectedly | — | Mark as crashed | `crashed` (terminal) |
| `crashed` | `shutdown` | — | No-op (process already gone) | `shut_down` (terminal) |
| `crashed` | Any other operation | — | Raise exception | `crashed` |

### 7.2 Process Lifecycle

1. **Spawn**: `create_coq_backend` starts coqtop with `-quiet` and optional `-R` flags.
2. **Use**: The session manager calls `load_file`, `position_at_proof`, then any combination of `execute_tactic`, `undo`, `get_proof_state`, `get_proof_term`, `get_premises`, and `submit_command`.
3. **Shutdown**: `shutdown` sends a termination signal and waits for the process to exit. If the process does not exit within a timeout (implementation-defined, recommended 5 seconds), it is forcefully killed (`SIGKILL`).

### 7.3 Crash Detection

The backend shall monitor its coqtop process. If the process exits unexpectedly (exit code != 0, or signal-terminated):

1. The backend transitions to `crashed` state.
2. Any subsequent operation (except `shutdown`) raises an exception.
3. `shutdown` on a crashed backend is a no-op that succeeds.

The session manager detects the crash when it next calls a backend operation, and marks the session as `BACKEND_CRASHED`.

### 7.4 Liveness Watchdog

When `watchdog_timeout` is configured (non-null), the backend shall wrap each I/O read with a per-read inactivity timeout. If `watchdog_timeout` seconds elapse with no data received on the backend's stdout pipe, the read shall be cancelled and a `ConnectionError` raised with the message `"coqtop unresponsive for {watchdog_timeout}s"`.

The watchdog timer resets on every successful data read. A tactic that takes several minutes to compute but then produces a response is not affected — the watchdog only fires during complete silence on the pipe.

When `watchdog_timeout` is `None`, reads block indefinitely (the default for interactive MCP sessions where the user controls timing).

> **Given** a backend with `watchdog_timeout=600` and a coqtop process that has stopped producing output
> **When** 600 seconds of inactivity pass during a read
> **Then** a `ConnectionError` is raised with message containing "unresponsive"

> **Given** a backend with `watchdog_timeout=None`
> **When** the coqtop process stops producing output
> **Then** the read blocks indefinitely (no watchdog)

## 8. Error Specification

### Error types

| Condition | Exception | Category |
|-----------|-----------|----------|
| File does not exist or is unreadable | `FileNotFoundError` / `OSError` | Input error |
| File has Coq syntax or dependency errors | Exception with Coq error message | Dependency error |
| Proof name not found in loaded file | `ValueError` / `KeyError` / `LookupError` | Input error |
| Tactic rejected by Coq | Exception with Coq error message | Dependency error |
| Undo fails | Exception | Dependency error |
| coqtop not found on PATH | `FileNotFoundError` / `OSError` | Dependency error |
| coqtop process crashes during operation | Exception (detected by EOF on pipe or nonzero exit) | Dependency error |
| coqtop process unresponsive (watchdog) | `ConnectionError` (detected by inactivity timeout on pipe) | Dependency error |
| Operation called after shutdown | Undefined behavior (caller's obligation to not call) | Invariant violation |

### Edge cases

| Condition | Behavior |
|-----------|----------|
| `load_file` called twice on same backend | Undefined. Session manager calls it exactly once. |
| `position_at_proof` called twice | Backend sends `Abort.` to exit current proof, then enters the new proof. |
| `execute_tactic` on a completed proof (no goals) | Forwards to Coq; Coq returns an error ("No focused proof") |
| `undo` at step 0 (before any tactic) | Coqtop returns an error. Session manager guards against this. |
| `get_premises` before full replay | Returns premises for the replayed prefix only. |
| `shutdown` called multiple times | Idempotent; second call is a no-op |
| Process killed by OS (OOM, SIGKILL) | Detected as crash; backend enters `crashed` state |
| Very large `.v` file (> 10K lines) | No specific limit; bounded by coqtop process memory. |

## 9. Non-Functional Requirements

- Process spawn time (factory call to ready state): < 2 seconds on a system with Coq installed (coqtop is lighter than coq-lsp).
- Tactic execution overhead (backend wrapper, excluding Coq execution time): < 5 ms per tactic.
- Shutdown shall complete within 10 seconds (5s graceful + 5s forced kill).
- Memory: each backend process consumes memory proportional to the Coq environment loaded. Typical: 30–150 MB per process for standard library proofs (lower than coq-lsp due to no LSP overhead).

## 10. Examples

### Full lifecycle

```
backend = await create_coq_backend("/path/to/arith.v")
await backend.load_file("/path/to/arith.v")
initial_state = await backend.position_at_proof("add_comm")
# initial_state.goals[0].type ≈ "forall n m, n + m = m + n"
# backend.original_script = ["intros n m.", "ring."]
# backend.original_states has 3 entries (initial + 2 tactics)

state1 = await backend.execute_tactic("intros n m.")
# state1.goals[0].type ≈ "n + m = m + n"
# state1.goals[0].hypotheses = [Hypothesis("n", "nat"), Hypothesis("m", "nat")]

state2 = await backend.execute_tactic("ring.")
# state2.is_complete = True, state2.goals = []

premises = await backend.get_premises()
# premises[1] = [{"name": "Coq.setoid_ring.Ring_theory.ring_theory", "kind": "lemma"}]

output = await backend.submit_command("Print nat.")
# output contains "Inductive nat : Set := O : nat | S : nat -> nat."

await backend.shutdown()
# Process terminated, resources released
```

### Error recovery

```
backend = await create_coq_backend("/path/to/file.v")
await backend.load_file("/path/to/file.v")
await backend.position_at_proof("my_proof")

try:
    await backend.execute_tactic("bad_tactic.")
except Exception as e:
    # e contains Coq error message
    # Backend state unchanged — can continue with a valid tactic
    state = await backend.execute_tactic("intros.")

await backend.shutdown()
```

## 11. Language-Specific Notes (Python)

- Define `CoqBackend` as a `typing.Protocol` class with async methods.
- Use `asyncio.create_subprocess_exec` for process spawning, with `stderr=asyncio.subprocess.STDOUT`.
- Use `asyncio.StreamReader` / `asyncio.StreamWriter` for stdin/stdout pipe communication.
- Reuse the sentinel-based output framing from `ProofTermResolver` in `premise_resolution.py`.
- Reuse `extract_constants_from_proof_term` and `resolve_step_premises` from `premise_resolution.py`.
- Package location: `src/Poule/session/backend.py` (replaces the existing coq-lsp implementation).
- New modules: `src/Poule/session/coqtop_parser.py` (goal state parser), `src/Poule/extraction/tactic_splitter.py` (sentence splitter).

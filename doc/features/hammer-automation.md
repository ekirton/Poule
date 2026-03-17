# Hammer Automation

CoqHammer is one of the most effective automated proving tools in the Coq ecosystem, but it remains underused because it requires plugin knowledge, tactic syntax familiarity, and the ability to interpret opaque failure output. Hammer Automation wraps CoqHammer's tactics (`hammer`, `sauto`, `qauto`) so that Claude can invoke them on behalf of the user during active proof sessions. The user experience shifts from "read the CoqHammer docs and figure out the right tactic" to "try to prove this automatically."

**Stories**: [Epic 1: Hammer Invocation](../requirements/stories/hammer-automation.md#epic-1-hammer-invocation), [Epic 2: Result Handling](../requirements/stories/hammer-automation.md#epic-2-result-handling), [Epic 3: Configuration](../requirements/stories/hammer-automation.md#epic-3-configuration), [Epic 4: Multi-Strategy Automation](../requirements/stories/hammer-automation.md#epic-4-multi-strategy-automation)

---

## Problem

Claude Code with the Proof Interaction Protocol can already submit individual tactics to Coq and reason about the results conversationally. But when a user wants to discharge a goal automatically, Claude must guess which tactic to try, wait for the result, and iterate — essentially performing manual proof search one tactic at a time. The user, meanwhile, would need to know that CoqHammer exists, which of its three tactics to try, what options to pass, and how to interpret its failure output. Newcomers rarely get this far; experienced users waste time on mechanical invocations they could skip.

What's missing is the ability for Claude to say "let me try automated proving" and have CoqHammer's full power applied to the current goal — with the right tactic chosen automatically, timeouts managed, and results reported in terms the user can act on.

## Solution

Hammer automation lets Claude invoke CoqHammer tactics within an active proof session through the existing proof interaction tools. When the user asks Claude to try proving a goal automatically, Claude submits hammer tactics to Coq and reports the outcome: either a verified proof script ready to insert, or a clear explanation of why automation did not succeed and what to try next.

### Multi-Strategy Fallback

The user should not need to know whether `hammer`, `sauto`, or `qauto` is the right tactic for their goal. When Claude invokes hammer automation without a specific tactic, the system tries multiple strategies in sequence — starting with the most powerful (`hammer`, which uses external ATP solvers) and falling back to lighter-weight alternatives (`sauto`, `qauto`). The first strategy that succeeds ends the sequence immediately. If all strategies fail, the user gets diagnostics from each attempt rather than a single opaque failure.

Users who do know which tactic they want can still request a specific one. Lemma hints can be supplied when the user or Claude has context about which lemmas might be relevant, guiding CoqHammer toward proofs it might not find on its own.

### Timeout Handling

Hammer tactics — especially `hammer` with external ATP solvers — can be slow. Every invocation respects a configurable timeout with a sensible default. When a multi-strategy sequence is running, the timeout governs the total time budget: if `hammer` exhausts most of the budget, the remaining strategies get whatever time is left rather than restarting the clock. When a timeout is reached, the result reports that the timeout was hit and what value was used, so the user can decide whether to retry with a larger budget.

### Result Reporting

When a hammer tactic succeeds, the result is a verified proof script — a sequence of Coq-native tactics that closes the goal. The user can insert this script directly into their development with confidence that it will be accepted by Coq. When `hammer` succeeds via ATP reconstruction, both the high-level ATP proof and the low-level reconstructed tactic script are available, so the user can choose which form to keep.

When a hammer tactic fails, the result includes structured diagnostics: why it failed (timeout, no proof found, reconstruction failure), any partial progress (e.g., the ATP solver found a proof but Coq reconstruction failed), and enough context for Claude to explain the failure and suggest alternatives.

## Scope

Hammer automation provides:

- Invocation of `hammer`, `sauto`, and `qauto` in active proof sessions
- Multi-strategy fallback when the user does not specify a tactic
- Configurable timeouts and tactic options
- Verified proof scripts on success, structured diagnostics on failure
- Lemma hint passthrough to guide premise selection

Hammer automation does not provide:

- Installation or management of CoqHammer or its ATP solver dependencies — these must be pre-installed in the user's Coq environment
- Proof search beyond what CoqHammer offers (see [Proof Search](proof-search.md) for tree-search-based exploration)
- Modifications to CoqHammer itself
- Statistics collection or success rate tracking across proof developments

---

## Design Rationale

### Why expose as a mode of existing tools

Poule already exposes 22 MCP tools, and research indicates that LLM accuracy degrades past 20-30 tools. Adding new top-level tools for each hammer variant would push past this budget. Exposing hammer automation as a mode of the existing proof interaction tools keeps the tool count stable while expanding capability. From Claude's perspective, invoking hammer is just another way to use a tool it already knows.

### Why try multiple strategies

CoqHammer's three tactics cover different points in the power-speed tradeoff. `hammer` is the most powerful (it invokes external ATP solvers and reconstructs proofs) but also the slowest. `sauto` provides strong automation without external solvers. `qauto` is the fastest but handles fewer goals. No single tactic dominates — the right choice depends on the goal structure, and users should not need to make that choice themselves. Trying strategies in sequence from most powerful to least powerful maximizes the chance of success while letting the user specify a single intent: "prove this automatically."

### Why CoqHammer is the right foundation

CoqHammer is the most mature automated proving tool in the Coq ecosystem. It combines premise selection with external ATP solvers (E, Vampire, Z3) and proof reconstruction, covering a large fraction of first-order goals. Its `sauto` and `qauto` tactics complement the main `hammer` tactic by handling goals that do not require external ATPs. The tool is actively maintained and battle-tested across major formalization projects. Rather than building new automation from scratch, wrapping CoqHammer gives users access to years of engineering and research through a natural language interface.

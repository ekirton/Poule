# Vernacular Introspection

A single MCP tool that gives Claude direct access to Coq's built-in vernacular introspection commands -- Print, Check, About, Locate, Search, Compute, and Eval -- so it can inspect types, unfold definitions, evaluate expressions, and locate names without the user acting as a relay between Claude Code and a Coq toplevel.

**Stories**: [Vernacular Introspection](../requirements/stories/vernacular-introspection.md)

---

## Problem

Coq developers working with Claude Code today hit a wall every time they need to know what a definition expands to, what type a term has, or where a name lives. Claude cannot answer these questions from its training data alone -- Coq libraries evolve, user projects define their own constants, and proof contexts introduce local hypotheses that no static knowledge base covers. The only option is for the user to switch to a Coq toplevel (CoqIDE, Proof General, coq-lsp), run the command, copy the output, and paste it back into the conversation. This context-switching is slow, error-prone, and especially painful when Claude needs to chain several queries to build understanding -- for example, locating a name, printing its definition, and then checking the type of a subterm.

The Lean ecosystem avoids this problem because its language server exposes type and definition information programmatically, and tools like LeanDojo provide direct access to term evaluation. Coq has no equivalent path from an AI assistant to its introspection commands.

## Solution

The MCP server exposes a single `coq_query` tool that accepts a `command` parameter selecting which vernacular command to execute. The user (or Claude on the user's behalf) provides the command name and its arguments; the tool executes the command against the current Coq environment and returns the result.

### Definition inspection

The `Print` command shows the full body of a named constant, inductive type, or fixpoint -- the same output a developer would see in a Coq toplevel. This is the primary way to understand what a definition actually contains, as opposed to just its type signature. An optional `assumptions` variant lists the axioms a definition transitively depends on, which matters when assessing the trustworthiness of a proof.

### Type checking

The `Check` command shows the type of a term or expression. This covers both simple lookups ("what is the type of `Nat.add`?") and on-the-fly type inference for compound expressions ("what is the type of `fun n => n + 1`?"). When a proof session is active, `Check` resolves terms against the local proof context, so Claude can reason about hypotheses and let-bindings without the user having to spell them out.

### Name resolution

The `About` command retrieves metadata for a name: its kind (theorem, definition, inductive, constructor), defining module, and opacity status. The `Locate` command resolves short or partial names to fully qualified paths, disambiguating when multiple matches exist, and can also look up notation definitions. The `Search` command finds names matching a type pattern or constraint, which is how Claude discovers relevant lemmas when it does not know the exact name. Search results are truncated at a reasonable limit with an indication when truncation occurs, so large result sets do not overwhelm the conversation.

### Expression evaluation

The `Compute` command evaluates a term to its normal form -- full reduction. The `Eval` command does the same but under a specified reduction strategy (cbv, lazy, cbn, simpl, hnf, unfold), giving control over how far a term is reduced. Both commands work inside proof sessions, where they can reference local hypotheses and let-bindings. This lets Claude show a user what an expression actually computes to, or inspect an intermediate reduction form to understand why a tactic does or does not make progress.

## Design Rationale

### Why one tool, not seven

The [MCP Tool Surface](mcp-tool-surface.md) feature already occupies a significant share of the tool count budget. Each tool schema consumes context window tokens and adds cognitive load to tool selection. Because the seven vernacular commands share a common shape -- a command name and a textual argument, returning textual output -- bundling them under a single `coq_query` tool with a `command` parameter avoids inflating the tool count without sacrificing expressiveness. This is the opposite tradeoff from the search tools, where each tool has a distinct parameter shape and benefits from a semantic name.

### Why these commands

Print, Check, About, Locate, Search, Compute, and Eval are the vernacular commands Coq developers use daily for interactive exploration. They are read-only -- they inspect the environment without modifying it -- which keeps the tool safe to call at any time. Commands that modify state (Definition, Require, tactic execution) are out of scope; proof interaction is covered separately by the Proof Interaction Protocol.

### Session-aware, not session-free

Introspection commands run against whatever Coq environment the MCP server currently manages: loaded files, imported modules, and any active proof session. When a proof is in progress, commands automatically see local hypotheses and let-bindings. This means the user does not need to tell Claude "I'm in a proof" or re-state their context -- the tool picks it up from the session. The tradeoff is that results depend on session state, so the same query can return different results at different points in a development. This matches how Coq itself works and avoids the complexity of maintaining a separate stateless query endpoint.

# Formalization Assistance

The gap between mathematical intuition and formal proof is the single largest barrier to Coq adoption. Users know what they want to prove — they can state it on a whiteboard or in a textbook — but translating that understanding into Coq's type theory requires navigating unfamiliar syntax, locating the right library lemmas, and managing an interactive proof session where each step depends on the evolving proof state. Formalization Assistance is a `/formalize` slash command that guides the user through the entire journey from a natural language description of a theorem to a completed, type-checked Coq proof, turning what is normally a multi-hour struggle into a single guided dialogue.

**Stories**: [Epic 1: Natural Language Input and Statement Suggestion](../requirements/stories/formalization-assistance.md#epic-1-natural-language-input-and-statement-suggestion), [Epic 2: Lemma Search and Discovery](../requirements/stories/formalization-assistance.md#epic-2-lemma-search-and-discovery), [Epic 3: Interactive Proof Building](../requirements/stories/formalization-assistance.md#epic-3-interactive-proof-building), [Epic 4: Partial and Alternative Formalizations](../requirements/stories/formalization-assistance.md#epic-4-partial-and-alternative-formalizations)

---

## Problem

Formalizing a mathematical result in Coq today requires three distinct skills that are rarely found together: understanding the mathematics well enough to state the result precisely, knowing Coq's type theory and library landscape well enough to express that statement formally, and navigating the interactive proof process to build a proof term. Each skill is individually demanding. Together, they make formalization inaccessible to most mathematicians and students, and tedious even for experienced Coq developers.

Existing tools address fragments of the problem but never the whole thing. Coq's `Search` and `SearchPattern` commands can find lemmas, but only if the user already knows the right query syntax and can sift through unranked results. CoqHammer can discharge goals, but only after the user has stated the theorem and opened a proof session. No existing tool accepts a natural language description and helps the user arrive at a well-typed formal statement. The critical first step — getting from "I want to prove that every continuous function on a compact set is bounded" to a valid Coq `Theorem` declaration with the right types, quantifiers, and imports — has no tool support at all.

The result is that users who know exactly what they want to prove still cannot get started. The formalization process feels like translating between two foreign languages at once, and most people give up before they produce a single well-typed statement.

## Solution

Formalization Assistance provides a `/formalize` command that accepts a natural language description of a theorem and walks the user through the complete formalization process in a single conversational session.

### From Natural Language to Formal Statement

The user describes what they want to prove in plain English or mathematical prose. Claude interprets the mathematical intent, identifies the relevant Coq types and propositions, and produces a candidate formal statement. Before presenting it, Claude checks the statement against the active Coq environment to ensure it is syntactically valid and well-typed. The user never sees a suggestion that Coq would reject.

When the description is ambiguous or underspecified, Claude asks clarifying questions rather than guessing. When the user has only a partial description — "associativity of append for lists" rather than a fully elaborated theorem — Claude infers the missing pieces from context and explains what was inferred so the user can confirm or correct.

### Lemma Discovery

Before suggesting a formal statement, Claude searches the loaded libraries and the current project for existing lemmas relevant to the user's described theorem. Each result comes with an explanation of why it is relevant: whether it already states the user's theorem, generalizes it, or would be useful as a building block in the proof. If the theorem has already been formalized, the user learns this immediately rather than re-deriving a known result.

The search also identifies which libraries and imports are needed, so the user does not have to track down dependencies manually.

### Interactive Proof Building

Once the user accepts a formal statement, Claude opens a proof session and helps build the proof interactively. At each step, Claude suggests tactics informed by both the current proof state and the user's original mathematical description of the theorem. Suggestions come with explanations of what each tactic does and why it is appropriate — the user learns proof technique alongside the specific proof.

For routine goals, Claude attempts automated strategies first so that mechanical subgoals are discharged without the user's intervention. When a proof step fails, Claude explains the failure in terms of the mathematical content rather than presenting a raw Coq error message, and suggests alternative approaches.

### Iterative Refinement

The suggested formal statement will not always match the user's intent on the first try. When it does not, the user describes the needed correction in natural language and Claude produces a revised statement, maintaining context across multiple rounds of feedback. Every revision is type-checked before it is presented. The conversation converges on the correct formalization without the user needing to edit Coq syntax directly.

## Scope

Formalization Assistance provides:

- A `/formalize` slash command that orchestrates the formalization workflow as a guided dialogue
- Natural language input for describing theorems, lemmas, and definitions
- Search for existing relevant lemmas with explanations of relevance
- Candidate formal Coq statements that are type-checked before being presented
- Iterative refinement of the formal statement through natural language feedback
- Interactive proof building with tactic suggestions grounded in the mathematical intent
- Automated proving attempts on goals amenable to existing automation
- Import and dependency suggestions based on the libraries where relevant lemmas were found
- Explanations of proof failures in mathematical terms

Formalization Assistance does not provide:

- Batch formalization of entire papers or textbooks — each session focuses on a single theorem
- Formal verification that the natural language description and the formal statement are semantically equivalent — the user is the arbiter of correctness
- New Coq tactics or automation procedures — it composes existing tools
- Proof visualization (see [Proof Visualization Widgets](proof-visualization-widgets.md))
- Training or fine-tuning of ML models for formalization tasks

---

## Design Rationale

### Why a slash command rather than a new tool

The formalization workflow is inherently multi-step and conversational: interpret the user's intent, search for relevant results, propose a statement, refine it, then build the proof. No single tool invocation can capture this sequence. A slash command lets Claude orchestrate multiple existing tools — lemma search, vernacular introspection, proof interaction, hammer automation — in a guided dialogue that adapts to the user's responses at each stage. The tools provide the primitives; the slash command provides the script that ties them together into a coherent experience.

### Why search before suggesting a statement

Searching for existing lemmas before generating a candidate statement serves two purposes. First, it prevents the user from re-formalizing a result that already exists in their loaded libraries. Second, the search results give Claude better context for constructing the formal statement — knowing what types, naming conventions, and proof patterns the relevant libraries use leads to suggestions that integrate naturally with the user's development rather than standing apart from it.

### Why type-check before presenting

A formal statement that Coq rejects is worse than no suggestion at all: it wastes the user's time and erodes trust. By checking every candidate statement against the active Coq environment before presenting it, the workflow guarantees that the user's first interaction with the formal statement is productive — they evaluate whether it captures their intent, not whether it compiles. This is especially important for newcomers who cannot easily diagnose type errors on their own.

### Why explain in mathematical terms

The target audience includes mathematicians, students, and developers who think in mathematical concepts rather than Coq internals. When a tactic fails because of a universe inconsistency or a missing coercion, the raw Coq error message is opaque to most users. Translating errors and proof steps into the language of the user's original description keeps the conversation grounded in the domain the user understands. The user learns what went wrong mathematically, not just syntactically, and can adjust their approach accordingly.

### Why support partial descriptions

Mathematicians rarely state theorems in full formal detail in conversation. They say "associativity of append" and expect the listener to fill in the quantifiers, types, and variable names. Requiring a complete and precise natural language description before Claude can help would impose a formality burden that defeats the purpose of the tool. By accepting partial descriptions and inferring the rest from context — the current file, loaded libraries, naming conventions — the workflow meets users where they are and makes the first interaction as low-friction as possible.

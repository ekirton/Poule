# Proof Explanation and Teaching

Coq proofs are opaque by nature: a proof script is a sequence of tactic invocations that transform an invisible proof state, and the reader must mentally simulate each step to understand why the proof works. Proof Explanation and Teaching provides an `/explain-proof` slash command that walks through a completed proof tactic by tactic, explains each step in plain English, shows how the proof state evolves, and connects the formal manipulation to the underlying mathematical intuition. The result is a readable, pedagogically useful narrative that transforms "I can see it compiles, but I don't understand why it works" into genuine understanding.

**Stories**: [Epic 1: Step-by-Step Proof Explanation](../requirements/stories/proof-explanation.md#epic-1-step-by-step-proof-explanation), [Epic 2: Mathematical Intuition](../requirements/stories/proof-explanation.md#epic-2-mathematical-intuition), [Epic 3: Adjustable Detail Level](../requirements/stories/proof-explanation.md#epic-3-adjustable-detail-level), [Epic 4: Proof Summary and Structure](../requirements/stories/proof-explanation.md#epic-4-proof-summary-and-structure)

---

## Problem

Today, understanding a Coq proof requires the very skills that newcomers have not yet developed. The user must know what each tactic does in general, infer what it accomplishes in the specific proof context, and mentally track how goals and hypotheses change at every step. Existing tools — CoqIDE, Proof General, Alectryon — can display the raw proof state at each point, but they offer no explanation. The user sees that `intros n IHn` was applied and that the goal changed, but nothing tells them *why* that tactic was chosen or how it relates to the mathematical argument being formalized.

This creates a steep learning curve for students, a tedious annotation burden for educators, and a comprehension barrier for developers reviewing unfamiliar proofs. The gap is not in proof state visibility — it is in the explanation layer that connects formal tactic applications to human-understandable reasoning. Filling that gap requires contextual interpretation of both the tactic and the proof state, which is exactly what an LLM excels at.

## Solution

The `/explain-proof` command takes a theorem or lemma name, steps through its proof, and produces a natural-language walkthrough that explains each tactic in context.

### Tactic-by-Tactic Explanation

For every tactic in the proof, the user sees what the tactic does in general ("intros moves hypotheses from the goal into the context"), what it accomplished in this specific proof ("this introduced the variable n and the induction hypothesis IHn"), and how the proof state changed as a result. Compound tactics — semicolons, `try`, `repeat` — are explained as composite operations so the user understands the combined effect rather than being confused by unfamiliar syntax.

### Proof State Evolution

Each step displays the goals and hypotheses before and after the tactic fires. New hypotheses are identified, changes to the goal are made evident, and goal creation or discharge is noted. The user can observe the proof state transforming step by step, building the same intuition that experienced Coq developers have internalized through years of practice.

### Mathematical Intuition

Beyond explaining what a tactic does mechanically, the command connects each step to the mathematical reasoning it implements. An induction tactic is not just "splitting the goal into subgoals" — it is applying the principle of mathematical induction on a specific variable, creating a base case and an inductive step with a named induction hypothesis. A rewrite is not just "substituting in the goal" — it is applying a known mathematical fact to transform one expression into an equivalent one. This bridges the gap between the formal proof and the informal mathematical argument that motivates it.

### Adjustable Detail Level

Different audiences need different levels of detail. A student working through a proof for the first time benefits from verbose explanations with full mathematical context and pedagogical notes. An experienced developer skimming an unfamiliar proof needs only a brief summary — one line per tactic — to understand the overall structure. The command supports multiple detail levels so the same proof can be explained at the depth that matches the reader.

### Proof Summary

After walking through every step, the command provides a high-level summary of the overall proof strategy: the approach taken (e.g., induction followed by rewriting), the key lemmas used, and any recognizable proof patterns employed. This helps the user see the forest after examining each tree, consolidating their step-by-step understanding into a coherent picture of the argument.

## Scope

Proof Explanation and Teaching provides:

- A `/explain-proof` slash command that walks through any completed Coq proof
- Natural-language explanation of each tactic, both in general and in context
- Proof state display (goals and hypotheses) before and after each step
- Mathematical intuition connecting tactics to the proof strategies they implement
- Explanation of automation tactics (`auto`, `omega`, `lia`) describing what they found and why they succeeded
- Adjustable detail levels from brief one-line summaries to verbose pedagogical walkthroughs
- A summary of overall proof strategy, key lemmas, and proof patterns after the walkthrough
- Export of the explanation as a structured document suitable for course materials

Proof Explanation and Teaching does not provide:

- Proof generation, repair, or search — it explains existing proofs, not write new ones
- Interactive tutoring with exercises, quizzes, or feedback loops
- Video or animated proof visualization
- Installation or management of Coq
- Modifications to Coq's proof engine or tactic language
- Translation of proofs between proof assistants

---

## Design Rationale

### Why a slash command rather than a tool

Explaining a proof is inherently a multi-step workflow: locate the theorem, step through its tactics one at a time, inspect the proof state at each point, and weave the results into a coherent narrative. This requires orchestration — the LLM must reason between each step about what to explain and how to frame it. A single MCP tool call cannot capture this kind of iterative, judgment-intensive process. A slash command lets Claude drive the workflow end to end, composing lower-level proof interaction tools as building blocks while applying its own reasoning to produce the explanation.

### Why this is a natural fit for an LLM

The raw information needed to explain a proof — the tactic name, the proof state before, the proof state after — is already available through proof interaction tools. What is missing is the interpretation: translating a formal state change into a sentence that a student can understand, connecting a tactic application to a mathematical concept, choosing the right level of detail for the audience. This is contextual language generation grounded in structured data, which is precisely where LLMs provide the most value. No static tool or template system can produce the same quality of contextual, adaptive explanation.

### Why adjustable detail matters

A single explanation style cannot serve all audiences. Newcomers need every step spelled out with mathematical context; experienced developers find that level of detail tedious and slow. Educators want verbose output they can edit into teaching materials; reviewers want brief output they can scan in seconds. Rather than choosing one audience and optimizing for it, adjustable detail levels let the same command serve the full spectrum of users. The default provides a balanced explanation suitable for most learners, while brief and verbose modes handle the ends of the spectrum.

### Why summarize at the end

Step-by-step explanations are valuable for understanding individual tactics, but they can obscure the overall proof strategy. A student who has just read through fifteen tactic explanations may understand each step but still not grasp the high-level argument. The closing summary addresses this by naming the proof strategy, listing the key lemmas, and identifying recognizable patterns — giving the user a mental framework to organize everything they just learned.

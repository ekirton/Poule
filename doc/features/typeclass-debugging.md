# Typeclass Debugging

Typeclass debugging gives Claude the ability to inspect registered instances, trace the resolution engine's search process, and explain — in plain language — why resolution succeeded, failed, or chose one instance over another. A Coq developer encountering a typeclass error asks Claude what went wrong; Claude runs the appropriate debugging commands, interprets the output, and returns a clear explanation without the developer ever needing to know which Coq vernacular to invoke.

**Stories:** [Epic 1: Instance Inspection](../requirements/stories/typeclass-debugging.md#epic-1-instance-inspection), [Epic 2: Resolution Tracing](../requirements/stories/typeclass-debugging.md#epic-2-resolution-tracing), [Epic 3: Instance Conflict Detection](../requirements/stories/typeclass-debugging.md#epic-3-instance-conflict-detection)

---

## Problem

Typeclass resolution failures produce cryptic error messages. Coq tells the user that resolution failed but says almost nothing about why — which instances were tried, which came close to matching, or what the resolution engine was searching for. Users waste significant time on what should be a straightforward diagnostic task.

The debugging tools exist. `Set Typeclasses Debug` produces a resolution trace; `Print Instances` lists registered instances; `Print Typeclasses` enumerates known typeclasses. But these tools are hard to discover, their output is unstructured and verbose, and interpreting that output requires expert knowledge of how the resolution engine works. A newcomer encountering their first typeclass error has no realistic path from the error message to the root cause. Even experienced Coq developers routinely spend tens of minutes manually parsing indentation levels in debug traces to reconstruct the resolution search tree.

No existing tool — IDE, CLI, or otherwise — interprets this debug output or explains it. The information is there; it is just inaccessible.

## Solution

Claude acts as an interpreter between the user and Coq's typeclass debugging commands. The user describes the problem in natural language; Claude invokes the right commands, reads their output, and returns a structured explanation. Four capabilities compose the feature.

### Instance Listing

Given a typeclass name, Claude lists every registered instance: the instance name, its type signature, and the module where it is defined. This is the starting point for most debugging sessions — the user needs to see what instances exist before reasoning about why one was or was not selected. When no instances exist for a typeclass, Claude says so explicitly rather than returning an empty result that the user must interpret. When the name does not refer to a typeclass, Claude reports that clearly rather than producing a confusing Coq error.

Claude can also list all registered typeclasses in the current environment with summary information — how many instances each has, whether default instances are present — giving library authors an overview of the typeclass landscape they are working within.

### Resolution Tracing

When the user has a proof state where typeclass resolution is failing (or succeeding unexpectedly), Claude traces the resolution process for that goal. The trace shows which instances were tried, in what order, and whether each succeeded or failed. Rather than dumping the raw output of `Set Typeclasses Debug`, Claude parses the trace into a structured account: each step identifies the instance, the goal it was applied to, and the outcome.

For complex resolutions, Claude can present the full search tree — branching points where multiple instances were candidates, the engine's choice at each branch, and the reasons alternatives were rejected. The user sees the resolution logic laid out clearly instead of reverse-engineering it from indentation levels in a log.

### Failure Explanation

When resolution fails, Claude identifies and explains the root cause. There are three common failure modes, and each gets a different explanation:

- **No matching instance.** Claude identifies the specific typeclass and type arguments that lack an instance, and names what is missing.
- **Unification failure.** Claude identifies the instance that came closest to matching and explains which type arguments failed to unify and why.
- **Resolution depth exceeded.** Claude recognizes the depth limit error, shows the resolution path that led to the loop or deep chain, and explains the cycle.

The user gets a diagnosis, not a stack trace.

### Conflict Detection

When two or more instances match the same goal, the resolution engine picks one based on declaration order, priority hints, or specificity — but the user often has no idea this happened. Claude identifies these ambiguous cases: which instances match, which one wins, and on what basis. This is especially valuable for library authors adding new instances who need to know whether their instance will shadow an existing one or be shadowed by it.

Given a specific instance and a goal, Claude can also explain why that particular instance was or was not selected — the unification details, prerequisite constraints, and priority ordering that determined the outcome.

## Design Rationale

### Why typeclass debugging is a top pain point

Typeclass resolution failures are consistently cited as one of the most frustrating aspects of working with Coq. The errors are opaque by default, the debugging tools require expert knowledge to use, and the output is voluminous and unstructured. Unlike proof failures — where the user at least sees a clear goal and can reason about tactics — typeclass errors offer almost no foothold. Users are left guessing, and guessing in a system with complex instance hierarchies is slow and error-prone.

### Why LLM interpretation of debug traces is the key value add

The underlying Coq commands are mature and reliable. The problem is not that the information is unavailable — it is that the information is presented in a form that requires significant expertise to interpret. An LLM that can read a verbose, deeply nested resolution trace and produce a two-sentence explanation of what went wrong provides exactly the translation layer that is missing. The development cost is low because no new Coq functionality is required; the value comes entirely from making existing output accessible through natural language. This is one of the highest-leverage applications of an LLM-powered tool: the machine does the tedious parsing and pattern-matching; the user gets the insight.

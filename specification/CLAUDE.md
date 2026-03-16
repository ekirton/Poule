# Specification Writing Guidelines

## Authority

Specifications are derived from architecture documents (`doc/architecture/`).

**Before writing or editing:**

1. Read the parent architecture document.
2. Read `doc/architecture/data-models/expression-tree.md` and `doc/architecture/data-models/index-entities.md` — authoritative for all entity names, field types, constraints, node labels, and relationships.
3. Read `doc/architecture/component-boundaries.md` for boundary contracts.
4. Architecture wins over specification. Data model wins over architecture on entity structure.

**Cross-spec consistency:** verify referenced types, labels, and contracts against the defining specification.

## Upstream Authority Is Immutable

Do not modify `doc/architecture/` or `doc/architecture/data-models/` when writing specs. File feedback in `doc/architecture/feedback/` per `doc/architecture/feedback/CLAUDE.md`.

## Document Structure

```
1. Purpose                  [required]
2. Scope                    [required]
3. Definitions              [if domain terms used]
4. Behavioral Requirements  [required]
5. Data Model               [if component owns/transforms data]
6. Interface Contracts      [if component has boundaries]
7. State and Lifecycle      [if behavior depends on history]
8. Error Specification      [required]
9. Non-Functional Reqs      [if applicable]
10. Examples                [required for complex behaviors]
11. Language-Specific Notes [separate section or file]
```

Order: happy path → errors/edges → NFRs → nice-to-haves. Within components: inputs → outputs → errors → internals.

## Abstraction Level

- Describe **what** and **why**, with enough **how** to constrain — not dictate.
- Use domain language, not solution language.
- Be precise at boundaries (inputs, outputs, errors, state transitions). Be abstract about internals.
- Platform-specific statements belong in Language-Specific Notes.

## Requirements

Each requirement: **atomic** (one behavior), **testable**, **unambiguous** (one interpretation).

**Banned terms** (replace with measurables): robust, efficient, user-friendly, flexible, reliable, secure, fast, scalable, appropriate, various, quickly, "in a timely manner."

**Fix ambiguity:** replace pronouns with nouns, use active voice, split compound "and" statements.

**EARS template:**
```
[When <trigger>] [while <precondition>] the <system> shall <action> [the <object>]
```

## Behavioral Specs — Design by Contract

| Element | Definition |
|---------|-----------|
| **REQUIRES** | What must be true before (caller's obligation) |
| **ENSURES** | What must be true after (implementer's obligation) |
| **MAINTAINS** | What is always true (both sides) |

Include 2-3 concrete Given/When/Then examples per behavior, placed immediately after the requirement.

## Data Model

Define entities with domain-level types. State all constraints, validation rules, and relationships with cardinality.

## Interface Contracts

Per boundary operation: **Input**, **Output**, **Guarantees**, **Error strategy**, **Concurrency**, **Idempotency** (required for retriable operations). Complete when either side can be implemented without reading the other's internals.

## State Machines

Always provide an explicit transition table — never narrative.

```
| Current State | Event | Guard | Action | Next State |
```

Every non-terminal state needs at least one outbound transition. Every event accounted for in every non-terminal state.

## Error Specification

Classify per operation: **input error**, **state error**, **dependency error**, **invariant violation**.

Enumerate edge cases: empty input, boundary values, null/missing, duplicates, concurrent access, partial failure, repeated invocation.

## Signal Quality

- Target ≤ 3,000 tokens per section.
- Prefer tables over prose for structured content.
- No TBD/TODO — make provisional decisions explicitly.
- No aspirational prose or redundant restatements.
- Front-load critical requirements.

## Language Separation

Keep language-agnostic content separate from language-specific content. The agnostic layer must survive a technology migration unchanged.

### Feature Documents

**Layer:** 2 — Behavioral Specification

**Location:** `doc/features/<feature-name>.md`

**Purpose:** Describes a feature from the user's perspective — what it does, why it exists, and the design decisions and tradeoffs behind it. Feature documents capture intent and rationale. They do not describe pipelines, data formats, or implementation mechanics.

**Authoritative for:**
- What a feature provides and what it does not provide
- The design decisions and tradeoffs behind the feature
- User-facing behavior and constraints

**Relationship to other types:** Feature documents are downstream of PRDs and user stories, which provide stakeholder intent and acceptance criteria. Each feature document has one or more corresponding architecture documents that describe *how* the feature is implemented. The feature document answers "what and why"; the architecture document answers "how."

**One per:** feature or concern

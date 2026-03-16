### 1. Architecture Documents (Component Specifications)

**Layer:** 3 — Design Specification

**Location:** `doc/architecture/<component-or-concern>.md`

**Purpose:** Describes how a feature or concern is implemented at the design level — pipelines, data flows, component responsibilities, boundary contracts, and identified gaps. Architecture documents do not re-state what a feature does; those belong in the corresponding feature document.

**Authoritative for:**
- Sequence diagrams and pipeline steps
- Component boundaries and inter-component contracts
- File and directory conventions
- Identified implementation gaps requiring decisions

**Structure:** Follows the specification document structure defined in `doc/sdd-specification-standards.md` § 3 (Purpose, Scope, Definitions, Behavioral Requirements, Data Model, Interface Contracts, State and Lifecycle, Error Specification, Non-Functional Requirements, Examples, Language-Specific Notes).

**Relationship to other types:** Each architecture document opens with a pointer to the corresponding feature document for context. Architecture documents are the primary input to the LLM spec-extraction pipeline that produces `specification/` artifacts. Architecture documents may reference a standalone data model document for shared entity definitions.

**One per:** component, pipeline, or cross-cutting concern

### 2. Component Boundary Document

**Layer:** 3 — Design Specification

**Location:** `doc/architecture/component-boundaries.md` (single document)

**Purpose:** System-level view of all cross-component boundaries, the complete dependency graph, and the mapping from source documents to specifications. This is the authoritative cross-reference for boundary contracts; per-component architecture documents contain convenience summaries.

**Authoritative for:**
- The component taxonomy (which components exist and what each owns)
- The dependency graph (which components depend on which)
- Boundary contracts (what crosses each boundary, in which direction, with what guarantees)
- The source-to-specification mapping (which architecture documents produce which specifications)

**Relationship to other types:** The component boundary document is a summary derived from the architecture documents — it is not itself a source of truth for boundary design. When this document and an architecture document disagree, the architecture document is authoritative for the boundary's design, and the disagreement is a gap-analysis finding. The change propagation procedure and the spec-extraction validation step both consume this document.

**One per:** project (singleton)

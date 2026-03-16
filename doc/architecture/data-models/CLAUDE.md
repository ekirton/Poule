# Data Model Documents

**Layer:** 3 — Design Specification
**Location:** `doc/architecture/data-models/<domain-or-component>.md`

## Authority

Data model documents are the **single source of truth** for entity structure. All downstream documents must use the exact entity names, node labels, field names, types, and constraints defined here. Data model wins over architecture on entity structure; architecture wins on usage.

**Before editing:** changes cascade to all downstream documents. Verify name or constraint changes are intentional and update referencing architecture documents.

## Standards

For each entity, specify:
- Entity name and purpose (one sentence)
- Fields with domain-level types
- Validation rules and constraints
- Relationships to other entities (cardinality and ownership)

**One per:** domain area or shared data concern

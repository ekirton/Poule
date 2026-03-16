### Product Requirements Documents (PRD)

**Layer:** 1 — Stakeholder Intent

**Location:** `doc/requirements/<product-or-initiative>.md`

**Purpose:** Captures the product-level rationale for an initiative — business goals, target users, competitive context, and a prioritized requirement pool. PRDs answer "what should the product do and why does it matter?" at a level above individual features. They are the primary input to feature document authoring and user story derivation.

**Authoritative for:**
- Product goals and success metrics
- Target user segments and their needs
- Competitive analysis and market context
- Requirement pool with priority classifications (P0 = must-have, P1 = should-have, P2+ = nice-to-have)
- Scope boundaries (what is explicitly out of scope)

**Relationship to other types:** PRDs are upstream of feature documents and user story documents. Each PRD may spawn multiple feature documents and user stories. PRDs reference research documents for evidence grounding. They are not consumed by the LLM spec-extraction pipeline directly — their content flows through feature and architecture documents.

**One per:** product initiative or major capability

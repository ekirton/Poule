# Before You Start

Read `index.md` to understand what documents exist in this directory and their purposes. This allows you to intelligently navigate and read relevant documents as needed.

The files in this folder review the state of the art but shall not discuss or mention the product described in the parent folder.

### Research Documents

**Layer:** Reference — supports all layers (evidence base for decisions at any level)

**Location:** `doc/background/<topic>.md`

**Purpose:** Captures background research that informs specification decisions — technology surveys, current art, academic literature reviews, and benchmarks. Research documents are reference material; they do not contain requirements or specification statements.

**Authoritative for:**
- Factual findings and source citations
- Comparative analysis of approaches
- Evidence supporting or challenging design decisions

**Relationship to other types:** Research documents are referenced by PRDs, feature documents, architecture documents, and specification standards to ground design decisions in evidence. They are not consumed by the LLM spec-extraction pipeline.

**One per:** research topic or investigation

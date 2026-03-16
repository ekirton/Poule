# Exposing Search/Retrieval Services via MCP for LLM Reasoning
## State-of-the-Art Survey (Early 2026)

---

## 1. MCP for Search/Retrieval: Existing Servers and Patterns

### Official Vector Database MCP Servers

As of early 2026, all major vector database vendors ship official MCP servers:

**Qdrant** ([mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant)): Official MCP server acting as a semantic memory layer. Uses `sentence-transformers/all-MiniLM-L6-v2` by default for embeddings. Exposes tools for storing and retrieving "memories" via vector similarity. Available on PyPI (`mcp-server-qdrant`). A community variant ([qdrant-knowledge-graph](https://www.pulsemcp.com/servers/delorenj-qdrant-knowledge-graph)) adds knowledge-graph overlays on top of Qdrant.

**Weaviate** ([mcp-server-weaviate](https://github.com/weaviate/mcp-server-weaviate)): Official server exposing `semantic_search` (pure vector similarity), `keyword_search` (BM25), and `hybrid_search` (combined) tools. This is notably the most featureful search-specific MCP server, giving the LLM explicit control over retrieval strategy.

**MindsDB** ([unified MCP server](https://mindsdb.com/unified-model-context-protocol-mcp-server-for-vector-stores)): A unified MCP server integrating Pinecone, Weaviate, and Qdrant behind a single tool interface, abstracting over multiple vector backends.

### Knowledge Graph MCP Servers

**Neo4j** ([mcp-neo4j](https://github.com/neo4j-contrib/mcp-neo4j)): Official Neo4j Labs MCP server with two modes:
- `mcp-neo4j-cypher`: Exposes the graph schema and lets the LLM generate/execute Cypher queries directly. This is a "schema-first" pattern where the agent reasons about graph structure.
- `mcp-neo4j-memory`: Stores entities, observations, and relationships; supports subgraph retrieval by relevance. Based on Anthropic's original knowledge-graph memory example, upgraded to use Neo4j as the backend.

**Graphiti** ([getzep/graphiti](https://github.com/getzep/graphiti)): A real-time knowledge graph framework with a built-in MCP server. Unlike traditional RAG, Graphiti continuously integrates user interactions and enterprise data into a queryable graph, supporting incremental updates without full recomputation. Backs onto Neo4j, Amazon Neptune, FalkorDB, or Kuzu. Agents interact via tool calls for storing, retrieving, and traversing relationships.

**GraphRAG MCP** ([mcpservers.org](https://mcpservers.org/servers/rileylemm/graphrag_mcp)): Community server implementing Microsoft's GraphRAG pattern over MCP.

### Emerging Patterns

1. **Schema-first tools**: Expose the database schema as a resource, let the LLM compose queries (Neo4j Cypher, Weaviate GraphQL). Maximizes flexibility but requires the LLM to understand query languages.
2. **Semantic memory tools**: Abstract away query languages; expose `store(text)` and `search(query)` primitives. Simpler for the LLM but less flexible (Qdrant pattern).
3. **Multi-strategy tools**: Expose multiple retrieval strategies (semantic, keyword, hybrid) as separate tools, letting the LLM choose adaptively (Weaviate pattern).
4. **Unified backends**: A single MCP server abstracts over multiple databases (MindsDB pattern).

---

## 2. MCP vs Function Calling vs Tool Use: Trade-offs

### Architectural Relationship

MCP and function calling are complementary, not competing. Function calling (Phase 1) translates natural language into structured tool invocations. MCP (Phase 2) standardizes how those invocations are executed across systems. Each LLM vendor has its own function-calling format (OpenAI `tool_calls`, Claude `tool_use`, Gemini `functionCall`), while MCP provides a vendor-neutral JSON-RPC layer for execution. ([Gentoro comparison](https://www.gentoro.com/blog/function-calling-vs-model-context-protocol-mcp))

### Context Window Cost

This is the critical trade-off for search/retrieval:

- Each MCP tool schema consumes **200-400 tokens**. At 50 tools, that is 10,000-20,000 tokens before any conversation begins. ([EclipseSource](https://eclipsesource.com/blogs/2026/01/22/mcp-context-overload/))
- Tool-calling accuracy **degrades after ~20-30 tools**, and by 40+ tools the model struggles to select the right one. Adding more detail to tool descriptions to aid selection backfires by consuming more context. ([Lunar.dev](https://www.lunar.dev/post/why-is-there-mcp-tool-overload-and-how-to-solve-it-for-your-ai-agents))
- Each invocation costs a **full round-trip**: model -> MCP client -> MCP server -> back to model, with schema parsing and context reassembly at each step.

### Latency Implications

| Approach | Latency Profile | Best For |
|----------|----------------|----------|
| Direct function call (in-process) | Minimal; no network hop | Latency-critical local operations |
| MCP tool (local server) | Low; local IPC | IDE integrations, local DB queries |
| MCP tool (remote server) | Network RTT per call | Cloud-hosted vector DBs, APIs |
| RAG (pre-retrieval injection) | One-shot; no tool call overhead | When relevant context is predictable |

### Solutions to Context Bloat

- **Claude's Tool Search**: Dynamically discovers and loads only 3-5 relevant tools per query from a larger catalog, rather than pre-loading all tool schemas. ([candede.com](https://www.candede.com/articles/claude-tool-search))
- **Dynamic Context Loading (DCL)**: The model receives a lightweight summary of available capabilities and loads specific tool schemas on demand. ([Moncef Abboud](https://cefboud.com/posts/dynamic-context-loading-llm-mcp/))
- **Bounded Context Packs**: Group tools by domain (all search tools together, all memory tools together) and load packs as needed. ([Synaptic Labs](https://blog.synapticlabs.ai/bounded-context-packs-tool-bloat-tipping-point))
- **Code Execution with MCP**: Anthropic's approach where agents execute code that calls MCP tools, filtering data before it reaches the model's context. ([Anthropic engineering](https://www.anthropic.com/engineering/code-execution-with-mcp))

### Observed Best Practices

Among existing search MCP servers, those with small tool surfaces (3-5 tools such as `search`, `get_document`, `list_collections`) have shown the best results, pushing complexity into tool parameters rather than proliferating tools. The Weaviate server's pattern of offering `semantic_search`, `keyword_search`, and `hybrid_search` as separate tools is representative of this approach -- it provides the LLM with strategic choice without overloading context.

---

## 3. Agentic Retrieval Patterns

### Core Principles (2025-2026 Consensus)

Three properties define a "truly agentic" RAG system ([A-RAG, Feb 2026](https://arxiv.org/abs/2602.03442)):

1. **Autonomous Strategy**: The LLM dynamically chooses retrieval strategies without hardcoded workflows
2. **Iterative Execution**: Multi-round retrieve-reason-retrieve loops, adapting based on intermediate results
3. **Interleaved Tool Use**: ReAct-style action-observation-reasoning loops mixing retrieval with computation

### Key Frameworks

**A-RAG** (University of Science and Technology of China, Feb 2026): State-of-the-art agentic RAG framework exposing hierarchical retrieval interfaces -- keyword search, semantic search, and chunk read -- at different granularities. The agent autonomously decides which interface to use and how many rounds to iterate. Achieves **94.5% on HotpotQA** and **89.7% on 2WikiMultiHop** with GPT-5-mini, significantly outperforming prior methods. Demonstrates scaling: performance improves with both stronger models and more test-time compute.

**PRISM** (Oct 2025, [arxiv](https://arxiv.org/html/2510.14278v1)): Separates precision-oriented filtering from recall-oriented retrieval in an iterative loop:
- *Selector Agent*: Removes distractors from candidate passages (precision focus)
- *Adder Agent*: Recovers overlooked bridging facts (recall focus)
- Iterates up to 3 rounds. Achieves **90.9% passage recall on HotpotQA** (vs. 72.8% for IRCoT baseline).

**R3-RAG** (EMNLP 2025, [paper](https://aclanthology.org/2025.findings-emnlp.554.pdf)): Teaches step-by-step reasoning interleaved with retrieval, learning when to retrieve vs. when to reason from already-gathered context.

**Agentic RAG with Knowledge Graphs** ([arxiv, Jul 2025](https://arxiv.org/abs/2507.16507)): Combines graph-structured retrieval with agentic multi-hop reasoning for complex real-world applications, using knowledge graphs as the retrieval substrate rather than flat document stores.

### Pattern Summary

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| Single-shot RAG | Retrieve once, generate | Simple factual queries |
| Iterative refinement | Retrieve, critique, re-query | When initial results may be incomplete |
| Multi-hop decomposition | Decompose question, retrieve per sub-question | Complex multi-fact questions |
| Hierarchical retrieval | Multiple granularity tools (keyword/semantic/chunk) | Large heterogeneous corpora |
| Precision-recall loop | Separate filter and expand phases | When both precision and recall matter |
| Graph traversal | Follow relationships in knowledge graphs | Entity-relationship queries |

---

## 4. LLM-as-Reranker: Latest Findings

### The Case Against LLMs as Rerankers

Voyage AI's October 2025 study ([blog post](https://blog.voyageai.com/2025/10/22/the-case-against-llms-as-rerankers/)) provides the most comprehensive benchmarks:

**Cost**: Purpose-built rerankers (e.g., `rerank-2.5`) cost $0.05/M tokens vs. $1.25-$3.00/M for LLMs -- **25-60x cheaper**.

**Speed**: `rerank-2.5` is 9x faster than Claude Sonnet 4.5, 36x faster than GPT-5, and 48x faster than Gemini 2.5 Pro.

**Accuracy** (NDCG@10 across 13 real-world datasets, 8 domains): `rerank-2.5` outperformed:
- GPT-5 by 12.61%
- Gemini 2.5 Pro by 13.43%
- Qwen 3 32B by 14.78%

**Critical finding**: When paired with strong first-stage retrieval, LLMs actually *degraded* performance. Qwen 3 32B and Gemini 2.0 Flash reduced NDCG@10 from 81.58% to ~80% and ~79% respectively.

### When LLMs Can Help

- **Generalization**: Listwise LLM reranking shows the best generalization to unseen content (8% avg degradation vs. 12-15% for other methods). ([EMNLP 2025 study](https://github.com/DataScienceUIBK/llm-reranking-generalization-study))
- **Training-free confidence reranking**: Using lightweight 7-9B LLMs as confidence scorers achieves up to 20.6% relative NDCG@5 improvement on BEIR/TREC benchmarks without any training. ([LLM-Confidence Reranker, Feb 2026](https://arxiv.org/pdf/2602.13571))
- **Niche/novel domains**: Where specialized rerankers lack training data, LLMs' general knowledge provides a fallback.

### Recommended Architecture

The emerging consensus is a **cascaded pipeline**:
1. Fast embedding model retrieves top-200 candidates
2. Specialized cross-encoder reranks to top-20
3. (Optional) LLM listwise reranking on final top-10, only if the domain is novel or the task requires deep reasoning about relevance

For most production search systems, skip stage 3 -- the cost/latency penalty rarely justifies the marginal accuracy gain. For agentic systems where the LLM is already in the loop, having it assess relevance of retrieved results as part of its reasoning (implicit reranking) is essentially free and often sufficient.

---

## 5. Alternative Exposure Mechanisms (Beyond MCP)

### Direct Web/REST APIs for Agent Consumption

- **Exa**: AI-native search engine with an API specifically designed for LLM integration; offers search, content retrieval, similar-link finding, and direct QA. Uses its own search index + vector DB.
- **Tavily**: Positions itself as "the web access layer for AI agents" with APIs optimized for RAG workflows and real-time search.
- **Firecrawl, Serper, Brave Search API**: General web search APIs increasingly used by AI agents.

These are consumed via standard function calling or MCP wrappers. The distinction from MCP-native servers is that these are cloud-hosted services with their own rate limits and pricing, while MCP servers can run locally.

### Integration Platforms (iPaaS)

- **Zapier Natural Language Actions (NLA)**: Exposes Zapier's 6000+ app integrations to LLMs via natural language. An LLM can trigger search across connected systems without per-service integration.
- **n8n, Make.com**: Open-source/low-code alternatives increasingly exposing agent-friendly interfaces.

### LSP Extensions and IDE Plugins

The Language Server Protocol (LSP) is a natural complement to MCP for code-aware search:
- **Lean LSP MCP** bridges LSP and MCP (see Section 6)
- **Coq LSP MCP** ([mcp-coq-lsp](https://github.com/scidonia/mcp-coq-lsp)): Exposes 8 MCP tools wrapping the Coq/Rocq language server
- Several IDE plugins (Cursor, Windsurf, VS Code Copilot) now support MCP natively, meaning any MCP search server is automatically available in the IDE context

### RPA and Browser Automation

- **UiPath** adopted MCP for bi-directional AI-RPA integration
- Browser automation agents (Playwright-based) operate at the UI layer, bypassing API limitations entirely -- useful when search services lack APIs

### Cloud-Managed Agent Platforms

- **Vertex AI Extensions** (GCP): Managed tool hosting with enterprise access controls
- **Azure Semantic Kernel**: Microsoft's agent framework with built-in retrieval connectors
- **AWS Bedrock Agents**: Managed agent runtime with knowledge base integration

### Key Insight

MCP is becoming the de facto standard for local/IDE tool integration, but for cloud-scale production systems, direct API calls via function calling remain dominant due to lower latency and simpler error handling. The trend is toward **MCP for development-time / interactive use** and **direct API integration for production pipelines**.

---

## 6. Lean Ecosystem Search Tools: IDE and Agent Integration

### Search Engines for Lean 4 / Mathlib

**LeanExplore** ([arxiv, Jun 2025](https://arxiv.org/html/2506.11085v1)): Hybrid search combining:
- Semantic embeddings (BAAI `bge-base-en-v1.5`, 109M params)
- BM25+ lexical matching
- PageRank scoring based on inter-declaration dependencies
- Novel "StatementGroups" abstraction aligning results with how developers author code

Ranked 1st in 55.4% of test queries (vs. LeanSearch 46.3%, Moogle 12.0%). Notably outperforms despite using a much smaller embedding model than LeanSearch's E5mistral-7b. **Provides an MCP server**, Python API, and CLI chat with Claude integration. The paper reports that "Claude Code successfully proved theorems leveraging LeanExplore's MCP interface."

**LeanSearch** ([LeanSearchClient](https://github.com/leanprover-community/LeanSearchClient)): Natural language search over Mathlib via API. Integrated into Lean 4 via the `#leansearch` command. Uses E5mistral-7b embeddings.

**Moogle** (Morph Labs): LLM-based semantic search for Mathlib. Available in VS Code via "Lean4: Moogle: Search" command. Ranked 1st in only 12.0% of instances in LeanExplore's evaluation.

**Lean Finder** ([arxiv, Oct 2025](https://arxiv.org/abs/2510.15940)): Semantic search engine fine-tuned on synthesized queries matching real mathematician intents. Achieves **30%+ relative improvement over previous engines and GPT-4o**. Compatible with LLM-based theorem provers.

**Loogle** ([loogle.lean-lang.org](https://loogle.lean-lang.org/)): Pattern/type-based search (not semantic). Accessible via VS Code extension, CLI, `#loogle` command in Lean, lean.nvim, and Zulip bot.

### Lean LSP MCP Server

The **lean-lsp-mcp** server ([GitHub](https://github.com/oOo0oOo/lean-lsp-mcp)) is the most comprehensive integration layer, bridging the Lean Language Server Protocol with MCP. It exposes:

**LSP-derived tools:**
- Diagnostics and proof goals at specific locations
- Hover documentation and type signatures
- Code completion and import suggestions
- Code actions (e.g., `simp?`, `exact?` suggestions)
- File outline with declarations
- Proof profiling (per-line tactic timing)

**External search tools:**
- LeanSearch (natural language queries)
- Loogle (type/pattern matching, with local mode to avoid rate limits)
- Lean Finder (semantic search)
- Lean Hammer and State Search

**Setup**: `claude mcp add lean-lsp uvx lean-lsp-mcp` for Claude Code; similar one-liners for Cursor and VS Code. Rate-limited to 3 external search requests per 30 seconds.

### Coq/Rocq Ecosystem Comparison

The Coq/Rocq ecosystem is less mature for search but advancing rapidly:

- **mcp-coq-lsp** ([GitHub](https://github.com/scidonia/mcp-coq-lsp)): MCP server wrapping coq-lsp/rocq-lsp with 8 exposed tools
- **MCP-RoCQ** ([mcp.so](https://mcp.so/server/mcp-rocq)): Formal proof management MCP server
- **RocqStar** ([JetBrains Research, May 2025](https://arxiv.org/pdf/2505.22846)): Agentic theorem proving with similarity-driven retrieval. Uses custom `rocq-language-theorem-embeddings` (on HuggingFace) alongside BM25. Multi-agent debate pattern for proof strategy selection. Available at [github.com/JetBrains-Research/rocqstar-rag](https://github.com/JetBrains-Research/rocqstar-rag).

There is no Moogle/LeanSearch equivalent for Coq/Rocq -- no public semantic search engine over the Coq standard library or Mathematical Components. This represents a significant gap.

---

## Summary of Findings

1. **MCP for search is production-ready**: Official servers exist for Qdrant, Weaviate, Neo4j, and unified backends. The pattern is mature enough for IDE and agent integration.

2. **Small tool surfaces correlate with better outcomes**: Servers exposing 3-5 search tools occupy a sweet spot where LLMs can make strategic choices without context overload. Dynamic tool loading (Claude's Tool Search, DCL) mitigates scaling issues when more tools are available.

3. **Agentic retrieval is the frontier**: A-RAG (Feb 2026) shows that giving LLMs hierarchical retrieval interfaces and letting them choose strategy autonomously outperforms hardcoded pipelines. The field is moving from "retrieve then generate" to "reason about what to retrieve."

4. **Specialized rerankers outperform LLM-based reranking**: Benchmarks show specialized rerankers are 25-60x cheaper, up to 48x faster, and 12-15% more accurate than LLM reranking. LLM reranking has shown advantages only in novel domains or when the LLM is already reasoning about the results.

5. **MCP is winning for interactive/IDE use; direct APIs win for production**: MCP's value is in standardizing tool discovery and integration for development environments. Production pipelines still prefer direct API calls for performance.

6. **Lean's search ecosystem is the most mature in formal verification**: The lean-lsp-mcp server demonstrates how to bridge LSP + multiple search engines + MCP into a unified agent interface. The Coq/Rocq ecosystem lacks equivalent search infrastructure.

---

## Sources

- [Qdrant MCP Server](https://github.com/qdrant/mcp-server-qdrant)
- [Weaviate MCP Server](https://github.com/weaviate/mcp-server-weaviate)
- [MindsDB Unified MCP Server](https://mindsdb.com/unified-model-context-protocol-mcp-server-for-vector-stores)
- [Neo4j MCP Integrations](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)
- [Neo4j MCP GitHub](https://github.com/neo4j-contrib/mcp-neo4j)
- [Graphiti Knowledge Graph](https://github.com/getzep/graphiti)
- [GraphRAG MCP Server](https://mcpservers.org/servers/rileylemm/graphrag_mcp)
- [Function Calling vs MCP - Gentoro](https://www.gentoro.com/blog/function-calling-vs-model-context-protocol-mcp)
- [MCP Context Overload - EclipseSource](https://eclipsesource.com/blogs/2026/01/22/mcp-context-overload/)
- [MCP Tool Overload - Lunar.dev](https://www.lunar.dev/post/why-is-there-mcp-tool-overload-and-how-to-solve-it-for-your-ai-agents)
- [Claude Tool Search - candede.com](https://www.candede.com/articles/claude-tool-search)
- [Dynamic Context Loading](https://cefboud.com/posts/dynamic-context-loading-llm-mcp/)
- [Bounded Context Packs - Synaptic Labs](https://blog.synapticlabs.ai/bounded-context-packs-tool-bloat-tipping-point)
- [Code Execution with MCP - Anthropic](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Skills vs MCP Tools - LlamaIndex](https://www.llamaindex.ai/blog/skills-vs-mcp-tools-for-agents-when-to-use-what)
- [The MCP Tool Trap - Jentic](https://jentic.com/blog/the-mcp-tool-trap)
- [A-RAG: Hierarchical Retrieval Interfaces](https://arxiv.org/abs/2602.03442)
- [PRISM: Agentic Retrieval for Multi-Hop QA](https://arxiv.org/html/2510.14278v1)
- [Agentic RAG with Knowledge Graphs](https://arxiv.org/abs/2507.16507)
- [R3-RAG: Step-by-Step Reasoning and Retrieval](https://aclanthology.org/2025.findings-emnlp.554.pdf)
- [Agentic RAG Survey](https://github.com/asinghcsu/AgenticRAG-Survey)
- [The Case Against LLMs as Rerankers - Voyage AI](https://blog.voyageai.com/2025/10/22/the-case-against-llms-as-rerankers/)
- [LLM Reranking Generalization Study (EMNLP 2025)](https://github.com/DataScienceUIBK/llm-reranking-generalization-study)
- [LLM-Confidence Reranker](https://arxiv.org/pdf/2602.13571)
- [Choosing the Best Reranking Model in 2026 - ZeroEntropy](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025)
- [Top MCP Alternatives - o-mega.ai](https://o-mega.ai/articles/top-10-mcp-alternatives-connect-everything-in-2025)
- [MCP Alternatives - Sider](https://sider.ai/blog/ai-tools/model-context-protocol-alternatives-what-to-use-instead-in-2025)
- [Best Web Search APIs for AI 2026 - Firecrawl](https://firecrawl.dev/blog/top_web_search_api_2025)
- [LeanExplore](https://arxiv.org/html/2506.11085v1)
- [Lean Finder](https://arxiv.org/abs/2510.15940)
- [LeanSearchClient](https://github.com/leanprover-community/LeanSearchClient)
- [Loogle](https://loogle.lean-lang.org/)
- [Lean LSP MCP Server](https://github.com/oOo0oOo/lean-lsp-mcp)
- [mcp-coq-lsp](https://github.com/scidonia/mcp-coq-lsp)
- [RocqStar](https://arxiv.org/pdf/2505.22846)
- [MCP-RoCQ](https://mcp.so/server/mcp-rocq)

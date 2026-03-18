# Live Diagram Viewer

Automatic rendering of proof visualization diagrams in the user's browser — diagrams appear the moment a visualization MCP tool is called, with no manual steps.

**Stories**: [Epic 5: Live Diagram Viewer](../requirements/stories/proof-visualization-widgets.md#epic-5-live-diagram-viewer)

---

## Problem

Poule's visualization tools generate Mermaid diagram syntax — text that describes a diagram. In Claude Code's terminal interface, this text is returned to the LLM, which can display it as raw text. But the whole point of visualization is to *see* a rendered graphic. The user needs a visual channel alongside the terminal.

## Solution

A web-based diagram viewer served directly by the Poule MCP server. The user opens `http://localhost:3000/viewer` in their browser once and leaves it open. When any visualization tool is called, the MCP server pushes the generated Mermaid diagram to the viewer via Server-Sent Events (SSE). The viewer renders it using mermaid.js from CDN.

The user experience is:
1. Start the container: `poule`
2. Open `http://localhost:3000/viewer` in a browser
3. Work with Claude: "Visualize the proof tree for `app_nil_r`"
4. Diagram appears in the browser tab automatically

## Design Rationale

### Why the MCP server hosts the viewer

The MCP server already runs as an HTTP daemon at port 3000. Adding viewer endpoints means no extra process, no extra port, no extra configuration. The viewer is just two additional HTTP routes.

### Why SSE rather than WebSocket

SSE is one-directional push — exactly what the viewer needs. Simpler than WebSocket, with automatic reconnection built into the browser's EventSource API.

### Why mermaid.js from CDN

No bundling needed, browser caches it, Docker image stays lean.

## Scope Boundaries

Provides: HTML page at `/viewer`, SSE push of diagram updates, client-side rendering via mermaid.js, in-memory history of recent diagrams.

Does **not** provide: persistent diagram storage, multi-user support, diagram editing, offline rendering, authentication.

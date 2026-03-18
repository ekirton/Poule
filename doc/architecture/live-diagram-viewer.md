# Live Diagram Viewer

The server-side infrastructure and client-side page that renders Mermaid diagrams in the user's browser automatically when visualization MCP tools are called.

**Feature**: [Live Diagram Viewer](../features/live-diagram-viewer.md)
**Stories**: [Epic 5](../requirements/stories/proof-visualization-widgets.md#epic-5-live-diagram-viewer)
**Related**: [MCP Server](mcp-server.md), [Mermaid Renderer](mermaid-renderer.md)

---

## Component Diagram

```
Host Machine                          Docker Container
                                      MCP Server (port 3000)
Browser Tab                           +------------------------------+
+--------------+                      |                              |
|              |  GET /viewer         |  /viewer          -> HTML    |
|  Viewer Page |<---------------------|  /viewer/events   -> SSE    |
|              |                      |  /mcp             -> MCP    |
|  mermaid.js  |  SSE /viewer/events  |                              |
|  (from CDN)  |<---------------------|  DiagramBroadcaster          |
|              |                      |    push(diagram)             |
|  Renders     |                      |                              |
|  diagrams    |                      |  Visualization Tool Handlers |
+--------------+                      +------------------------------+
       ^
       | -p 3000:3000 (docker port mapping)
```

## DiagramBroadcaster

In-memory pub/sub within the MCP server process. Maintains connected SSE client queues and broadcasts DiagramEvent objects.

- History: bounded list of most recent 50 DiagramEvents.
- Clients: set of asyncio.Queue objects, one per connected viewer tab.
- push(): appends to history, writes SSE message to all client queues. Fire-and-forget.
- push_diagram(): creates event with auto-assigned monotonic ID and ISO 8601 timestamp.

## SSE Endpoint

`GET /viewer/events` returns a streaming response:
- On connect: sends `event: history` with all past events.
- On new diagram: sends `event: diagram` with the DiagramEvent.
- Keepalive: `: keepalive\n\n` every 30 seconds.

## Viewer HTML

Self-contained HTML page served at `GET /viewer`:
1. Loads mermaid.js from CDN
2. Connects to `/viewer/events` via EventSource
3. Renders Mermaid syntax via `mermaid.render()`
4. History sidebar for browsing previous diagrams
5. Auto-reconnect on connection loss

## Integration

Visualization tool handlers push DiagramEvents after generating Mermaid text:
- `visualize_proof_state` -> title: "Proof State: {session_id} step {N}"
- `visualize_proof_tree` -> title: "Proof Tree: {proof_name}"
- `visualize_dependencies` -> title: "Dependencies: {name}"
- `visualize_proof_sequence` -> title: "Proof Sequence: {session_id}"

Push is fire-and-forget. Handlers accept `broadcaster=None` for backward compatibility.

## Container Configuration

`bin/poule` adds `-p 3000:3000` to docker run. No additional processes or Dockerfile layers needed.

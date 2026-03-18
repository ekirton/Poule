# Live Diagram Viewer

In-process SSE broadcaster and HTTP endpoints that push Mermaid diagram text to a browser-based viewer whenever a visualization MCP tool is called.

**Architecture**: [live-diagram-viewer.md](../doc/architecture/live-diagram-viewer.md), [mcp-server.md](../doc/architecture/mcp-server.md)

---

## 1. Purpose

Define the DiagramBroadcaster, DiagramEvent data type, HTTP viewer endpoints, and the integration contract with visualization tool handlers.

## 2. Scope

**In scope**: DiagramBroadcaster (in-memory pub/sub), DiagramEvent data type, SSE endpoint (`/viewer/events`), viewer HTML endpoint (`/viewer`), integration with visualization tool handlers (fire-and-forget push), bounded in-memory history, viewer HTML page content.

**Out of scope**: Mermaid diagram generation logic (owned by mermaid-renderer), image rendering (owned by client-side mermaid.js), MCP protocol handling (owned by mcp-server).

## 3. Definitions

| Term | Definition |
|------|-----------|
| DiagramBroadcaster | In-memory pub/sub channel that maintains connected SSE clients and broadcasts DiagramEvent objects |
| DiagramEvent | A data record containing tool name, title, Mermaid syntax, and metadata for one visualization |
| SSE | Server-Sent Events — a one-directional HTTP push protocol from server to browser |

## 4. Behavioral Requirements

### 4.1 DiagramBroadcaster

- Constructor: `max_history` positive integer (default: 50). Creates broadcaster with empty client set and empty history list.
- `add_client(queue)`: Adds queue to connected clients set.
- `remove_client(queue)`: Removes queue from set (safe if not present).
- `push(event)`: Appends event to history (evicting oldest if at capacity), sends SSE message to all connected clients. Fire-and-forget.
- `push_diagram(tool, title, mermaid)`: Creates DiagramEvent with auto-assigned monotonic ID and ISO 8601 timestamp, then calls push(). Returns the created event.
- `get_history()`: Returns copy of history list (oldest to newest).
- `client_count`: Property returning number of connected clients.

### 4.2 DiagramEvent

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | string | Required; monotonically increasing counter |
| `timestamp` | string | Required; ISO 8601 format |
| `tool` | string | Required; visualization tool name |
| `title` | string | Required; human-readable title |
| `mermaid` | string | Required; Mermaid syntax |

### 4.3 SSE Formatting

- `format_sse_event(event)`: Returns bytes `event: diagram\ndata: {json}\n\n`
- `format_sse_history(events)`: Returns bytes `event: history\ndata: [{json}, ...]\n\n`

### 4.4 SSE Endpoint (`GET /viewer/events`)

- Returns SSE stream with headers: Content-Type text/event-stream, Cache-Control no-cache, X-Accel-Buffering no.
- On connect: sends history event. On new diagram: sends diagram event.
- Keepalive: `: keepalive\n\n` every 30 seconds.

### 4.5 Viewer HTML (`GET /viewer`)

- Returns self-contained HTML page loading mermaid.js from CDN.
- Connects to `/viewer/events` via EventSource.
- Renders Mermaid syntax via `mermaid.render()`.
- History sidebar for browsing past diagrams.
- Reconnection indicator on connection loss.

### 4.6 Handler Integration

Each visualization handler pushes a DiagramEvent after generating Mermaid text. Fire-and-forget. Title format per tool:

| Tool | Title format |
|------|-------------|
| `visualize_proof_state` | `Proof State: {session_id} step {step_index}` |
| `visualize_proof_tree` | `Proof Tree: {proof_name}` |
| `visualize_dependencies` | `Dependencies: {name}` |
| `visualize_proof_sequence` | `Proof Sequence: {session_id}` |

## 5. Error Specification

| Condition | Behavior |
|-----------|----------|
| No clients connected on push | Event appended to history; no error |
| Client disconnects during write | Client removed from set; logged at DEBUG |
| mermaid.js CDN unreachable | Viewer displays raw Mermaid text |
| Invalid Mermaid syntax | Viewer shows error message; keeps previous diagram |

## 6. Non-Functional Requirements

- Push latency: < 1ms (in-memory). History: 50 events max (~250KB).
- SSE keepalive: 30 seconds. Viewer page load: < 100ms.
- No authentication (localhost trust boundary).

## 7. Language-Specific Notes (Python)

- Package: `src/poule/server/viewer.py`
- `DiagramEvent` as `dataclasses.dataclass`.
- `DiagramBroadcaster` uses `asyncio.Queue` per client.
- Starlette `StreamingResponse` for SSE.
- Viewer HTML as inline string constant.

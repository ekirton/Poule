"""Live Diagram Viewer — SSE broadcaster and HTTP endpoints.

Specification: specification/live-diagram-viewer.md
Architecture: doc/architecture/live-diagram-viewer.md
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class DiagramEvent:
    """A single visualization event pushed to browser viewers."""

    id: str
    timestamp: str
    tool: str
    title: str
    mermaid: str


def format_sse_event(event: DiagramEvent) -> bytes:
    """Format a DiagramEvent as an SSE message."""
    data = json.dumps(dataclasses.asdict(event), separators=(",", ":"))
    return f"event: diagram\ndata: {data}\n\n".encode("utf-8")


def format_sse_history(events: list[DiagramEvent]) -> bytes:
    """Format a list of DiagramEvents as an SSE history message."""
    data = json.dumps(
        [dataclasses.asdict(e) for e in events], separators=(",", ":")
    )
    return f"event: history\ndata: {data}\n\n".encode("utf-8")


_SSE_KEEPALIVE = b": keepalive\n\n"


class DiagramBroadcaster:
    """In-memory pub/sub for diagram events with bounded history."""

    def __init__(self, max_history: int = 50) -> None:
        self.max_history = max_history
        self._history: list[DiagramEvent] = []
        self._clients: set[asyncio.Queue] = set()
        self._counter = 0

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def add_client(self, queue: asyncio.Queue) -> None:
        self._clients.add(queue)

    def remove_client(self, queue: asyncio.Queue) -> None:
        self._clients.discard(queue)

    def get_history(self) -> list[DiagramEvent]:
        return list(self._history)

    def push(self, event: DiagramEvent) -> None:
        self._history.append(event)
        if len(self._history) > self.max_history:
            self._history.pop(0)
        msg = format_sse_event(event)
        dead: list[asyncio.Queue] = []
        for q in self._clients:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            self._clients.discard(q)
            logger.debug("Removed dead client queue from broadcaster")

    def push_diagram(self, *, tool: str, title: str, mermaid: str) -> DiagramEvent:
        self._counter += 1
        event = DiagramEvent(
            id=str(self._counter),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tool=tool,
            title=title,
            mermaid=mermaid,
        )
        self.push(event)
        return event


VIEWER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poule - Diagram Viewer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         display: flex; height: 100vh; background: #1a1a2e; color: #e0e0e0; }
  #sidebar { width: 260px; background: #16213e; border-right: 1px solid #0f3460;
             overflow-y: auto; flex-shrink: 0; }
  #sidebar h2 { padding: 16px; font-size: 14px; color: #94a3b8; text-transform: uppercase;
                 letter-spacing: 1px; border-bottom: 1px solid #0f3460; }
  .history-item { padding: 10px 16px; cursor: pointer; border-bottom: 1px solid #0f3460;
                  font-size: 13px; transition: background 0.15s; }
  .history-item:hover { background: #1a3a5c; }
  .history-item.active { background: #0f3460; }
  .history-item .title { font-weight: 600; color: #e2e8f0; }
  .history-item .meta { color: #64748b; font-size: 11px; margin-top: 2px; }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  #header { padding: 12px 24px; background: #16213e; border-bottom: 1px solid #0f3460;
            display: flex; align-items: center; justify-content: space-between; }
  #header h1 { font-size: 16px; font-weight: 600; }
  #status { font-size: 12px; padding: 4px 10px; border-radius: 12px; }
  .status-connected { background: #065f46; color: #6ee7b7; }
  .status-reconnecting { background: #92400e; color: #fbbf24; }
  .status-waiting { background: #1e3a5f; color: #7dd3fc; }
  #diagram-area { flex: 1; overflow: auto; padding: 24px; display: flex;
                  align-items: flex-start; justify-content: center; }
  #diagram-area svg { max-width: 100%; height: auto; }
  #empty-state { text-align: center; color: #64748b; padding-top: 120px; }
  #empty-state h2 { font-size: 20px; margin-bottom: 8px; color: #94a3b8; }
  #error-msg { color: #f87171; padding: 16px; font-family: monospace; white-space: pre-wrap; }
  pre.raw-mermaid { background: #0d1117; padding: 16px; border-radius: 8px;
                    font-size: 13px; overflow: auto; max-height: 80vh; color: #c9d1d9; }
</style>
</head>
<body>
<div id="sidebar">
  <h2>History</h2>
  <div id="history-list"></div>
</div>
<div id="main">
  <div id="header">
    <h1 id="diagram-title">Poule Diagram Viewer</h1>
    <span id="status" class="status-waiting">Waiting for diagrams...</span>
  </div>
  <div id="diagram-area">
    <div id="empty-state">
      <h2>Waiting for diagrams...</h2>
      <p>Ask Claude to visualize a proof tree, proof state, or dependency graph.</p>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

  const diagramArea = document.getElementById('diagram-area');
  const titleEl = document.getElementById('diagram-title');
  const statusEl = document.getElementById('status');
  const historyList = document.getElementById('history-list');
  const emptyState = document.getElementById('empty-state');
  let history = [];
  let activeIdx = -1;
  let renderCount = 0;

  function setStatus(text, cls) {
    statusEl.textContent = text;
    statusEl.className = cls;
  }

  async function renderDiagram(mermaidCode, title) {
    titleEl.textContent = title;
    if (emptyState) emptyState.remove();
    diagramArea.innerHTML = '';
    if (!mermaidCode || !mermaidCode.trim()) {
      diagramArea.innerHTML = '<p id="error-msg">(empty diagram)</p>';
      return;
    }
    try {
      renderCount++;
      const id = 'mermaid-' + renderCount;
      const { svg } = await mermaid.render(id, mermaidCode);
      diagramArea.innerHTML = svg;
    } catch (e) {
      diagramArea.innerHTML = '<p id="error-msg">Mermaid render error: ' +
        e.message + '</p><pre class="raw-mermaid">' +
        mermaidCode.replace(/</g, '&lt;') + '</pre>';
    }
  }

  function addHistoryItem(evt, idx) {
    const div = document.createElement('div');
    div.className = 'history-item' + (idx === activeIdx ? ' active' : '');
    div.innerHTML = '<div class="title">' + evt.title.replace(/</g, '&lt;') + '</div>' +
      '<div class="meta">' + new Date(evt.timestamp).toLocaleTimeString() + '</div>';
    div.onclick = () => selectHistory(idx);
    historyList.prepend(div);
  }

  function selectHistory(idx) {
    activeIdx = idx;
    const evt = history[idx];
    renderDiagram(evt.mermaid, evt.title);
    document.querySelectorAll('.history-item').forEach((el, i) => {
      el.classList.toggle('active', i === (history.length - 1 - idx));
    });
  }

  function rebuildHistory() {
    historyList.innerHTML = '';
    history.forEach((evt, i) => addHistoryItem(evt, i));
  }

  function connect() {
    const es = new EventSource('/viewer/events');
    es.addEventListener('history', (e) => {
      const data = JSON.parse(e.data);
      history = data;
      rebuildHistory();
      if (history.length > 0) {
        selectHistory(history.length - 1);
        setStatus('Connected', 'status-connected');
      }
    });
    es.addEventListener('diagram', (e) => {
      const evt = JSON.parse(e.data);
      history.push(evt);
      activeIdx = history.length - 1;
      addHistoryItem(evt, activeIdx);
      renderDiagram(evt.mermaid, evt.title);
      setStatus('Connected', 'status-connected');
    });
    es.onopen = () => setStatus('Connected', 'status-connected');
    es.onerror = () => setStatus('Reconnecting...', 'status-reconnecting');
  }

  connect();
</script>
</body>
</html>
"""


async def viewer_page_handler(request: Any) -> Any:
    """Serve the viewer HTML page at GET /viewer."""
    from starlette.responses import HTMLResponse
    return HTMLResponse(VIEWER_HTML)


async def viewer_sse_handler(request: Any, broadcaster: DiagramBroadcaster) -> Any:
    """Serve the SSE event stream at GET /viewer/events."""
    from starlette.responses import StreamingResponse

    queue: asyncio.Queue = asyncio.Queue()
    broadcaster.add_client(queue)

    async def event_stream():
        try:
            yield format_sse_history(broadcaster.get_history())
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield _SSE_KEEPALIVE
        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.remove_client(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


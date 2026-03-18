"""TDD tests for the Live Diagram Viewer (specification/live-diagram-viewer.md)."""

from __future__ import annotations
import asyncio
import json
import pytest


def _import_broadcaster():
    from poule.server.viewer import DiagramBroadcaster
    return DiagramBroadcaster

def _import_event():
    from poule.server.viewer import DiagramEvent
    return DiagramEvent

def _import_viewer_html():
    from poule.server.viewer import VIEWER_HTML
    return VIEWER_HTML

def _import_format_sse():
    from poule.server.viewer import format_sse_event, format_sse_history
    return format_sse_event, format_sse_history

def _make_event(id_="1", tool="visualize_proof_tree", title="Proof Tree: app_nil_r",
                mermaid='flowchart TD\n    s0g0["test"]', timestamp="2026-03-18T14:30:00Z"):
    return _import_event()(id=id_, timestamp=timestamp, tool=tool, title=title, mermaid=mermaid)


class TestDiagramEvent:
    def test_event_has_required_fields(self):
        e = _make_event()
        assert e.id == "1" and e.tool == "visualize_proof_tree"
    def test_event_json_roundtrip(self):
        import dataclasses
        e = _make_event()
        assert json.loads(json.dumps(dataclasses.asdict(e)))["id"] == "1"


class TestBroadcasterConstruction:
    def test_default_max_history(self):
        assert _import_broadcaster()().max_history == 50
    def test_empty_on_creation(self):
        b = _import_broadcaster()()
        assert b.get_history() == [] and b.client_count == 0


class TestBroadcasterPush:
    def test_push_appends_to_history(self):
        b = _import_broadcaster()()
        b.push(_make_event(id_="1"))
        assert len(b.get_history()) == 1
    def test_push_evicts_oldest_at_capacity(self):
        b = _import_broadcaster()(max_history=3)
        for i in range(1, 5):
            b.push(_make_event(id_=str(i)))
        assert [e.id for e in b.get_history()] == ["2", "3", "4"]
    def test_push_with_no_clients_succeeds(self):
        b = _import_broadcaster()()
        b.push(_make_event())
        assert len(b.get_history()) == 1
    @pytest.mark.asyncio
    async def test_push_sends_to_connected_clients(self):
        b = _import_broadcaster()()
        q = asyncio.Queue()
        b.add_client(q)
        b.push(_make_event(id_="42"))
        msg = await asyncio.wait_for(q.get(), timeout=1.0)
        assert b"event: diagram" in msg and b"42" in msg
        b.remove_client(q)


class TestBroadcasterClientManagement:
    def test_add_remove(self):
        b = _import_broadcaster()()
        q = asyncio.Queue()
        b.add_client(q)
        assert b.client_count == 1
        b.remove_client(q)
        assert b.client_count == 0
    def test_remove_nonexistent_is_safe(self):
        b = _import_broadcaster()()
        b.remove_client(asyncio.Queue())
        assert b.client_count == 0


class TestBroadcasterGetHistory:
    def test_history_returns_copy(self):
        b = _import_broadcaster()()
        b.push(_make_event())
        b.get_history().clear()
        assert len(b.get_history()) == 1


class TestBroadcasterMonotonicId:
    def test_auto_id_assignment(self):
        b = _import_broadcaster()()
        e1 = b.push_diagram(tool="t", title="t1", mermaid="flowchart TD")
        e2 = b.push_diagram(tool="t", title="t2", mermaid="flowchart TD")
        assert int(e1.id) < int(e2.id)
    def test_auto_id_starts_from_one(self):
        assert _import_broadcaster()().push_diagram(tool="t", title="t", mermaid="x").id == "1"
    def test_auto_timestamp_is_iso8601(self):
        import datetime
        e = _import_broadcaster()().push_diagram(tool="t", title="t", mermaid="x")
        datetime.datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))


class TestSSEFormatting:
    def test_format_sse_event(self):
        fmt, _ = _import_format_sse()
        r = fmt(_make_event(id_="5")).decode("utf-8")
        assert r.startswith("event: diagram\n") and r.endswith("\n\n")
        data = [l for l in r.split("\n") if l.startswith("data: ")][0][len("data: "):]
        assert json.loads(data)["id"] == "5"
    def test_format_sse_history_empty(self):
        _, fmt = _import_format_sse()
        r = fmt([]).decode("utf-8")
        data = [l for l in r.split("\n") if l.startswith("data: ")][0][len("data: "):]
        assert json.loads(data) == []
    def test_format_sse_history_with_events(self):
        _, fmt = _import_format_sse()
        r = fmt([_make_event(id_="1"), _make_event(id_="2")]).decode("utf-8")
        data = [l for l in r.split("\n") if l.startswith("data: ")][0][len("data: "):]
        assert len(json.loads(data)) == 2


class TestViewerHTML:
    def test_contains_mermaid_cdn(self):
        assert "cdn.jsdelivr.net/npm/mermaid" in _import_viewer_html()
    def test_contains_eventsource(self):
        h = _import_viewer_html()
        assert "EventSource" in h and "/viewer/events" in h
    def test_handles_events(self):
        h = _import_viewer_html()
        assert "diagram" in h and "history" in h
    def test_reconnection(self):
        assert "Reconnecting" in _import_viewer_html()


class TestVisualizationHandlerIntegration:
    @pytest.mark.asyncio
    async def test_visualize_proof_tree_pushes_event(self):
        from unittest.mock import AsyncMock, Mock
        from poule.session.types import ProofState, ProofTrace, TraceStep, Goal
        broadcaster = _import_broadcaster()()
        sm = AsyncMock()
        sm.extract_trace.return_value = ProofTrace(
            schema_version=1, session_id="s1", proof_name="app_nil_r",
            file_path="/t.v", total_steps=1, steps=[
                TraceStep(step_index=0, tactic=None, state=ProofState(
                    schema_version=1, session_id="s1", step_index=0,
                    is_complete=False, focused_goal_index=0,
                    goals=[Goal(index=0, type="P", hypotheses=[])])),
                TraceStep(step_index=1, tactic="auto", state=ProofState(
                    schema_version=1, session_id="s1", step_index=1,
                    is_complete=True, focused_goal_index=None, goals=[]))])
        r = Mock(); r.render_proof_tree.return_value = "flowchart TD"
        from poule.server.handlers import handle_visualize_proof_tree
        await handle_visualize_proof_tree(session_id="s1", session_manager=sm, renderer=r, broadcaster=broadcaster)
        assert len(broadcaster.get_history()) == 1
        assert "app_nil_r" in broadcaster.get_history()[0].title

    @pytest.mark.asyncio
    async def test_error_does_not_push(self):
        from unittest.mock import AsyncMock, Mock
        from poule.session.errors import SessionError
        broadcaster = _import_broadcaster()()
        sm = AsyncMock()
        sm.extract_trace.side_effect = SessionError("SESSION_NOT_FOUND", "Not found.")
        from poule.server.handlers import handle_visualize_proof_tree
        await handle_visualize_proof_tree(session_id="bad", session_manager=sm, renderer=Mock(), broadcaster=broadcaster)
        assert broadcaster.get_history() == []

    @pytest.mark.asyncio
    async def test_broadcaster_none_works(self):
        from unittest.mock import AsyncMock, Mock
        from poule.session.types import ProofState, ProofTrace, TraceStep, Goal
        sm = AsyncMock()
        sm.extract_trace.return_value = ProofTrace(
            schema_version=1, session_id="s1", proof_name="t", file_path="/t.v", total_steps=1,
            steps=[TraceStep(step_index=0, tactic=None, state=ProofState(
                schema_version=1, session_id="s1", step_index=0, is_complete=False,
                focused_goal_index=0, goals=[Goal(index=0, type="P", hypotheses=[])])),
                TraceStep(step_index=1, tactic="auto", state=ProofState(
                    schema_version=1, session_id="s1", step_index=1, is_complete=True,
                    focused_goal_index=None, goals=[]))])
        r = Mock(); r.render_proof_tree.return_value = "flowchart TD"
        from poule.server.handlers import handle_visualize_proof_tree
        result = await handle_visualize_proof_tree(session_id="s1", session_manager=sm, renderer=r, broadcaster=None)
        assert "mermaid" in json.loads(result)


class TestTitleConstruction:
    @pytest.mark.asyncio
    async def test_proof_tree_title(self):
        from unittest.mock import AsyncMock, Mock
        from poule.session.types import ProofState, ProofTrace, TraceStep, Goal
        broadcaster = _import_broadcaster()()
        sm = AsyncMock()
        sm.extract_trace.return_value = ProofTrace(
            schema_version=1, session_id="s1", proof_name="Nat.add_comm",
            file_path="/t.v", total_steps=1, steps=[
                TraceStep(step_index=0, tactic=None, state=ProofState(
                    schema_version=1, session_id="s1", step_index=0, is_complete=False,
                    focused_goal_index=0, goals=[Goal(index=0, type="P", hypotheses=[])])),
                TraceStep(step_index=1, tactic="auto", state=ProofState(
                    schema_version=1, session_id="s1", step_index=1, is_complete=True,
                    focused_goal_index=None, goals=[]))])
        r = Mock(); r.render_proof_tree.return_value = "flowchart TD"
        from poule.server.handlers import handle_visualize_proof_tree
        await handle_visualize_proof_tree(session_id="s1", session_manager=sm, renderer=r, broadcaster=broadcaster)
        assert broadcaster.get_history()[0].title == "Proof Tree: Nat.add_comm"

    @pytest.mark.asyncio
    async def test_proof_state_title(self):
        from unittest.mock import AsyncMock, Mock
        from poule.session.types import ProofState, Goal
        broadcaster = _import_broadcaster()()
        sm = AsyncMock()
        sm.observe_state.return_value = ProofState(
            schema_version=1, session_id="sess-42", step_index=5, is_complete=False,
            focused_goal_index=0, goals=[Goal(index=0, type="P", hypotheses=[])])
        r = Mock(); r.render_proof_state.return_value = "flowchart TD"
        from poule.server.handlers import handle_visualize_proof_state
        await handle_visualize_proof_state(session_id="sess-42", session_manager=sm, renderer=r, broadcaster=broadcaster)
        assert broadcaster.get_history()[0].title == "Proof State: sess-42 step 5"

    @pytest.mark.asyncio
    async def test_dependencies_title(self):
        from unittest.mock import Mock
        from poule.rendering.types import RenderedDiagram
        broadcaster = _import_broadcaster()()
        si = Mock(); si.index_ready = True; si.find_related.return_value = []
        r = Mock(); r.render_dependencies.return_value = RenderedDiagram(mermaid="flowchart TD", node_count=1, truncated=False)
        from poule.server.handlers import handle_visualize_dependencies
        await handle_visualize_dependencies(name="List.rev_append", search_index=si, renderer=r, broadcaster=broadcaster)
        assert broadcaster.get_history()[0].title == "Dependencies: List.rev_append"

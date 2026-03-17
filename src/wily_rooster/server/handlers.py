"""MCP tool handler functions for the wily-rooster server."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from wily_rooster.server.errors import (
    format_error,
    INDEX_MISSING,
    INDEX_VERSION_MISMATCH,
    NOT_FOUND,
    PARSE_ERROR,
)
from wily_rooster.session.errors import SessionError
from wily_rooster.server.validation import (
    validate_string,
    validate_limit,
    validate_symbols,
    validate_relation,
)


def _serialize(obj: Any) -> Any:
    """Convert dataclass instances to dicts for JSON serialization."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _format_success(data: Any) -> dict:
    """Format a successful response as an MCP content dict."""
    return {
        "content": [{"type": "text", "text": json.dumps(_serialize(data))}],
    }


def _check_index(ctx: Any) -> dict | None:
    """Check index state; return an error response dict if not ready, else None."""
    if not ctx.index_ready:
        return format_error(INDEX_MISSING, "Index database not found. Run the indexing command to create it.")
    if getattr(ctx, "index_version_mismatch", False) is True:
        found = getattr(ctx, "found_version", "unknown")
        expected = getattr(ctx, "expected_version", "unknown")
        return format_error(
            INDEX_VERSION_MISMATCH,
            f"Index schema version {found} is incompatible with tool version {expected}. Re-indexing from scratch.",
        )
    return None


def handle_search_by_name(ctx: Any, *, pattern: str, limit: int) -> dict:
    """Handle search_by_name tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        pattern = validate_string(pattern)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "pattern must be a non-empty string.")
    limit = validate_limit(limit)
    results = ctx.pipeline.search_by_name(pattern, limit)
    return _format_success(results)


def handle_search_by_type(ctx: Any, *, type_expr: str, limit: int) -> dict:
    """Handle search_by_type tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        type_expr = validate_string(type_expr)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "type_expr must be a non-empty string.")
    limit = validate_limit(limit)
    results = ctx.pipeline.search_by_type(type_expr, limit)
    return _format_success(results)


def handle_search_by_structure(ctx: Any, *, expression: str, limit: int) -> dict:
    """Handle search_by_structure tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        expression = validate_string(expression)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "expression must be a non-empty string.")
    limit = validate_limit(limit)
    try:
        results = ctx.pipeline.search_by_structure(expression, limit)
    except Exception as exc:
        return format_error(PARSE_ERROR, f"Failed to parse expression: {exc}")
    return _format_success(results)


def handle_search_by_symbols(ctx: Any, *, symbols: list[str], limit: int) -> dict:
    """Handle search_by_symbols tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        symbols = validate_symbols(symbols)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "symbols must be a non-empty list of non-empty strings.")
    limit = validate_limit(limit)
    results = ctx.pipeline.search_by_symbols(symbols, limit)
    return _format_success(results)


def handle_get_lemma(ctx: Any, *, name: str) -> dict:
    """Handle get_lemma tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        name = validate_string(name)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "name must be a non-empty string.")
    result = ctx.pipeline.get_lemma(name)
    if result is None:
        return format_error(NOT_FOUND, f"Declaration {name} not found in the index.")
    return _format_success(result)


def handle_find_related(ctx: Any, *, name: str, relation: str, limit: int) -> dict:
    """Handle find_related tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    try:
        name = validate_string(name)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "name must be a non-empty string.")
    try:
        relation = validate_relation(relation)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, f"Invalid relation '{relation}'.")
    limit = validate_limit(limit)
    result = ctx.pipeline.find_related(name, relation, limit=limit)
    if result is None:
        return format_error(NOT_FOUND, f"Declaration {name} not found in the index.")
    return _format_success(result)


def handle_list_modules(ctx: Any, *, prefix: str) -> dict:
    """Handle list_modules tool call."""
    index_err = _check_index(ctx)
    if index_err is not None:
        return index_err
    results = ctx.pipeline.list_modules(prefix)
    return _format_success(results)


# ---------------------------------------------------------------------------
# Proof interaction handlers (Spec §4.3)
# ---------------------------------------------------------------------------

def _session_error_response(exc: SessionError) -> dict:
    """Translate a SessionError into an MCP error response."""
    return format_error(exc.code, exc.message)


async def handle_open_proof_session(
    ctx: Any, *, file_path: str, proof_name: str,
) -> dict:
    """Handle open_proof_session tool call."""
    try:
        file_path = validate_string(file_path)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "file_path must be a non-empty string.")
    try:
        proof_name = validate_string(proof_name)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "proof_name must be a non-empty string.")
    try:
        session_id, state = await ctx.session_manager.create_session(file_path, proof_name)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success({"session_id": session_id, "state": _serialize(state)})


async def handle_close_proof_session(ctx: Any, *, session_id: str) -> dict:
    """Handle close_proof_session tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        await ctx.session_manager.close_session(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success({"closed": True})


async def handle_list_proof_sessions(ctx: Any) -> dict:
    """Handle list_proof_sessions tool call."""
    sessions = await ctx.session_manager.list_sessions()
    return _format_success(sessions)


async def handle_observe_proof_state(ctx: Any, *, session_id: str) -> dict:
    """Handle observe_proof_state tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        state = await ctx.session_manager.observe_state(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(state)


async def handle_get_proof_state_at_step(
    ctx: Any, *, session_id: str, step: int,
) -> dict:
    """Handle get_proof_state_at_step tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        state = await ctx.session_manager.get_state_at_step(session_id, step)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(state)


async def handle_extract_proof_trace(ctx: Any, *, session_id: str) -> dict:
    """Handle extract_proof_trace tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        trace = await ctx.session_manager.extract_trace(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(trace)


async def handle_submit_tactic(
    ctx: Any, *, session_id: str, tactic: str,
) -> dict:
    """Handle submit_tactic tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        tactic = validate_string(tactic)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "tactic must be a non-empty string.")
    try:
        state = await ctx.session_manager.submit_tactic(session_id, tactic)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(state)


async def handle_step_backward(ctx: Any, *, session_id: str) -> dict:
    """Handle step_backward tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        state = await ctx.session_manager.step_backward(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(state)


async def handle_step_forward(ctx: Any, *, session_id: str) -> dict:
    """Handle step_forward tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        tactic, state = await ctx.session_manager.step_forward(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success({"tactic": tactic, "state": _serialize(state)})


async def handle_submit_tactic_batch(
    ctx: Any, *, session_id: str, tactics: list[str],
) -> dict:
    """Handle submit_tactic_batch tool call (P1)."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    if not tactics:
        return format_error(PARSE_ERROR, "tactics must be a non-empty list.")
    try:
        results = await ctx.session_manager.submit_tactic_batch(session_id, tactics)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(results)


async def handle_get_proof_premises(ctx: Any, *, session_id: str) -> dict:
    """Handle get_proof_premises tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        annotations = await ctx.session_manager.get_premises(session_id)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(annotations)


async def handle_get_step_premises(
    ctx: Any, *, session_id: str, step: int,
) -> dict:
    """Handle get_step_premises tool call."""
    try:
        session_id = validate_string(session_id)
    except (ValueError, Exception):
        return format_error(PARSE_ERROR, "session_id must be a non-empty string.")
    try:
        annotation = await ctx.session_manager.get_step_premises(session_id, step)
    except SessionError as exc:
        return _session_error_response(exc)
    return _format_success(annotation)

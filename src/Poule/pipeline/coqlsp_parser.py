"""CoqLspParser — CoqParser implementation using coq-lsp over LSP JSON-RPC.

Spawns ``coq-lsp`` as a subprocess and communicates via Content-Length
framed JSON-RPC messages.  For each ``parse()`` call it opens a synthetic
document containing ``Check <expression>.``, waits for diagnostics, queries
``proof/goals`` for the structured output, and converts it to a ``ConstrNode``
via ``parse_constr_json``.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from Poule.extraction.constr_parser import parse_constr_json
from Poule.pipeline.parser import ParseError

logger = logging.getLogger(__name__)


class CoqLspParser:
    """CoqParser implementation backed by a ``coq-lsp`` subprocess.

    The subprocess is spawned lazily on the first ``parse()`` call and
    kept alive until ``close()`` is called.
    """

    def __init__(self) -> None:
        self._proc: subprocess.Popen[bytes] | None = None
        self._next_id: int = 0
        self._next_uri_id: int = 0
        self._notification_buffer: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # LSP message framing
    # ------------------------------------------------------------------

    def _write_message(self, msg: dict[str, Any]) -> None:
        """Encode and write a JSON-RPC message with Content-Length header."""
        assert self._proc is not None and self._proc.stdin is not None
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self._proc.stdin.write(header + body)
        self._proc.stdin.flush()

    def _read_message(self) -> dict[str, Any]:
        """Read one Content-Length framed JSON-RPC message from stdout."""
        assert self._proc is not None and self._proc.stdout is not None
        stdout = self._proc.stdout
        headers: dict[str, str] = {}
        while True:
            line = stdout.readline()
            if not line:
                raise ParseError(
                    "coq-lsp closed stdout unexpectedly (process may have crashed)"
                )
            line_str = line.decode("ascii").rstrip("\r\n")
            if not line_str:
                break
            if ":" in line_str:
                key, val = line_str.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        if "content-length" not in headers:
            raise ParseError("Missing Content-Length header from coq-lsp")

        content_length = int(headers["content-length"])
        body = stdout.read(content_length)
        return json.loads(body)

    # ------------------------------------------------------------------
    # JSON-RPC helpers
    # ------------------------------------------------------------------

    def _send_request(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for the matching response."""
        self._next_id += 1
        request_id = self._next_id
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self._write_message(request)

        while True:
            msg = self._read_message()
            if "id" in msg and msg["id"] == request_id:
                if "error" in msg:
                    raise ParseError(
                        f"coq-lsp error: {msg['error'].get('message', msg['error'])}"
                    )
                return msg.get("result", {})
            # Buffer notifications and other messages
            self._notification_buffer.append(msg)

    def _send_notification(
        self, method: str, params: dict[str, Any]
    ) -> None:
        """Send a JSON-RPC notification (no id, no response expected)."""
        notification: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._write_message(notification)

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def _open_document(self, uri: str, text: str) -> None:
        """Send textDocument/didOpen notification."""
        self._send_notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "coq",
                    "version": 1,
                    "text": text,
                }
            },
        )

    def _close_document(self, uri: str) -> None:
        """Send textDocument/didClose notification."""
        self._send_notification(
            "textDocument/didClose",
            {"textDocument": {"uri": uri}},
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _wait_for_diagnostics(self, uri: str) -> list[dict[str, Any]]:
        """Read messages until publishDiagnostics arrives for *uri*."""
        # Check buffer first
        remaining: list[dict[str, Any]] = []
        for msg in self._notification_buffer:
            if (
                msg.get("method") == "textDocument/publishDiagnostics"
                and msg["params"]["uri"] == uri
            ):
                self._notification_buffer = remaining
                return msg["params"]["diagnostics"]
            remaining.append(msg)
        self._notification_buffer = remaining

        # Read from the wire
        while True:
            msg = self._read_message()
            if (
                msg.get("method") == "textDocument/publishDiagnostics"
                and msg["params"]["uri"] == uri
            ):
                return msg["params"]["diagnostics"]
            self._notification_buffer.append(msg)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _ensure_started(self) -> None:
        """Start coq-lsp if it is not already running."""
        if self._proc is not None:
            # Check that the process is still alive
            if self._proc.poll() is None:
                return
            # Process died — clean up and restart
            self._proc = None

        try:
            self._proc = subprocess.Popen(
                ["coq-lsp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise ParseError(f"coq-lsp not found on PATH: {exc}") from exc

        # LSP initialize handshake
        self._send_request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": None,
                "capabilities": {},
            },
        )
        self._send_notification("initialized", {})

    def _next_uri(self) -> str:
        """Generate a unique URI for a synthetic query document."""
        uri = f"file:///tmp/poule_parser_{self._next_uri_id}.v"
        self._next_uri_id += 1
        return uri

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, expression: str) -> Any:
        """Parse a Coq expression into a ConstrNode.

        Lazily starts coq-lsp on the first call.  Sends ``Check <expression>.``
        to coq-lsp and converts the resulting Constr.t JSON into a ConstrNode.

        Raises ParseError on failure.
        """
        self._ensure_started()

        uri = self._next_uri()
        text = f"Check {expression}."
        self._open_document(uri, text)

        try:
            diags = self._wait_for_diagnostics(uri)

            # Check for error diagnostics (severity 1 = error)
            errors = [d for d in diags if d.get("severity") == 1]
            if errors:
                error_messages = "; ".join(
                    d.get("message", "unknown error") for d in errors
                )
                raise ParseError(
                    f"Coq rejected expression: {error_messages}"
                )

            # Query proof/goals to get the structured output
            goals_result = self._send_request(
                "proof/goals",
                {
                    "textDocument": {"uri": uri},
                    "position": {"line": 0, "character": 0},
                },
            )

            messages = goals_result.get("messages", [])
            if not messages:
                raise ParseError(
                    f"No output from coq-lsp for expression: {expression!r}"
                )

            # Find the first non-error message containing structured data
            for msg in messages:
                if msg.get("level") == 1:
                    continue
                # The message may contain the Constr.t as JSON in a
                # structured field, or as text that we need to parse.
                # coq-lsp returns structured JSON when available.
                raw = msg.get("raw")
                if raw is not None and isinstance(raw, (list, dict)):
                    return parse_constr_json(raw)

            # Fallback: no structured data found in messages
            # Collect text output for a useful error message
            texts = [
                m["text"] for m in messages if m.get("level", 3) != 1
            ]
            if not texts:
                raise ParseError(
                    f"No parseable output from coq-lsp for: {expression!r}"
                )
            raise ParseError(
                f"coq-lsp returned text but no structured Constr.t for: "
                f"{expression!r}. Output: {'; '.join(texts)}"
            )
        finally:
            self._close_document(uri)

    def close(self) -> None:
        """Shut down the coq-lsp subprocess."""
        if self._proc is None:
            return
        try:
            self._send_request("shutdown", {})
            self._send_notification("exit", {})
            self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
                self._proc.wait(timeout=5)
            except Exception:
                pass
        finally:
            self._proc = None

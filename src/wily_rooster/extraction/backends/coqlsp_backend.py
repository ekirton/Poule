"""CoqLspBackend — extraction backend using coqtop subprocess.

Communicates with ``coqtop -q`` over stdin/stdout to inspect compiled
``.vo`` files and extract declaration data.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from wily_rooster.extraction.errors import BackendCrashError, ExtractionError

logger = logging.getLogger(__name__)

# Sentinel string appended after each command so we can reliably detect
# where coqtop's response ends.
_SENTINEL = "(*WILY_ROOSTER_SENTINEL*)"
_SENTINEL_ECHO = "Error: Syntax error: illegal begin of vernac."

# Regex for parsing ``Search`` output lines.
# Each result looks like: ``name : type_signature``
_SEARCH_LINE_RE = re.compile(r"^(\S+)\s*:\s*(.+)$")

# Regex for parsing ``About`` output to extract the declaration kind.
_ABOUT_KIND_RE = re.compile(
    r"^(\S+)\s+is\s+(?:a\s+)?(.+?)(?:\.|$)", re.MULTILINE
)

# Regex for parsing ``Print Assumptions`` output.
_ASSUMPTION_RE = re.compile(r"^\s*(\S+)\s*:\s*(.+)$", re.MULTILINE)

# Regex for the coqc version string.
_VERSION_RE = re.compile(r"version\s+([\d.]+)")


def _vo_to_logical_path(vo_path: Path) -> str:
    """Derive a candidate logical path from a ``.vo`` file path.

    This is a heuristic: it takes the stem parts after a ``theories`` or
    ``user-contrib`` directory and joins them with dots.  For user
    projects it falls back to the file stem.
    """
    parts = vo_path.parts
    # Look for "theories" (stdlib) or "user-contrib" (opam packages)
    for marker_idx, part in enumerate(parts):
        if part == "theories":
            relevant = parts[marker_idx + 1 :]
            break
        if part == "user-contrib":
            relevant = parts[marker_idx + 1 :]
            break
    else:
        # Fallback: use last two path components (package.Module)
        relevant = parts[-2:] if len(parts) >= 2 else parts

    # Strip the .vo extension from the last element
    module_parts = [
        p[: -len(".vo")] if p.endswith(".vo") else p for p in relevant
    ]
    return ".".join(module_parts)


class CoqLspBackend:
    """Extraction backend that shells out to ``coqtop``.

    Despite the name (kept for compatibility with the task plan), this
    backend drives ``coqtop -q`` rather than coq-lsp, because coqtop
    provides a simpler interface for the bulk-extraction commands we
    need (``Search``, ``Print``, ``Check``, ``Print Assumptions``).

    Lifecycle
    ---------
    1. Call :meth:`start` to spawn the ``coqtop`` subprocess.
    2. Use the query methods (:meth:`list_declarations`, etc.).
    3. Call :meth:`stop` to terminate the subprocess.

    The class also works as a context manager::

        with CoqLspBackend() as backend:
            decls = backend.list_declarations(vo_path)
    """

    def __init__(self) -> None:
        self._proc: subprocess.Popen[str] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn the ``coqtop`` subprocess."""
        if self._proc is not None:
            return
        try:
            self._proc = subprocess.Popen(
                ["coqtop", "-q"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError as exc:
            raise ExtractionError(
                f"coqtop not found on PATH: {exc}"
            ) from exc
        # Read any initial banner/prompt that coqtop might emit
        self._read_until_prompt()

    def stop(self) -> None:
        """Terminate the ``coqtop`` subprocess gracefully."""
        if self._proc is None:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.write("Quit.\n")
                self._proc.stdin.flush()
            self._proc.wait(timeout=5)
        except Exception:
            self._proc.kill()
            self._proc.wait(timeout=5)
        finally:
            self._proc = None

    def __enter__(self) -> CoqLspBackend:
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Backend protocol
    # ------------------------------------------------------------------

    def detect_version(self) -> str:
        """Return the Coq version string (e.g. ``"8.19.0"``)."""
        try:
            result = subprocess.run(
                ["coqc", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError as exc:
            raise ExtractionError(
                f"coqc not found on PATH: {exc}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ExtractionError(
                f"coqc --version timed out: {exc}"
            ) from exc

        match = _VERSION_RE.search(result.stdout)
        if match:
            return match.group(1)

        # Fallback: return the raw first line stripped
        first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        if first_line:
            return first_line
        raise ExtractionError(
            f"Could not parse Coq version from coqc output: {result.stdout!r}"
        )

    def list_declarations(
        self, vo_path: Path
    ) -> list[tuple[str, str, Any]]:
        """List declarations from a compiled ``.vo`` file.

        Returns a list of ``(name, kind, constr_t)`` tuples.  The
        ``constr_t`` value is a placeholder dict with available metadata
        since ``coqtop`` does not expose raw ``Constr.t`` terms.
        """
        self._ensure_alive()

        logical_path = _vo_to_logical_path(vo_path)
        parent_dir = str(vo_path.parent)

        # Add the directory to the load path so Require can find the .vo
        self._send_command(f'Add LoadPath "{parent_dir}" as {logical_path.rsplit(".", 1)[0] if "." in logical_path else logical_path}.')

        # Require the module
        require_resp = self._send_command(f"Require Import {logical_path}.")
        if "Error" in require_resp:
            logger.warning(
                "Failed to Require Import %s: %s", logical_path, require_resp
            )
            return []

        # Search for all declarations inside the module
        search_resp = self._send_command(f"Search _ inside {logical_path}.")

        declarations: list[tuple[str, str, Any]] = []
        for line in search_resp.splitlines():
            line = line.strip()
            if not line:
                continue
            match = _SEARCH_LINE_RE.match(line)
            if match:
                name = match.group(1)
                type_sig = match.group(2)
                # Determine the kind via About
                kind = self._get_declaration_kind(name)
                constr_t: dict[str, Any] = {
                    "name": name,
                    "type_signature": type_sig,
                    "source": "coqtop",
                }
                declarations.append((name, kind, constr_t))

        return declarations

    def pretty_print(self, name: str) -> str:
        """Return the human-readable statement of a declaration."""
        self._ensure_alive()
        response = self._send_command(f"Print {name}.")
        if "Error" in response:
            raise ExtractionError(
                f"pretty_print failed for {name!r}: {response}"
            )
        return response.strip()

    def pretty_print_type(self, name: str) -> str | None:
        """Return the type signature of a declaration, or ``None``."""
        self._ensure_alive()
        response = self._send_command(f"Check {name}.")
        if "Error" in response:
            logger.warning("pretty_print_type failed for %s: %s", name, response)
            return None
        return response.strip() or None

    def get_dependencies(
        self, name: str
    ) -> list[tuple[str, str]]:
        """Return dependency pairs ``(target_name, relation)``."""
        self._ensure_alive()
        response = self._send_command(f"Print Assumptions {name}.")

        if "Closed under the global context" in response:
            return []

        deps: list[tuple[str, str]] = []
        for match in _ASSUMPTION_RE.finditer(response):
            dep_name = match.group(1)
            deps.append((dep_name, "assumes"))

        return deps

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_alive(self) -> None:
        """Raise if the subprocess is not running."""
        if self._proc is None:
            raise ExtractionError("CoqLspBackend has not been started")
        if self._proc.poll() is not None:
            exit_code = self._proc.returncode
            stderr = ""
            if self._proc.stderr:
                try:
                    stderr = self._proc.stderr.read()
                except Exception:
                    pass
            self._proc = None
            raise BackendCrashError(
                f"coqtop exited unexpectedly (exit code {exit_code}). "
                f"stderr: {stderr!r}"
            )

    def _send_command(self, command: str) -> str:
        """Send a vernacular command to coqtop and return the response.

        We append a deliberately malformed comment after the real command
        so that coqtop emits a known error string, which we use as a
        delimiter to know when the response is complete.
        """
        assert self._proc is not None
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None

        # Send the real command followed by the sentinel
        try:
            self._proc.stdin.write(command + "\n")
            self._proc.stdin.write(_SENTINEL + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise BackendCrashError(
                f"Failed to write to coqtop stdin: {exc}"
            ) from exc

        return self._read_until_sentinel()

    def _read_until_sentinel(self) -> str:
        """Read coqtop stdout until the sentinel error appears."""
        assert self._proc is not None
        assert self._proc.stdout is not None

        lines: list[str] = []
        while True:
            try:
                line = self._proc.stdout.readline()
            except Exception as exc:
                raise BackendCrashError(
                    f"Failed to read from coqtop stdout: {exc}"
                ) from exc

            if not line:
                # EOF — process likely died
                raise BackendCrashError(
                    "coqtop closed stdout unexpectedly (process may have crashed)"
                )

            # The sentinel produces a known error — stop when we see it
            if _SENTINEL_ECHO in line or _SENTINEL in line:
                break
            lines.append(line)

        return "".join(lines)

    def _read_until_prompt(self) -> str:
        """Read any initial output from coqtop (banner, etc.).

        Since coqtop -q suppresses the banner, this typically returns
        quickly.  We send a no-op sentinel to flush the stream.
        """
        if self._proc is None:
            return ""
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None

        try:
            self._proc.stdin.write(_SENTINEL + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError):
            return ""

        return self._read_until_sentinel()

    def _get_declaration_kind(self, name: str) -> str:
        """Use ``About`` to determine the kind of a declaration."""
        response = self._send_command(f"About {name}.")
        match = _ABOUT_KIND_RE.search(response)
        if match:
            raw_kind = match.group(2).strip().lower()
            # Normalize common About output to kind_mapping keys
            kind_map: dict[str, str] = {
                "lemma": "lemma",
                "theorem": "theorem",
                "definition": "definition",
                "inductive": "inductive",
                "record": "record",
                "class": "class",
                "constructor": "constructor",
                "instance": "instance",
                "axiom": "axiom",
                "parameter": "parameter",
                "conjecture": "conjecture",
                "coercion": "coercion",
                "canonical structure": "canonical structure",
                "notation": "notation",
                "abbreviation": "abbreviation",
                "section variable": "section variable",
            }
            for key, value in kind_map.items():
                if key in raw_kind:
                    return value
            logger.warning(
                "Unknown declaration kind for %s: %r", name, raw_kind
            )
            return raw_kind
        logger.warning("Could not determine kind for %s from About output", name)
        return "definition"  # conservative fallback

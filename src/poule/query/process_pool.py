"""Standalone Coq process pool for session-free query execution."""

from __future__ import annotations

import asyncio


# Default prelude to load the standard library into session-free processes.
# Spec 4.3.2: "execute against the default global environment (standard library
# and project-level imports configured for the MCP server)."
_DEFAULT_PRELUDE = "From Stdlib Require Import Arith.\n"


class ProcessPool:
    """Pool of standalone Coq processes for session-free vernacular queries.

    Each invocation uses one process; no shared state between invocations.
    The process is acquired before command execution and released after output
    is received.
    """

    def __init__(self, timeout: float = 30.0, prelude: str = _DEFAULT_PRELUDE) -> None:
        self._timeout = timeout
        self._prelude = prelude

    async def send_command(self, command: str) -> str:
        """Send a vernacular command string to a standalone Coq process.

        Args:
            command: The full Coq vernacular string (e.g. "Check nat.").

        Returns:
            The raw Coq output string.

        Raises:
            RuntimeError: If the Coq backend process crashes or times out.
        """
        proc = await asyncio.create_subprocess_exec(
            "coqtop", "-quiet",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Prepend the prelude so the standard library is available,
        # then send the actual command.
        payload = (self._prelude + command + "\n").encode()
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=payload),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("coqtop process timed out")

        if proc.returncode != 0:
            msg = stderr.decode().strip() if stderr else "unknown error"
            raise RuntimeError(f"coqtop exited with code {proc.returncode}: {msg}")

        return stdout.decode()

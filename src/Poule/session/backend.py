"""Coq Proof Backend — per-session coqtop process wrapper.

Implements the CoqBackend protocol defined in specification/coq-proof-backend.md.
Each instance wraps a single coqtop process for interactive proof exploration.
Communication uses stdin/stdout with sentinel-based output framing.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from Poule.session.coqtop_parser import parse_coqtop_goals
from Poule.session.premise_resolution import (
    extract_constants_from_proof_term,
    resolve_step_premises,
)
from Poule.session.types import (
    Goal,
    Hypothesis,
    ProofState,
)

logger = logging.getLogger(__name__)

_SENTINEL = "__POULE_BACKEND_SENTINEL__"


def _extract_goal_type(stmt: str) -> str:
    """Extract the goal type from a theorem statement.

    Given ``Lemma name [params] : type.``, returns ``type``
    (everything after the colon that follows the name/params, without
    the trailing period).
    """
    # Find the first " : " that is at the top level (not inside parens/braces)
    depth = 0
    i = 0
    while i < len(stmt):
        ch = stmt[i]
        if ch in '({':
            depth += 1
        elif ch in ')}':
            depth -= 1
        elif ch == ':' and depth == 0 and i > 0 and stmt[i - 1] == ' ':
            # Check it's " : " not ":=" or part of a name
            if i + 1 < len(stmt) and stmt[i + 1] in ' \n':
                goal_type = stmt[i + 1:].strip()
                # Remove trailing period
                if goal_type.endswith('.'):
                    goal_type = goal_type[:-1].strip()
                return goal_type
        i += 1
    return ""

# Regex to split a proof body into individual tactic sentences (fallback).
# A Coq sentence ends with a period followed by whitespace or end-of-string.
# Periods inside qualified names (e.g., Nat.add_comm) are NOT sentence terminators
# because they are followed by a letter/digit, not whitespace.
# NOTE: This regex cannot handle bullets, braces, comments, or numeric literals.
# The primary path uses the tactic_splitter module for better splitting.
_TACTIC_RE = re.compile(r"(?:[^.]|\.(?=[a-zA-Z0-9_]))*\.\s*")


@dataclass
class _CachedState:
    """Cached proof state and proof term at a step."""
    proof_state: ProofState
    proof_term: str


class CoqProofBackend:
    """Async wrapper around a single coqtop process for proof interaction.

    Implements the CoqBackend protocol from specification/coq-proof-backend.md.
    Uses coqtop's Show. command for proof state observation and Show Proof.
    for proof term capture, all through a single process.
    """

    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        watchdog_timeout: Optional[float] = None,
    ) -> None:
        self._proc = proc
        self._file_path: Optional[str] = None
        self._shut_down = False
        self.original_script: list[str] = []
        self._watchdog_timeout = watchdog_timeout
        self._tactic_count = 0
        self._loaded_offset = 0  # Tracks how much of the file has been sent
        self._in_proof = False   # Whether coqtop is currently in proof mode

        # Cached states from original script replay
        self.original_states: list[_CachedState] = []

    # ------------------------------------------------------------------
    # coqtop I/O (sentinel-based framing)
    # ------------------------------------------------------------------

    async def _send_and_read(self, command: str) -> str:
        """Send a command to coqtop and read output until sentinel.

        Writes to stdin without awaiting drain(), then reads stdout.
        The event loop flushes the stdin write buffer while we await
        readline(), preventing pipe deadlocks on large commands.
        """
        if self._proc is None or self._proc.stdin is None:
            return ""
        sentinel_cmd = f"Check {_SENTINEL}.\n"
        if not command.endswith("\n"):
            command = command + "\n"
        self._proc.stdin.write(
            (command + sentinel_cmd).encode("utf-8")
        )
        # Do NOT await drain() — the event loop flushes stdin while we
        # read stdout below, preventing pipe deadlocks on large commands.
        return await self._read_until_sentinel()

    async def _read_until_sentinel(
        self, timeout: float = 30.0, max_wait: float = 300.0,
    ) -> str:
        """Read coqtop stdout until the sentinel appears.

        coqtop prefixes output with prompts like 'Rocq < ' or 'name < '.
        We strip these prefixes and collect the actual content.

        Args:
            timeout: Per-readline timeout in seconds.
            max_wait: Maximum total wall-clock time in seconds.
        """
        wt = self._watchdog_timeout
        if wt is not None:
            timeout = wt
            max_wait = max(max_wait, wt * 2)

        output_lines: list[str] = []
        stdout = self._proc.stdout
        deadline = time.monotonic() + max_wait
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    logger.warning(
                        "coqtop read exceeded max_wait of %.0fs", max_wait,
                    )
                    break
                line_bytes = await asyncio.wait_for(
                    stdout.readline(), timeout=min(timeout, remaining),
                )
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace")
                if _SENTINEL in line:
                    # Drain the rest of the sentinel error block
                    try:
                        while True:
                            rest = await asyncio.wait_for(
                                stdout.readline(), timeout=2.0,
                            )
                            if not rest or rest.decode("utf-8", errors="replace").strip() == "":
                                break
                    except asyncio.TimeoutError:
                        pass
                    break
                # Strip coqtop prompt prefixes (e.g., "Rocq < ", "name < ")
                stripped = re.sub(r"^[A-Za-z_][A-Za-z0-9_.']* < ", "", line)
                output_lines.append(stripped)
        except asyncio.TimeoutError:
            raise ConnectionError(
                f"coqtop unresponsive for {timeout}s"
            ) from None
        # Strip trailing sentinel preamble
        while output_lines and (
            "Toplevel input" in output_lines[-1]
            or output_lines[-1].strip().startswith(">")
            or output_lines[-1].strip().startswith("^")
        ):
            output_lines.pop()
        return "".join(output_lines).strip()

    # ------------------------------------------------------------------
    # Static helpers (kept for backward compatibility with tests)
    # ------------------------------------------------------------------

    @staticmethod
    def _short_name(proof_name: str) -> str:
        """Extract the short (unqualified) name from a possibly FQN.

        For ``Coq.Arith.PeanoNat.Nat.add_comm`` returns ``add_comm``.
        For ``add_comm`` returns ``add_comm`` unchanged.
        """
        return proof_name.rsplit(".", 1)[-1] if "." in proof_name else proof_name

    def _extract_tactics_regex(self, text: str, proof_name: str) -> list[str]:
        """Fallback: extract tactic sentences using regex splitting.

        Used when the tactic_splitter module is unavailable or for
        backward compatibility.
        """
        short_name = self._short_name(proof_name)
        decl_pattern = re.compile(
            rf"\b(Lemma|Theorem|Proposition|Corollary|Fact|Remark|Definition|"
            rf"Fixpoint|CoFixpoint|Example|Let|Instance)\s+{re.escape(short_name)}\b"
        )
        decl_match = decl_pattern.search(text)
        if decl_match is None:
            return []

        proof_kw_match = re.search(r"\bProof\s*\.", text[decl_match.start():])

        if proof_kw_match is not None:
            between_text = text[decl_match.end():decl_match.start() + proof_kw_match.start()]
            if re.search(
                r"\b(Lemma|Theorem|Proposition|Corollary|Fact|Remark|Definition|"
                r"Fixpoint|CoFixpoint|Example|Let|Instance)\s+\w+",
                between_text,
            ):
                return []

            body_start = decl_match.start() + proof_kw_match.end()
        else:
            stmt_end = re.search(r"\.\s", text[decl_match.start():])
            if stmt_end is None:
                return []
            body_start = decl_match.start() + stmt_end.end()

        end_match = re.search(
            r"\b(Qed|Defined|Admitted|Abort)\s*\.", text[body_start:]
        )
        if end_match:
            body_text = text[body_start:body_start + end_match.start()].strip()
        else:
            body_text = ""

        if not body_text:
            return []

        # Try the tactic_splitter first
        try:
            from Poule.extraction.tactic_splitter import split_tactics
            result = split_tactics(body_text)
            if result:
                return result
        except ImportError:
            pass

        tactics = _TACTIC_RE.findall(body_text)
        return [t.strip() for t in tactics if t.strip()]

    # ------------------------------------------------------------------
    # CoqBackend protocol (§4.1)
    # ------------------------------------------------------------------

    async def load_file(self, file_path: str) -> None:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self._file_path = str(path)

        # Load the entire file into coqtop. This type-checks everything
        # (imports, definitions, all proofs), making all declarations
        # available for subsequent position_at_proof calls.
        text = path.read_text(encoding="utf-8")
        if text.strip():
            result = await self._send_and_read(text)
            if "Error:" in result:
                # Non-fatal: some proofs may fail but we can still extract others.
                # Only raise if the first line fails (imports).
                first_line = text.strip().split("\n")[0]
                if first_line in result:
                    raise RuntimeError(f"Coq check failed: {result}")
                logger.warning("Errors during file load (non-fatal): %s", result[:200])
        self._loaded_offset = len(text)

    async def position_at_proof(self, proof_name: str) -> ProofState:
        if self._file_path is None:
            raise RuntimeError("No file loaded")

        from Poule.session.premise_resolution import _extract_theorem_statement

        text = Path(self._file_path).read_text(encoding="utf-8")

        # If a proof is still open from a previous position_at_proof call,
        # abort it before starting the next one.
        if self._in_proof:
            await self._send_and_read("Abort.")
            self._in_proof = False

        # The entire file was already loaded in load_file, so all definitions
        # are available. We enter proof mode via Goal <type> to avoid needing
        # to re-process the theorem statement (which was already Qed'd during
        # load_file).
        stmt = _extract_theorem_statement(self._file_path, proof_name)
        if not stmt:
            raise ValueError(f"Cannot find proof '{proof_name}' in {self._file_path}")

        # Extract the goal type from the theorem statement.
        # Statement format: "Lemma/Theorem name [binders] : type."
        # We need the type part after the first " : " (not in binders).
        goal_type = _extract_goal_type(stmt)
        if not goal_type:
            raise ValueError(f"Cannot parse goal type from '{stmt[:100]}'")

        # Enter proof mode via Goal <type>.
        result = await self._send_and_read(f"Goal {goal_type}.")
        if "Error:" in result:
            raise ValueError(f"Cannot start proof '{proof_name}': {result}")

        # Enter proof mode
        await self._send_and_read("Proof.")

        # Set Printing All for premise resolution
        await self._send_and_read("Set Printing All.")

        # Get initial proof state (with Printing All for premise resolution)
        show_output_pa = await self._send_and_read("Show Proof.")

        # Also get human-readable state
        await self._send_and_read("Unset Printing All.")
        show_output = await self._send_and_read("Show.")
        initial_state = parse_coqtop_goals(show_output, step_index=0)

        # Extract tactic script
        self.original_script = self._extract_tactics_regex(text, proof_name)

        # Cache initial state
        self.original_states = [_CachedState(
            proof_state=initial_state,
            proof_term=show_output_pa,
        )]

        # Replay original script with Printing All for proof terms
        await self._send_and_read("Set Printing All.")
        self._tactic_count = 0
        for tac in self.original_script:
            result = await self._send_and_read(tac)
            if "Error:" in result:
                break

            self._tactic_count += 1
            proof_term = await self._send_and_read("Show Proof.")

            # Get human-readable state for caching
            await self._send_and_read("Unset Printing All.")
            show_output = await self._send_and_read("Show.")
            state = parse_coqtop_goals(show_output, step_index=self._tactic_count)
            await self._send_and_read("Set Printing All.")

            self.original_states.append(_CachedState(
                proof_state=state,
                proof_term=proof_term,
            ))

        await self._send_and_read("Unset Printing All.")

        # Undo all replayed tactics so interactive use starts at step 0
        replayed = self._tactic_count
        if replayed > 0:
            for _ in range(replayed):
                await self._send_and_read("Undo.")
        self._tactic_count = 0

        # Mark that we're in proof mode. The next position_at_proof call
        # will abort before entering the new proof.
        self._in_proof = True

        return initial_state

    async def execute_tactic(self, tactic: str) -> ProofState:
        if self._shut_down:
            raise RuntimeError("Backend has been shut down")

        result = await self._send_and_read(tactic)
        if "Error:" in result:
            raise RuntimeError(f"Tactic failed: {result}")

        self._tactic_count += 1

        show_output = await self._send_and_read("Show.")
        state = parse_coqtop_goals(show_output, step_index=self._tactic_count)
        return state

    async def get_proof_state(self) -> ProofState:
        show_output = await self._send_and_read("Show.")
        return parse_coqtop_goals(show_output, step_index=self._tactic_count)

    async def get_current_state(self) -> ProofState:
        """Alias for get_proof_state (backward compatibility)."""
        return await self.get_proof_state()

    async def get_proof_term(self) -> str:
        try:
            return await self._send_and_read("Show Proof.")
        except Exception:
            return ""

    async def undo(self) -> None:
        if self._tactic_count <= 0:
            return
        await self._send_and_read("Undo.")
        self._tactic_count -= 1

    def get_rss_bytes(self) -> int:
        """Return the coqtop child process RSS in bytes, or 0 on failure."""
        if self._proc.pid is None:
            return 0
        try:
            with open(f"/proc/{self._proc.pid}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) * 1024
        except (OSError, ValueError):
            pass
        return 0

    async def get_premises(self) -> list[list[dict[str, str]]]:
        """Return per-step premise annotations via proof term diffing.

        Uses the cached proof terms from original_states to diff constants
        at each step.
        """
        if len(self.original_states) < 2:
            return []

        per_step: list[list[dict[str, str]]] = []
        prev_constants = extract_constants_from_proof_term(
            self.original_states[0].proof_term
        )
        for cached in self.original_states[1:]:
            step_premises = resolve_step_premises(
                len(per_step) + 1,
                prev_constants,
                cached.proof_term,
            )
            per_step.append(step_premises)
            prev_constants = extract_constants_from_proof_term(cached.proof_term)

        return per_step

    async def get_premises_at_step(self, step: int) -> list[dict[str, str]]:
        """Return premises for a specific step (backward compatibility)."""
        premises = await self.get_premises()
        if step < 1 or step > len(premises):
            return []
        return premises[step - 1]

    async def submit_command(self, command: str) -> str:
        """Send a vernacular command and return the output."""
        return await self._send_and_read(command)

    async def execute_vernacular(self, command: str) -> str:
        """Alias for submit_command (backward compatibility)."""
        return await self.submit_command(command)

    async def shutdown(self) -> None:
        if self._shut_down:
            return
        self._shut_down = True

        if self._proc.returncode is not None:
            return

        try:
            self._proc.stdin.close()
            self._proc.kill()
            await self._proc.wait()
        except Exception:
            try:
                self._proc.kill()
                await self._proc.wait()
            except Exception:
                pass


# ------------------------------------------------------------------
# Factory (§4.2)
# ------------------------------------------------------------------


async def create_coq_backend(
    file_path: str,
    watchdog_timeout: Optional[float] = None,
    load_paths: Optional[list[tuple[str, str]]] = None,
) -> CoqProofBackend:
    """Spawn a coqtop process and return a connected CoqProofBackend.

    Per spec §4.2: the factory is the only way to create backend instances.

    When *load_paths* is provided, each ``(directory, logical_prefix)``
    tuple is passed as a ``-R`` flag to coqtop so that bare
    ``Require Import`` directives resolve correctly.
    """
    args: list[str] = ["coqtop", "-quiet"]
    for directory, prefix in (load_paths or []):
        args.extend(["-R", directory, prefix])
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"coqtop not found on PATH: {exc}"
        ) from exc

    backend = CoqProofBackend(proc, watchdog_timeout=watchdog_timeout)

    # Drain any startup output
    backend._proc.stdin.write(f"Check {_SENTINEL}.\n".encode("utf-8"))
    await backend._read_until_sentinel()

    return backend

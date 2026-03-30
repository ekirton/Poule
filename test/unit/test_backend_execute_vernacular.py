"""Unit tests for vernacular command output capture in proof sessions.

With the coqtop backend, vernacular output capture is native — coqtop
returns the output of Print/Check/About commands directly on stdout.
The session manager routes through the backend's submit_command method.

This file tests:
1. CoqProofBackend.execute_vernacular / submit_command — alias for _send_and_read
2. SessionManager.send_command — routing through backend
3. _extract_imports — import extraction from .v files
4. _extract_file_prelude — file prelude extraction

Spec: specification/coq-proof-backend.md
      specification/proof-session.md (§4.4 submit_command)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. CoqProofBackend.submit_command — coqtop native output
# ---------------------------------------------------------------------------

class TestCoqtopVernacularOutput:
    """coqtop backend natively captures vernacular command output."""

    @pytest.mark.asyncio
    async def test_submit_command_calls_send_and_read(self):
        """submit_command delegates to _send_and_read."""
        from Poule.session.backend import CoqProofBackend

        backend = CoqProofBackend.__new__(CoqProofBackend)
        backend._proc = MagicMock()
        backend._proc.returncode = None
        backend._shut_down = False
        backend._watchdog_timeout = None
        backend._send_and_read = AsyncMock(return_value="Inductive nat : Set := O : nat | S : nat -> nat.")

        result = await backend.submit_command("Print nat.")

        backend._send_and_read.assert_called_once_with("Print nat.")
        assert "Inductive nat" in result

    @pytest.mark.asyncio
    async def test_execute_vernacular_is_alias(self):
        """execute_vernacular is backward-compatible alias for submit_command."""
        from Poule.session.backend import CoqProofBackend

        backend = CoqProofBackend.__new__(CoqProofBackend)
        backend._proc = MagicMock()
        backend._proc.returncode = None
        backend._shut_down = False
        backend._watchdog_timeout = None
        backend._send_and_read = AsyncMock(return_value="output")

        result = await backend.execute_vernacular("Check nat.")

        assert result == "output"


# ---------------------------------------------------------------------------
# 2. _extract_imports
# ---------------------------------------------------------------------------

class TestExtractImports:
    """_extract_imports extracts Require/Import lines from .v files."""

    def test_extracts_from_require_import(self, tmp_path):
        from Poule.session.manager import _extract_imports

        v_file = tmp_path / "test.v"
        v_file.write_text(
            "From Coq Require Import PeanoNat.\n"
            "From mathcomp Require Import ssreflect ssrnat.\n"
            "\n"
            "Lemma foo : True.\nProof. exact I. Qed.\n"
        )

        result = _extract_imports(str(v_file))

        assert "From Coq Require Import PeanoNat." in result
        assert "From mathcomp Require Import ssreflect ssrnat." in result
        assert "Lemma" not in result

    def test_extracts_plain_require(self, tmp_path):
        from Poule.session.manager import _extract_imports

        v_file = tmp_path / "test.v"
        v_file.write_text("Require Import Arith.\nLemma x : True. Proof. exact I. Qed.\n")

        result = _extract_imports(str(v_file))

        assert "Require Import Arith." in result

    def test_file_not_found_returns_empty(self):
        from Poule.session.manager import _extract_imports

        result = _extract_imports("/nonexistent/path.v")

        assert result == ""

    def test_no_imports_returns_empty(self, tmp_path):
        from Poule.session.manager import _extract_imports

        v_file = tmp_path / "test.v"
        v_file.write_text("Lemma foo : True. Proof. exact I. Qed.\n")

        result = _extract_imports(str(v_file))

        assert result == ""


# ---------------------------------------------------------------------------
# 2b. _extract_file_prelude
# ---------------------------------------------------------------------------

class TestExtractFilePrelude:
    """_extract_file_prelude loads the entire .v file content.

    Spec §4.4.1: The backend loads the session's file context —
    all vernacular commands from the entire .v file — so that vernacular
    introspection commands can reference any definition in the file.
    """

    def test_loads_entire_file_including_proof_target_and_beyond(self, tmp_path):
        from Poule.session.manager import _extract_file_prelude

        v_file = tmp_path / "test.v"
        v_file.write_text(
            "From Coq Require Import PeanoNat.\n"
            "\n"
            "Lemma helper : forall n, n + 0 = n.\n"
            "Proof. intros n. lia. Qed.\n"
            "\n"
            "Definition double (n : nat) := n + n.\n"
            "\n"
            "Lemma target : forall n, n = n.\n"
            "Proof.\n"
            "  reflexivity.\n"
            "Qed.\n"
            "\n"
            "Lemma after_target : True.\n"
            "Proof. exact I. Qed.\n"
        )

        result = _extract_file_prelude(str(v_file), "target")

        assert "From Coq Require Import PeanoNat." in result
        assert "Lemma helper" in result
        assert "Definition double" in result
        assert "Lemma target" in result
        assert "Lemma after_target" in result

    def test_includes_all_definitions_for_multi_theorem_files(self, tmp_path):
        from Poule.session.manager import _extract_file_prelude

        v_file = tmp_path / "test.v"
        v_file.write_text(
            "Lemma first : True.\n"
            "Proof. exact I. Qed.\n"
            "\n"
            "Lemma second : True.\n"
            "Proof. exact I. Qed.\n"
            "\n"
            "Lemma third : True.\n"
            "Proof. exact I. Qed.\n"
        )

        result = _extract_file_prelude(str(v_file), "first")

        assert "Lemma first" in result
        assert "Lemma second" in result
        assert "Lemma third" in result

    def test_no_proof_name_returns_imports_only(self, tmp_path):
        from Poule.session.manager import _extract_file_prelude

        v_file = tmp_path / "test.v"
        v_file.write_text(
            "From Coq Require Import PeanoNat.\n"
            "Definition foo := 1.\n"
            "Lemma bar : True. Proof. exact I. Qed.\n"
        )

        result = _extract_file_prelude(str(v_file), "")

        assert "From Coq Require Import PeanoNat." in result
        assert "Definition foo" not in result

    def test_proof_name_not_found_returns_all_content(self, tmp_path):
        from Poule.session.manager import _extract_file_prelude

        v_file = tmp_path / "test.v"
        v_file.write_text(
            "From Coq Require Import PeanoNat.\n"
            "Definition foo := 1.\n"
        )

        result = _extract_file_prelude(str(v_file), "nonexistent")

        assert "From Coq Require Import PeanoNat." in result
        assert "Definition foo" in result

    def test_file_not_found_returns_empty(self):
        from Poule.session.manager import _extract_file_prelude

        result = _extract_file_prelude("/nonexistent/path.v", "anything")

        assert result == ""

    def test_loads_entire_file_for_any_keyword(self, tmp_path):
        from Poule.session.manager import _extract_file_prelude

        for keyword in ["Lemma", "Theorem", "Proposition", "Corollary",
                         "Example", "Fact", "Remark"]:
            v_file = tmp_path / f"test_{keyword}.v"
            v_file.write_text(
                "Definition setup := 42.\n"
                f"{keyword} target : True.\n"
                "Proof. exact I. Qed.\n"
                "Definition after := 99.\n"
            )

            result = _extract_file_prelude(str(v_file), "target")

            assert "Definition setup" in result, f"Failed for keyword {keyword}"
            assert f"{keyword} target" in result, f"Failed for keyword {keyword}"
            assert "Definition after" in result, f"Failed for keyword {keyword}"


# ---------------------------------------------------------------------------
# 3. SessionManager.send_command routes through backend
# ---------------------------------------------------------------------------

class TestSendCommandRouting:
    """send_command routes through the backend's submit_command."""

    @pytest.mark.asyncio
    async def test_send_command_uses_backend_submit_command(self):
        """send_command routes through backend.submit_command."""
        from Poule.session.manager import SessionManager

        backend = MagicMock()
        backend.load_file = AsyncMock()
        backend.position_at_proof = AsyncMock(return_value=MagicMock(
            schema_version=1,
            session_id="",
            step_index=0,
            is_complete=False,
            focused_goal_index=0,
            goals=[],
        ))
        backend.shutdown = AsyncMock()
        backend.original_script = []
        backend.submit_command = AsyncMock(return_value="nat : Set")

        mgr = SessionManager(backend_factory=AsyncMock(return_value=backend))
        sid, _ = await mgr.create_session("/file.v", "proof1")

        result = await mgr.send_command(sid, "Check nat.")

        backend.submit_command.assert_called_once_with("Check nat.")
        assert result == "nat : Set"

    @pytest.mark.asyncio
    async def test_submit_vernacular_also_routes_through_backend(self):
        """submit_vernacular routes through backend.submit_command."""
        from Poule.session.manager import SessionManager

        backend = MagicMock()
        backend.load_file = AsyncMock()
        backend.position_at_proof = AsyncMock(return_value=MagicMock(
            schema_version=1,
            session_id="",
            step_index=0,
            is_complete=False,
            focused_goal_index=0,
            goals=[],
        ))
        backend.shutdown = AsyncMock()
        backend.original_script = []
        backend.submit_command = AsyncMock(return_value="output text")

        mgr = SessionManager(backend_factory=AsyncMock(return_value=backend))
        sid, _ = await mgr.create_session("/file.v", "proof1")

        result = await mgr.submit_vernacular(sid, "Print nat.")

        backend.submit_command.assert_called_once_with("Print nat.")
        assert result == "output text"

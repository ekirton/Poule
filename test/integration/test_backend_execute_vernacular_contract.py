"""Contract tests for vernacular command output capture via real session manager.

These tests require coqtop and coq-lsp to be installed.

Spec: specification/coq-proof-backend.md
      specification/proof-session.md
"""

from __future__ import annotations

import pytest


class TestSendCommandContract:
    """Contract tests verifying real session manager returns non-empty output.

    These tests require coqtop and coq-lsp to be installed.
    """

    @pytest.mark.asyncio
    async def test_print_nat_via_submit_vernacular(self):
        """Print nat. via submit_vernacular (prefer_coqtop) returns non-empty output."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        sid, _ = await mgr.create_session(
            "/poule/examples/arith.v", "add_comm",
        )
        try:
            result = await mgr.submit_vernacular(sid, "Print nat.")
            assert isinstance(result, str)
            assert len(result) > 0, "submit_vernacular returned empty for Print nat."
            assert "nat" in result.lower()
        finally:
            await mgr.close_session(sid)

    @pytest.mark.asyncio
    async def test_check_nat_via_submit_vernacular(self):
        """Check nat. via submit_vernacular returns non-empty output."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        sid, _ = await mgr.create_session(
            "/poule/examples/arith.v", "add_comm",
        )
        try:
            result = await mgr.submit_vernacular(sid, "Check nat.")
            assert isinstance(result, str)
            assert len(result) > 0, "submit_vernacular returned empty for Check nat."
        finally:
            await mgr.close_session(sid)

    @pytest.mark.asyncio
    async def test_session_loads_file_imports(self):
        """Queries in a proof session have access to the file's imports."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        # arith.v imports PeanoNat
        sid, _ = await mgr.create_session(
            "/poule/examples/arith.v", "add_comm",
        )
        try:
            result = await mgr.submit_vernacular(sid, "Check Nat.add_comm.")
            assert isinstance(result, str)
            assert len(result) > 0, "Nat.add_comm should be available via PeanoNat import"
        finally:
            await mgr.close_session(sid)

    @pytest.mark.asyncio
    async def test_session_loads_same_file_definitions(self):
        """Spec §4.4.1 step 2: Queries in a proof session have access to
        same-file definitions that precede the proof target.

        Given a session on add_0_r_v3 in algebra.v (which contains my_lemma before it),
        When Check my_lemma. is submitted,
        Then the output contains the type of my_lemma."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        # algebra.v: my_lemma is defined at line 14, add_0_r_v3 starts at line 38
        sid, _ = await mgr.create_session(
            "/poule/examples/algebra.v", "add_0_r_v3",
        )
        try:
            result = await mgr.submit_vernacular(sid, "Check my_lemma.")
            assert isinstance(result, str)
            assert "Error" not in result, (
                f"my_lemma should be available (same-file definition), got: {result}"
            )
            assert len(result) > 0, "Check my_lemma should return its type"
        finally:
            await mgr.close_session(sid)

    @pytest.mark.asyncio
    async def test_session_loads_same_file_definition_in_automation(self):
        """Same-file definitions: double in automation.v."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        # automation.v: double defined at line 26, double_2 at line 39
        sid, _ = await mgr.create_session(
            "/poule/examples/automation.v", "double_2",
        )
        try:
            result = await mgr.submit_vernacular(sid, "About double.")
            assert isinstance(result, str)
            assert "Error" not in result, (
                f"double should be available (same-file definition), got: {result}"
            )
        finally:
            await mgr.close_session(sid)

    @pytest.mark.asyncio
    async def test_send_command_without_prefer_coqtop_uses_lsp(self):
        """send_command (default) falls back to coq-lsp, which returns empty for Print."""
        from Poule.session.manager import SessionManager

        mgr = SessionManager()
        sid, _ = await mgr.create_session(
            "/poule/examples/arith.v", "add_comm",
        )
        try:
            # send_command without prefer_coqtop goes through coq-lsp
            result = await mgr.send_command(sid, "Print nat.")
            assert isinstance(result, str)
            # coq-lsp returns empty for successful Print — this documents the limitation
            assert result == "", "coq-lsp should return empty for Print (no diagnostics)"
        finally:
            await mgr.close_session(sid)

"""Unit tests for backend tactic extraction regex handling.

Tests that _extract_tactics_regex and _extract_tactics_from_spans
correctly handle fully-qualified names (FQN) from the search index
by extracting the short name for regex matching.

Spec: specification/coq-proof-backend.md §original_script
Spec: specification/extraction-campaign.md §4.1 (theorem_name is FQN)
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock

import pytest

from Poule.session.backend import CoqProofBackend


def _make_backend_stub() -> CoqProofBackend:
    """Create a CoqProofBackend with a mocked process (no real coqtop)."""
    proc = MagicMock()
    proc.returncode = None
    backend = CoqProofBackend.__new__(CoqProofBackend)
    backend._proc = proc
    backend._shut_down = False
    backend._file_path = None
    return backend


# ═══════════════════════════════════════════════════════════════════════════
# FQN → short name in _extract_tactics_regex
# ═══════════════════════════════════════════════════════════════════════════


class TestExtractTacticsRegexWithFQN:
    """_extract_tactics_regex must find proof body when proof_name is a
    fully-qualified name from the index (e.g., Coq.Arith.PeanoNat.Nat.add_comm)."""

    def test_fqn_finds_lemma_by_short_name(self):
        """FQN 'Mod.Sub.lemma_name' matches 'Lemma lemma_name' in source."""
        backend = _make_backend_stub()
        text = (
            "Lemma add_comm : forall n m, n + m = m + n.\n"
            "Proof. intros n m. ring. Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "Stdlib.Arith.PeanoNat.Nat.add_comm")
        assert len(tactics) >= 1
        assert any("intros" in t for t in tactics)

    def test_fqn_finds_theorem_by_short_name(self):
        """FQN 'Mod.Sub.thm_name' matches 'Theorem thm_name' in source."""
        backend = _make_backend_stub()
        text = (
            "Theorem foo_bar : True.\n"
            "Proof. exact I. Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "MyLib.Module.foo_bar")
        assert len(tactics) >= 1

    def test_fqn_finds_definition_with_proof(self):
        """FQN matches 'Definition name' when it has a Proof. block."""
        backend = _make_backend_stub()
        text = (
            "Definition decidable_eq : forall x y : nat, {x = y} + {x <> y}.\n"
            "Proof. decide equality. Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "Stdlib.Arith.Decidable.decidable_eq")
        assert len(tactics) >= 1

    def test_short_name_still_works(self):
        """Short name (no dots) continues to work as before."""
        backend = _make_backend_stub()
        text = (
            "Lemma add_comm : forall n m, n + m = m + n.\n"
            "Proof. intros n m. ring. Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "add_comm")
        assert len(tactics) >= 1

    def test_fqn_no_match_returns_empty(self):
        """FQN whose short name doesn't appear in file returns empty list."""
        backend = _make_backend_stub()
        text = "Lemma other : True. Proof. exact I. Qed.\n"
        tactics = backend._extract_tactics_regex(text, "Mod.nonexistent")
        assert tactics == []

    def test_fqn_definition_without_proof_returns_empty(self):
        """A Definition without a Proof. block returns empty list."""
        backend = _make_backend_stub()
        text = "Definition foo := 42.\n"
        tactics = backend._extract_tactics_regex(text, "Mod.foo")
        assert tactics == []

    def test_no_proof_keyword_extracts_tactics(self):
        """Proof without explicit Proof. keyword (old Coq style) extracts tactics.

        Spec: coq-proof-backend.md §original_script — proofs without Proof.
        keyword shall return the tactic list."""
        backend = _make_backend_stub()
        text = (
            "Lemma Iftrue_inv : forall (A B:Prop) (b:bool), IfProp A B b -> b = true -> A.\n"
            "destruct 1; intros; auto with bool.\n"
            "case diff_true_false; auto with bool.\n"
            "Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "Iftrue_inv")
        assert len(tactics) >= 1
        assert any("destruct" in t for t in tactics)

    def test_no_proof_keyword_single_line(self):
        """Proof without Proof. keyword, all on one line after statement."""
        backend = _make_backend_stub()
        text = "Lemma foo : True. exact I. Qed.\n"
        tactics = backend._extract_tactics_regex(text, "foo")
        assert len(tactics) >= 1
        assert any("exact" in t for t in tactics)

    def test_fixpoint_does_not_steal_next_proof(self):
        """Fixpoint without proof body must not capture the next declaration's
        Proof. block (e.g., Fixpoint fact followed by Lemma lt_O_fact)."""
        backend = _make_backend_stub()
        text = (
            "Fixpoint fact (n:nat) : nat :=\n"
            "  match n with\n"
            "    | O => 1\n"
            "    | S n => S n * fact n\n"
            "  end.\n"
            "\n"
            "Lemma lt_O_fact n : 0 < fact n.\n"
            "Proof.\n"
            "  induction n; simpl; auto.\n"
            "Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "Mod.Factorial.fact")
        assert tactics == []

    def test_definition_does_not_steal_next_proof(self):
        """Definition with := must not capture a later declaration's Proof."""
        backend = _make_backend_stub()
        text = (
            "Definition in_int p q r := p <= r /\\ r < q.\n"
            "\n"
            "Lemma in_int_intro : forall p q r, p <= r -> r < q -> in_int p q r.\n"
            "Proof.\n"
            "  split; assumption.\n"
            "Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "Mod.in_int")
        assert tactics == []

    def test_adjacent_lemma_with_proof_still_works(self):
        """A lemma immediately followed by Proof. still extracts correctly."""
        backend = _make_backend_stub()
        text = (
            "Lemma lt_O_fact n : 0 < fact n.\n"
            "Proof.\n"
            "  induction n; simpl; auto.\n"
            "Qed.\n"
        )
        tactics = backend._extract_tactics_regex(text, "lt_O_fact")
        assert len(tactics) >= 1
        assert any("induction" in t for t in tactics)


# _extract_tactics_from_spans tests removed: coq-lsp document model
# is no longer used (coqtop backend migration). Tactic extraction now
# uses regex splitting via _extract_tactics_regex and tactic_splitter.

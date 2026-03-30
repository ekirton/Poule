"""Unit tests for tactic sentence splitting.

Spec: specification/coq-proof-backend.md §4.1 (original_script).
"""

from __future__ import annotations

import pytest

from Poule.extraction.tactic_splitter import split_tactics


class TestBasicSplitting:
    def test_two_tactics(self):
        assert split_tactics("intros n m. ring.") == ["intros n m.", "ring."]

    def test_single_tactic(self):
        assert split_tactics("exact I.") == ["exact I."]

    def test_empty(self):
        assert split_tactics("") == []

    def test_whitespace_only(self):
        assert split_tactics("   \n  ") == []

    def test_multiline(self):
        result = split_tactics("intros n.\n  simpl.\n  reflexivity.")
        assert result == ["intros n.", "simpl.", "reflexivity."]


class TestQualifiedNames:
    def test_qualified_name_not_split(self):
        """Periods in qualified names (Nat.add) are not sentence terminators."""
        result = split_tactics("apply Nat.add_comm.")
        assert result == ["apply Nat.add_comm."]

    def test_rewrite_qualified(self):
        result = split_tactics("rewrite Nat.add_comm. reflexivity.")
        assert result == ["rewrite Nat.add_comm.", "reflexivity."]


class TestBullets:
    def test_simple_bullets(self):
        result = split_tactics("intros.\n- simpl.\n- reflexivity.")
        assert "intros." in result
        assert "-" in result
        assert "simpl." in result
        assert "reflexivity." in result

    def test_double_bullets(self):
        result = split_tactics("-- simpl.\n-- ring.")
        assert "--" in result

    def test_plus_bullet(self):
        result = split_tactics("+ auto.")
        assert "+" in result
        assert "auto." in result

    def test_star_bullet(self):
        result = split_tactics("* trivial.")
        assert "*" in result


class TestBraces:
    def test_braces_are_separate(self):
        result = split_tactics("{ simpl. } { ring. }")
        assert "{" in result
        assert "}" in result
        assert "simpl." in result
        assert "ring." in result


class TestComments:
    def test_period_in_comment_not_split(self):
        result = split_tactics("(* This is a comment. With periods. *) intros.")
        assert result == ["intros."]

    def test_nested_comments(self):
        result = split_tactics("(* outer (* inner. *) still outer. *) auto.")
        assert result == ["auto."]


class TestStrings:
    def test_period_in_string_not_split(self):
        result = split_tactics('idtac "hello. world". reflexivity.')
        assert len(result) == 2
        assert "hello. world" in result[0]


class TestSsreflect:
    def test_semicolons_are_internal(self):
        """Semicolons don't split — only periods do."""
        result = split_tactics("move=> /eqP H; rewrite H.")
        assert result == ["move=> /eqP H; rewrite H."]


class TestEdgeCases:
    def test_trailing_whitespace(self):
        result = split_tactics("intros.   ")
        assert result == ["intros."]

    def test_no_period_at_end(self):
        """Tactic without trailing period is still captured."""
        result = split_tactics("intros")
        assert result == ["intros"]

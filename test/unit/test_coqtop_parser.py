"""Unit tests for coqtop Show. output parser.

Spec: specification/coq-proof-backend.md §4.4 (ProofState Translation).
"""

from __future__ import annotations

import pytest

from Poule.session.coqtop_parser import parse_coqtop_goals


class TestNoGoals:
    def test_no_more_goals(self):
        state = parse_coqtop_goals("No more goals.")
        assert state.is_complete is True
        assert state.goals == []
        assert state.focused_goal_index is None

    def test_no_more_subgoals(self):
        state = parse_coqtop_goals("No more subgoals.")
        assert state.is_complete is True

    def test_empty_string(self):
        state = parse_coqtop_goals("")
        assert state.is_complete is True


class TestSingleGoal:
    def test_simple_goal(self):
        text = (
            "1 goal\n"
            "\n"
            "  ============================\n"
            "  True"
        )
        state = parse_coqtop_goals(text)
        assert state.is_complete is False
        assert len(state.goals) == 1
        assert state.goals[0].type == "True"
        assert state.goals[0].hypotheses == []
        assert state.focused_goal_index == 0

    def test_goal_with_hypotheses(self):
        text = (
            "1 goal\n"
            "\n"
            "  n : nat\n"
            "  m : nat\n"
            "  IHn : n + 0 = n\n"
            "  ============================\n"
            "  S n + 0 = S n"
        )
        state = parse_coqtop_goals(text)
        assert len(state.goals) == 1
        assert state.goals[0].type == "S n + 0 = S n"
        hyps = state.goals[0].hypotheses
        assert len(hyps) == 3
        assert hyps[0].name == "n"
        assert hyps[0].type == "nat"
        assert hyps[1].name == "m"
        assert hyps[1].type == "nat"
        assert hyps[2].name == "IHn"
        assert hyps[2].type == "n + 0 = n"

    def test_multi_name_hypothesis(self):
        text = (
            "1 goal\n"
            "\n"
            "  n, m : nat\n"
            "  ============================\n"
            "  n + m = m + n"
        )
        state = parse_coqtop_goals(text)
        hyps = state.goals[0].hypotheses
        assert len(hyps) == 2
        assert hyps[0].name == "n"
        assert hyps[0].type == "nat"
        assert hyps[1].name == "m"
        assert hyps[1].type == "nat"

    def test_let_bound_hypothesis(self):
        text = (
            "1 goal\n"
            "\n"
            "  x := 5 : nat\n"
            "  ============================\n"
            "  x = 5"
        )
        state = parse_coqtop_goals(text)
        hyps = state.goals[0].hypotheses
        assert len(hyps) == 1
        assert hyps[0].name == "x"
        assert hyps[0].type == "nat"
        assert hyps[0].body == "5"

    def test_multiline_hypothesis_type(self):
        text = (
            "1 goal\n"
            "\n"
            "  H : forall (n : nat),\n"
            "        n + 0 = n\n"
            "  ============================\n"
            "  0 + 0 = 0"
        )
        state = parse_coqtop_goals(text)
        hyps = state.goals[0].hypotheses
        assert len(hyps) == 1
        assert hyps[0].name == "H"
        assert "forall" in hyps[0].type
        assert "n + 0 = n" in hyps[0].type

    def test_step_index(self):
        text = "No more goals."
        state = parse_coqtop_goals(text, step_index=3)
        assert state.step_index == 3


class TestMultipleGoals:
    def test_two_goals(self):
        text = (
            "2 goals\n"
            "\n"
            "  n : nat\n"
            "  ============================\n"
            "  n + 0 = n\n"
            "\n"
            "  ============================\n"
            "  0 + 0 = 0"
        )
        state = parse_coqtop_goals(text)
        assert len(state.goals) == 2
        assert state.goals[0].type == "n + 0 = n"
        assert state.goals[1].type == "0 + 0 = 0"
        # First goal has hypothesis, second may or may not
        assert len(state.goals[0].hypotheses) >= 1

    def test_two_goals_both_with_hyps(self):
        text = (
            "2 goals\n"
            "\n"
            "  n : nat\n"
            "  ============================\n"
            "  n = n\n"
            "\n"
            "  m : nat\n"
            "  ============================\n"
            "  m = m"
        )
        state = parse_coqtop_goals(text)
        assert len(state.goals) == 2
        assert state.goals[0].type == "n = n"
        assert state.goals[1].type == "m = m"
        assert state.goals[0].hypotheses[0].name == "n"
        assert state.goals[1].hypotheses[0].name == "m"


class TestSchemaVersion:
    def test_schema_version_is_1(self):
        state = parse_coqtop_goals("No more goals.")
        assert state.schema_version == 1

    def test_session_id_is_empty(self):
        state = parse_coqtop_goals("No more goals.")
        assert state.session_id == ""

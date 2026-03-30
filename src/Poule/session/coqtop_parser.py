"""Parse coqtop ``Show.`` output into ProofState.

Implements specification/coq-proof-backend.md §4.4 (ProofState Translation).

coqtop's ``Show.`` output has the structure::

    N goal(s)

      h1, h2 : type
      h3 := body : type
      ============================
      goal_type

      ============================
      goal_type_2
"""

from __future__ import annotations

import re

from Poule.session.types import Goal, Hypothesis, ProofState

# Header patterns
_NO_GOALS_RE = re.compile(r"No more (goals|subgoals)")
_GOAL_COUNT_RE = re.compile(r"(\d+) (?:goal|subgoal)")
_SEPARATOR_RE = re.compile(r"^={4,}$")


def parse_coqtop_goals(text: str, step_index: int = 0) -> ProofState:
    """Parse coqtop ``Show.`` output into a ProofState.

    Args:
        text: Raw output from coqtop's ``Show.`` command, with prompts
            already stripped.
        step_index: Step index to assign to the returned ProofState.

    Returns:
        A ProofState reflecting the parsed goals and hypotheses.
    """
    text = text.strip()
    if not text or _NO_GOALS_RE.search(text):
        return ProofState(
            schema_version=1,
            session_id="",
            step_index=step_index,
            is_complete=True,
            focused_goal_index=None,
            goals=[],
        )

    lines = text.split("\n")
    goals = _parse_goals(lines)

    return ProofState(
        schema_version=1,
        session_id="",
        step_index=step_index,
        is_complete=len(goals) == 0,
        focused_goal_index=0 if goals else None,
        goals=goals,
    )


def _parse_goals(lines: list[str]) -> list[Goal]:
    """Parse all goals from Show. output lines."""
    # Skip the header line ("N goal(s)")
    start = 0
    if lines and _GOAL_COUNT_RE.match(lines[0].strip()):
        start = 1

    # Find all separator positions
    sep_positions = []
    for i in range(start, len(lines)):
        if _SEPARATOR_RE.match(lines[i].strip()):
            sep_positions.append(i)

    if not sep_positions:
        return []

    goals = []
    for goal_idx, sep_pos in enumerate(sep_positions):
        # Hypotheses: non-blank lines above this separator
        # For the first goal, hyps start after the header.
        # For subsequent goals, hyps start after the previous goal's type block.
        if goal_idx == 0:
            hyp_start = start
        else:
            # Find first non-blank line after previous goal type block
            prev_goal_type_end = sep_positions[goal_idx - 1] + 1
            # Skip goal type lines and blank lines to find hyp block start
            hyp_start = prev_goal_type_end
            # Actually, for multi-goal output, the structure is:
            # [hyps] ==== [goal_type] (blank) [hyps] ==== [goal_type]
            # We need to find the last contiguous non-blank block before sep_pos

        # Collect hypothesis lines: scan backward from separator to find the
        # contiguous block of hypothesis lines
        hyp_lines = []
        for i in range(hyp_start, sep_pos):
            hyp_lines.append(lines[i])

        # Remove leading blank lines
        while hyp_lines and not hyp_lines[0].strip():
            hyp_lines.pop(0)
        # For goals after the first, remove the previous goal's type lines
        # The previous goal type is separated from current hyps by blank line(s)
        if goal_idx > 0:
            # Find the last blank line, everything after it is the hyp block
            last_blank = -1
            for i, line in enumerate(hyp_lines):
                if not line.strip():
                    last_blank = i
            if last_blank >= 0:
                hyp_lines = hyp_lines[last_blank + 1:]

        # Goal type: lines after the separator until next blank or next separator
        goal_type_lines = []
        next_bound = sep_positions[goal_idx + 1] if goal_idx < len(sep_positions) - 1 else len(lines)
        for i in range(sep_pos + 1, next_bound):
            line = lines[i]
            if not line.strip() and goal_type_lines:
                break
            if line.strip():
                goal_type_lines.append(line.strip())

        hypotheses = _parse_hypotheses(hyp_lines)
        goal_type = " ".join(goal_type_lines)

        goals.append(Goal(
            index=goal_idx,
            type=goal_type,
            hypotheses=hypotheses,
        ))

    return goals


def _parse_hypotheses(lines: list[str]) -> list[Hypothesis]:
    """Parse hypothesis lines into Hypothesis objects.

    Handles:
    - ``n, m : nat`` → two hypotheses
    - ``H := 5 : nat`` → let-bound hypothesis
    - Multi-line types (continuation lines indented further)
    """
    if not lines:
        return []

    # Group continuation lines with their parent
    groups: list[str] = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if groups and indent > _hypothesis_indent(groups[-1]):
            # Continuation of previous hypothesis
            groups[-1] = groups[-1].rstrip() + " " + stripped.strip()
        else:
            groups.append(stripped)

    hypotheses = []
    for group in groups:
        group = group.strip()
        if not group:
            continue

        # Try let-bound: name := body : type
        # Match greedily on body, last " : " is the type separator
        let_match = re.match(r"^(\S+)\s*:=\s*(.+)$", group)
        if let_match:
            name = let_match.group(1)
            rest = let_match.group(2)
            # Find the last " : " to split body from type
            last_colon = rest.rfind(" : ")
            if last_colon >= 0:
                body = rest[:last_colon].strip()
                typ = rest[last_colon + 3:].strip()
                hypotheses.append(Hypothesis(name=name, type=typ, body=body))
                continue

        # Try multi-name: n, m, ... : type
        # Find first " : " that separates names from type
        colon_pos = group.find(" : ")
        if colon_pos == -1:
            continue

        names_part = group[:colon_pos].strip()
        type_part = group[colon_pos + 3:].strip()

        # Split names by comma
        names = [n.strip() for n in names_part.split(",") if n.strip()]
        for name in names:
            hypotheses.append(Hypothesis(name=name, type=type_part))

    return hypotheses


def _hypothesis_indent(line: str) -> int:
    """Return the indentation level of a line."""
    return len(line) - len(line.lstrip())

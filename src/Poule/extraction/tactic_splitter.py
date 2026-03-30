"""Sentence splitting for Coq proof bodies.

Splits a proof body (text between Proof. and Qed./Defined./Admitted./Abort.)
into individual tactic sentences.

Implements specification/coq-proof-backend.md §4.1 (original_script).
"""

from __future__ import annotations

import re


def split_tactics(proof_body: str) -> list[str]:
    """Split a proof body into individual tactic sentences.

    Handles:
    - Standard period-terminated sentences
    - Bullet markers (-, +, *, --, ++, **)
    - Braces ({ and })
    - Periods inside comments (* ... *)
    - Periods inside strings ("...")
    - ssreflect tactic chains (semicolons are internal)

    Args:
        proof_body: The proof body text (between Proof. and Qed.).

    Returns:
        List of tactic strings, each including trailing period.
    """
    # Strip comments first to avoid false period splits
    text = _strip_comments(proof_body)
    text = text.strip()
    if not text:
        return []

    tactics: list[str] = []
    i = 0
    current: list[str] = []

    while i < len(text):
        ch = text[i]

        # Skip string literals
        if ch == '"':
            j = i + 1
            while j < len(text) and text[j] != '"':
                if text[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            j += 1  # past closing quote
            current.append(text[i:j])
            i = j
            continue

        # Check for braces — each is its own sentence
        if ch in '{}':
            # Flush current accumulator if non-empty
            flushed = "".join(current).strip()
            if flushed:
                tactics.append(flushed)
                current = []
            tactics.append(ch)
            i += 1
            continue

        # Check for bullet markers at line start
        if ch in '-+*' and _at_line_start(text, i):
            bullet = _read_bullet(text, i)
            if bullet:
                # Flush current accumulator
                flushed = "".join(current).strip()
                if flushed:
                    tactics.append(flushed)
                    current = []
                tactics.append(bullet)
                i += len(bullet)
                continue

        # Period followed by whitespace or EOF = sentence end
        if ch == '.' and _is_sentence_end(text, i):
            current.append('.')
            tactic = "".join(current).strip()
            if tactic:
                tactics.append(tactic)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    # Flush remaining
    flushed = "".join(current).strip()
    if flushed:
        tactics.append(flushed)

    return tactics


def _strip_comments(text: str) -> str:
    """Remove Coq comments (* ... *) handling nesting."""
    result: list[str] = []
    i = 0
    depth = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == '(' and text[i + 1] == '*':
            depth += 1
            i += 2
            continue
        if i + 1 < len(text) and text[i] == '*' and text[i + 1] == ')':
            if depth > 0:
                depth -= 1
            i += 2
            continue
        if depth == 0:
            result.append(text[i])
        else:
            # Replace comment content with spaces to preserve positions
            result.append(' ')
        i += 1
    return "".join(result)


def _is_sentence_end(text: str, pos: int) -> bool:
    """Check if the period at pos is a sentence terminator.

    A period is a sentence terminator if followed by whitespace or EOF.
    Periods followed by alphanumeric (qualified names like Nat.add) are not.
    """
    if pos + 1 >= len(text):
        return True
    next_ch = text[pos + 1]
    # Period followed by whitespace = sentence end
    if next_ch in ' \t\n\r':
        return True
    # Period followed by letter/digit/underscore = qualified name
    return False


def _at_line_start(text: str, pos: int) -> bool:
    """Check if position is at the start of a line (after optional whitespace)."""
    # Walk backward to find if only whitespace precedes on this line
    j = pos - 1
    while j >= 0:
        if text[j] == '\n':
            return True
        if text[j] not in ' \t':
            return False
        j -= 1
    # At start of text
    return True


def _read_bullet(text: str, pos: int) -> str | None:
    """Read a bullet marker at the given position.

    Bullets: -, +, *, --, ++, **, ---, +++, ***
    A bullet is only valid if the character after the bullet sequence is
    whitespace (not another bullet character used as an operator).
    """
    ch = text[pos]
    if ch not in '-+*':
        return None
    # Read consecutive same characters
    j = pos
    while j < len(text) and text[j] == ch:
        j += 1
    bullet = text[pos:j]
    # Bullet must be followed by whitespace or EOF
    if j < len(text) and text[j] not in ' \t\n\r':
        return None
    return bullet

"""Education-specific FTS5 query preprocessing.

Unlike channels/fts.py which handles Coq identifiers (dot-split, underscore-split),
this module preprocesses natural language queries for the education FTS5 index.
"""

from __future__ import annotations

import re

_FTS5_SPECIAL = re.compile(r'[*"()+\-:^{},=?!;]')
_TOKEN_LIMIT = 20

_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do",
    "does", "for", "from", "has", "how", "i", "if", "in", "is", "it",
    "its", "my", "not", "of", "on", "or", "should", "so", "than",
    "that", "the", "them", "they", "this", "to", "us", "vs", "was",
    "we", "what", "when", "which", "why", "with", "you",
})

# Coq tactic and command names that overlap with common English words.
# Membership in this set signals that a query token should be treated as a
# domain-specific technical term rather than a generic English word.
COQ_DOMAIN_TERMS: frozenset[str] = frozenset({
    "admit", "apply", "assert", "assumption", "auto",
    "case", "change", "clear", "constructor", "contradiction",
    "destruct", "discriminate",
    "eapply", "eauto", "exact", "exists",
    "fold",
    "generalize",
    "have",
    "induction", "injection", "intro", "intros", "inversion",
    "left", "lia", "lra",
    "omega",
    "pose",
    "reflexivity", "remember", "rename", "replace", "rewrite", "right",
    "set", "simpl", "split", "symmetry",
    "transitivity",
    "unfold",
})


def _escape_token(token: str) -> str:
    """Wrap token in double quotes if it contains FTS5 special characters."""
    if _FTS5_SPECIAL.search(token):
        return f'"{token}"'
    return token


def _clean_token(token: str) -> str:
    """Strip trailing punctuation and escape FTS5 specials."""
    cleaned = token.rstrip("?.,!;:")
    if not cleaned:
        return ""
    return _escape_token(cleaned)


def education_fts_query(raw_query: str) -> str:
    """Preprocess a natural language query into an FTS5 query string.

    Strips stop words and trailing punctuation, then joins with OR.
    When domain-specific Coq terms are detected, uses only those for FTS
    to avoid diluting BM25 scores with generic words.
    """
    stripped = raw_query.strip()
    if not stripped:
        return ""
    words = [w.rstrip("?.,!;:") for w in stripped.lower().split() if w]
    words = [w for w in words if w]

    # Prefer domain terms: they benefit most from FTS chapter/title boosting
    domain = [w for w in words if w in COQ_DOMAIN_TERMS]
    if domain:
        tokens = [_escape_token(t) for t in domain][:_TOKEN_LIMIT]
        return " OR ".join(tokens)

    # Fallback: strip stop words
    meaningful = [w for w in words if w not in _STOP_WORDS]
    if not meaningful:
        meaningful = words
    tokens = [_escape_token(t) for t in meaningful][:_TOKEN_LIMIT]
    return " OR ".join(tokens)


def detect_domain_terms(query: str) -> set[str]:
    """Return the set of Coq domain terms found in *query*."""
    tokens = query.lower().split()
    return {t.rstrip("?.,!;:") for t in tokens if t.rstrip("?.,!;:") in COQ_DOMAIN_TERMS}

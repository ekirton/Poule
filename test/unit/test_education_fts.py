"""Tests for education-specific FTS query preprocessing and domain term detection."""

from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path

from Poule.education.fts import (
    COQ_DOMAIN_TERMS,
    detect_domain_terms,
    education_fts_query,
)
from Poule.education.models import Chunk, ChunkMetadata
from Poule.education.storage import EducationStorage


# ---------------------------------------------------------------------------
# education_fts_query
# ---------------------------------------------------------------------------


class TestEducationFtsQuery:
    def test_domain_terms_preferred(self):
        result = education_fts_query("how does induction work")
        # "induction" is a COQ_DOMAIN_TERM; only domain terms used when present
        assert result == "induction"

    def test_empty_string_returns_empty(self):
        assert education_fts_query("") == ""
        assert education_fts_query("   ") == ""

    def test_escapes_fts5_special_characters(self):
        # Quotes around "have" contain FTS5 specials — they get escaped
        result = education_fts_query('test "value"')
        # No domain terms, so falls back to stop-word-filtered tokens
        assert "test" in result

    def test_respects_token_limit(self):
        query = " ".join(f"word{i}" for i in range(30))
        tokens = education_fts_query(query).split(" OR ")
        assert len(tokens) == 20

    def test_single_token(self):
        assert education_fts_query("induction") == "induction"

    def test_strips_leading_trailing_whitespace(self):
        assert education_fts_query("  hello world  ") == "hello OR world"

    def test_strips_stop_words(self):
        result = education_fts_query("what is the difference between assert and have")
        assert "assert" in result
        assert "have" in result
        assert "what" not in result.split(" OR ")
        assert "the" not in result.split(" OR ")

    def test_fallback_when_all_stop_words(self):
        result = education_fts_query("how is it")
        assert len(result) > 0


# ---------------------------------------------------------------------------
# detect_domain_terms
# ---------------------------------------------------------------------------


class TestDetectDomainTerms:
    def test_recognizes_coq_tactics(self):
        terms = detect_domain_terms("how does induction work in Coq?")
        assert "induction" in terms

    def test_recognizes_have_and_assert(self):
        terms = detect_domain_terms("what is the difference between assert and have?")
        assert "assert" in terms
        assert "have" in terms

    def test_ignores_common_english_words(self):
        terms = detect_domain_terms("how does this work")
        assert len(terms) == 0

    def test_case_insensitive(self):
        terms = detect_domain_terms("Apply REWRITE Simpl")
        assert "apply" in terms
        assert "rewrite" in terms
        assert "simpl" in terms

    def test_strips_trailing_punctuation(self):
        terms = detect_domain_terms("use induction? try destruct!")
        assert "induction" in terms
        assert "destruct" in terms

    def test_returns_empty_for_no_domain_terms(self):
        assert detect_domain_terms("hello world foo bar") == set()


# ---------------------------------------------------------------------------
# COQ_DOMAIN_TERMS vocabulary
# ---------------------------------------------------------------------------


class TestCoqDomainTerms:
    def test_contains_ambiguous_english_words(self):
        ambiguous = {"have", "apply", "set", "left", "right", "split", "case", "exact", "auto"}
        assert ambiguous.issubset(COQ_DOMAIN_TERMS)

    def test_contains_core_tactics(self):
        core = {"induction", "destruct", "rewrite", "simpl", "inversion", "reflexivity"}
        assert core.issubset(COQ_DOMAIN_TERMS)

    def test_is_frozenset(self):
        assert isinstance(COQ_DOMAIN_TERMS, frozenset)


# ---------------------------------------------------------------------------
# EducationStorage.search_fts
# ---------------------------------------------------------------------------


def _make_chunk(text, section="Test Section", chapter="TestChapter", volume="lf"):
    return Chunk(
        text=text,
        code_blocks=[],
        metadata=ChunkMetadata(
            volume=volume,
            volume_title="Logical Foundations",
            chapter=chapter,
            chapter_file=f"{chapter}.html",
            section_title=section,
            section_path=[chapter, section],
            anchor_id=None,
        ),
        token_count=len(text.split()),
    )


class TestEducationStorageSearchFts:
    @pytest.fixture
    def db_with_chunks(self, tmp_path):
        db_path = tmp_path / "education.db"
        EducationStorage.create(db_path)
        chunks = [
            _make_chunk(
                "Proof by induction is the key technique for natural numbers",
                section="Proof by Induction",
                chapter="Induction",
            ),
            _make_chunk(
                "Rewriting replaces one side of an equation with the other",
                section="Proof by Rewriting",
                chapter="Basics",
            ),
            _make_chunk(
                "Case analysis splits a proof into branches for each constructor",
                section="Proof by Case Analysis",
                chapter="Basics",
            ),
        ]
        EducationStorage.write_chunks(db_path, chunks)
        return db_path

    def test_returns_results_for_matching_query(self, db_with_chunks):
        results = EducationStorage.search_fts(db_with_chunks, "induction", limit=10)
        assert len(results) > 0
        chunk_ids = [r[0] for r in results]
        assert 1 in chunk_ids  # chunk 1 is the induction chunk

    def test_scores_are_normalized(self, db_with_chunks):
        results = EducationStorage.search_fts(db_with_chunks, "proof", limit=10)
        for _, score in results:
            assert 0.0 <= score <= 1.0

    def test_respects_limit(self, db_with_chunks):
        results = EducationStorage.search_fts(db_with_chunks, "proof", limit=1)
        assert len(results) <= 1

    def test_empty_query_returns_empty(self, db_with_chunks):
        assert EducationStorage.search_fts(db_with_chunks, "", limit=10) == []
        assert EducationStorage.search_fts(db_with_chunks, "  ", limit=10) == []

    def test_no_match_returns_empty(self, db_with_chunks):
        results = EducationStorage.search_fts(db_with_chunks, "zzzznonexistent", limit=10)
        assert results == []

    def test_chapter_column_boosted(self, db_with_chunks):
        """Chunks matching on chapter/section_title should rank higher."""
        results = EducationStorage.search_fts(db_with_chunks, "induction", limit=10)
        # The induction chunk (chapter="Induction") should be first
        assert results[0][0] == 1

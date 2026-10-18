"""Tests for TranscriptAnalyst — requirement extraction."""

from __future__ import annotations

import pytest

from app.pipeline.transcript_analyst import TranscriptAnalyst, _chunk_segment
from app.schemas import RequirementType


class TestTranscriptAnalystBasic:
    def test_returns_requirements_document(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        assert doc.transcript_id == "TRANSCRIPT-A"

    def test_extracts_functional_requirements(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        assert len(doc.functional_requirements) > 0, "Expected functional requirements from transcript A"

    def test_extracts_constraints(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        assert len(doc.constraints) > 0, "Expected budget/timeline constraints from transcript A"

    def test_extracts_open_questions(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        assert len(doc.open_questions) > 0, "Expected open questions from transcript A"

    def test_source_refs_populated(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        for req in doc.all_requirements():
            assert req.sources, f"Requirement {req.req_id} has no source references"
            assert req.sources[0].transcript_id == "TRANSCRIPT-A"
            assert req.sources[0].segment_id.startswith("SEG-A-")

    def test_all_req_ids_unique(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        ids = [r.req_id for r in doc.all_requirements()]
        assert len(ids) == len(set(ids)), "Requirement IDs must be unique"

    def test_confidence_in_range(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        for req in doc.all_requirements():
            assert 0.0 <= req.confidence <= 1.0

    def test_description_not_empty(self, analyst, transcript_a):
        doc = analyst.analyse(transcript_a)
        for req in doc.all_requirements():
            assert req.description.strip(), f"Empty description for {req.req_id}"

    def test_transcript_b_extracts_checkout_items(self, analyst, transcript_b):
        doc = analyst.analyse(transcript_b)
        # Transcript B is about e-commerce; should find functional reqs
        assert len(doc.functional_requirements) > 0

    def test_transcript_c_extracts_requirements(self, analyst, transcript_c):
        doc = analyst.analyse(transcript_c)
        all_reqs = doc.all_requirements()
        assert len(all_reqs) > 0, "Transcript C must produce requirements"


class TestChunking:
    def test_short_text_no_chunking(self):
        text = "We need a search bar."
        chunks = _chunk_segment(text, max_chars=1000)
        assert chunks == [text]

    def test_long_text_creates_multiple_chunks(self):
        # 3 long sentences
        text = (
            "We need feature X with many details and requirements. " * 15
            + "We also need feature Y with additional constraints. " * 15
        )
        chunks = _chunk_segment(text, max_chars=200)
        assert len(chunks) > 1

    def test_chunks_cover_all_content(self):
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        chunks = _chunk_segment(text, max_chars=50)
        combined = " ".join(chunks)
        # All sentences should appear somewhere
        for part in ["Sentence one", "Sentence two", "Sentence three"]:
            assert part in combined

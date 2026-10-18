"""Tests for ScopeAgent — requirements → scope document mapping."""

from __future__ import annotations

import pytest

from app.pipeline.scope_agent import ScopeAgent
from app.schemas import (
    ExtractedRequirement,
    FeasibilityFinding,
    RequirementType,
    RequirementsDocument,
    TranscriptSegmentRef,
    VerificationStatus,
)


def _make_req(req_id: str, req_type: RequirementType, description: str) -> ExtractedRequirement:
    return ExtractedRequirement(
        req_id=req_id,
        req_type=req_type,
        description=description,
        sources=[
            TranscriptSegmentRef(
                transcript_id="TRANSCRIPT-TEST",
                segment_id="SEG-T-01",
                line_number=1,
                speaker="Test Speaker",
            )
        ],
        confidence=0.8,
        verification_status=VerificationStatus.UNVERIFIED,
    )


def _make_reqs(
    transcript_id: str = "TRANSCRIPT-TEST",
    functional: list | None = None,
    constraints: list | None = None,
    open_questions: list | None = None,
) -> RequirementsDocument:
    doc = RequirementsDocument(transcript_id=transcript_id)
    for i, desc in enumerate(functional or []):
        doc.functional_requirements.append(
            _make_req(f"REQ-F-{i}", RequirementType.FUNCTIONAL, desc)
        )
    for i, desc in enumerate(constraints or []):
        doc.constraints.append(
            _make_req(f"REQ-C-{i}", RequirementType.CONSTRAINT, desc)
        )
    for i, desc in enumerate(open_questions or []):
        doc.open_questions.append(
            _make_req(f"REQ-Q-{i}", RequirementType.OPEN_QUESTION, desc)
        )
    return doc


class TestScopeAgentBasic:
    def test_scope_from_transcript_a(self, scope_agent, reqs_a):
        scope = scope_agent.generate_scope(reqs_a, [])
        assert scope.transcript_id == "TRANSCRIPT-A"

    def test_deliverables_populated(self, scope_agent, reqs_a):
        scope = scope_agent.generate_scope(reqs_a, [])
        assert len(scope.deliverables) > 0

    def test_in_scope_populated(self, scope_agent, reqs_a):
        scope = scope_agent.generate_scope(reqs_a, [])
        assert len(scope.in_scope) > 0

    def test_out_of_scope_items_detected(self, scope_agent):
        reqs = _make_reqs(
            functional=[
                "We need a search bar",
                "Loyalty points programme would be out of scope for this phase",
            ]
        )
        scope = scope_agent.generate_scope(reqs, [])
        out_descs = " ".join(scope.out_of_scope)
        assert "out of scope" in out_descs.lower()

    def test_no_duplicates_in_out_of_scope(self, scope_agent, reqs_a):
        scope = scope_agent.generate_scope(reqs_a, [])
        assert len(scope.out_of_scope) == len(set(scope.out_of_scope))

    def test_unanswered_feasibility_creates_risk(self, scope_agent, reqs_a):
        unanswered = FeasibilityFinding(
            question="Can we support voice search?",
            answered=False,
            confidence=0.0,
            error="KB unavailable",
        )
        scope = scope_agent.generate_scope(reqs_a, [unanswered])
        risk_text = " ".join(scope.risks)
        assert "voice search" in risk_text.lower() or "unresolved" in risk_text.lower()

    def test_answered_feasibility_creates_acceptance_criteria(self, scope_agent, reqs_a):
        answered = FeasibilityFinding(
            question="Is Stripe checkout supported?",
            answered=True,
            confidence=0.9,
            kb_answer="Yes, Stripe is supported.",
        )
        scope = scope_agent.generate_scope(reqs_a, [answered])
        criteria_text = " ".join(scope.acceptance_criteria)
        assert "stripe" in criteria_text.lower()

    def test_open_questions_passed_through(self, scope_agent):
        reqs = _make_reqs(open_questions=["Can we add saved searches?"])
        scope = scope_agent.generate_scope(reqs, [])
        assert any("saved searches" in q.lower() for q in scope.open_questions)

    def test_scope_from_transcript_b(self, scope_agent, reqs_b):
        scope = scope_agent.generate_scope(reqs_b, [])
        assert scope.transcript_id == "TRANSCRIPT-B"
        assert len(scope.deliverables) > 0

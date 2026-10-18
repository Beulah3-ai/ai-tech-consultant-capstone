"""Focused regression tests for proposal milestone scheduling."""

from __future__ import annotations

from app.pipeline.proposal_agent import ProposalAgent
from app.schemas import EstimationItem, ScopeDocument


def _estimation_items(count: int = 3) -> list[EstimationItem]:
    return [
        EstimationItem(
            task=f"Task {index + 1}",
            low_hours=4,
            likely_hours=8,
            high_hours=12,
        )
        for index in range(count)
    ]


def test_six_week_deadline_bounds_milestones_and_flags_unverified_feasibility():
    scope = ScopeDocument(
        transcript_id="SIX-WEEK",
        assumptions=["Delivery must be completed within 6 weeks."],
    )

    proposal = ProposalAgent().generate_proposal(scope, _estimation_items())

    assert [milestone.week for milestone in proposal.milestones] == [2, 4, 6]
    assert [milestone.name for milestone in proposal.milestones] == [
        "Discovery & Setup",
        "Core Development",
        "Testing & Delivery",
    ]
    assert proposal.milestones[-1].name == "Testing & Delivery"
    assert "Timeline feasibility is unverified" in " ".join(
        proposal.consistency_warnings
    )
    assert proposal.provider == "deterministic_pipeline"
    assert proposal.is_mock is True


def test_ten_week_deadline_preserves_derived_chronological_schedule():
    scope = ScopeDocument(
        transcript_id="TEN-WEEK",
        assumptions=["The delivery timeline of 10 weeks is approved."],
    )

    proposal = ProposalAgent().generate_proposal(scope, _estimation_items())

    weeks = [milestone.week for milestone in proposal.milestones]
    assert weeks == [4, 7, 10]
    assert weeks == sorted(weeks)
    assert max(weeks) <= 10


def test_missing_or_ambiguous_deadline_omits_schedule_and_warns():
    agent = ProposalAgent()
    items = _estimation_items()

    missing_deadline = agent.generate_proposal(
        ScopeDocument(transcript_id="NO-DEADLINE"),
        items,
    )
    ambiguous_deadline = agent.generate_proposal(
        ScopeDocument(
            transcript_id="AMBIGUOUS-DEADLINE",
            assumptions=[
                "The delivery timeline is 6 weeks.",
                "The deadline is 10 weeks.",
            ],
        ),
        items,
    )
    unconfirmed_deadline = agent.generate_proposal(
        ScopeDocument(
            transcript_id="UNCONFIRMED-DEADLINE",
            open_questions=["Could delivery happen within 6 weeks?"],
        ),
        items,
    )

    assert missing_deadline.milestones == []
    assert any(
        "No project deadline was found" in warning
        for warning in missing_deadline.consistency_warnings
    )
    assert ambiguous_deadline.milestones == []
    assert any(
        "Project timeline is ambiguous" in warning
        for warning in ambiguous_deadline.consistency_warnings
    )
    assert unconfirmed_deadline.milestones == []
    assert any(
        "No project deadline was found" in warning
        for warning in unconfirmed_deadline.consistency_warnings
    )


def test_no_estimates_still_produces_no_milestones():
    proposal = ProposalAgent().generate_proposal(
        ScopeDocument(transcript_id="NO-ESTIMATES"),
        [],
    )

    assert proposal.milestones == []

"""Tests for ChangeAnalyst — addition/modification/removal/out-of-scope detection."""

from __future__ import annotations

import pytest

from app.pipeline.change_analyst import ChangeAnalyst
from app.pipeline.estimation_agent import EstimationAgent
from app.pipeline.proposal_agent import ProposalAgent
from app.pipeline.scope_agent import ScopeAgent
from app.pipeline.transcript_analyst import TranscriptAnalyst
from app.schemas import (
    ChangeType,
    ProposalStatus,
    RequirementsDocument,
)


def _build_approved_proposal(transcript):
    analyst = TranscriptAnalyst()
    scope_agent = ScopeAgent()
    est_agent = EstimationAgent()
    prop_agent = ProposalAgent()

    reqs = analyst.analyse(transcript)
    scope = scope_agent.generate_scope(reqs, [])
    items = est_agent.estimate(scope)
    proposal = prop_agent.generate_proposal(scope, items)
    # Manually approve for testing
    proposal.status = ProposalStatus.APPROVED
    return proposal


class TestChangeAnalyst:
    def test_requires_approved_baseline(self, analyst, transcript_c):
        """Change analysis must reject unapproved baselines."""
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        baseline.status = ProposalStatus.DRAFT  # intentionally un-approved

        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        with pytest.raises(ValueError, match="not APPROVED"):
            ca.analyse_changes(baseline, reqs_c)

    def test_detects_changes(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        assert len(analysis.changes) > 0, "Follow-up transcript C must produce change records"

    def test_scope_delta_summary_not_empty(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        assert analysis.scope_delta_summary

    def test_followup_transcript_id_set(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        assert analysis.followup_transcript_id == "TRANSCRIPT-C"

    def test_baseline_proposal_id_set(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        assert analysis.baseline_proposal_id == baseline.proposal_id

    def test_analysis_status_is_draft(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        assert analysis.status == ProposalStatus.DRAFT

    def test_change_types_are_valid(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        valid_types = set(ChangeType)
        for change in analysis.changes:
            assert change.change_type in valid_types

    def test_revised_estimates_have_valid_ranges(self, analyst, transcript_c):
        from app.data.transcripts import TRANSCRIPT_A_WEBSITE
        baseline = _build_approved_proposal(TRANSCRIPT_A_WEBSITE)
        ca = ChangeAnalyst()
        reqs_c = analyst.analyse(transcript_c)
        analysis = ca.analyse_changes(baseline, reqs_c)
        for rev in analysis.revised_estimates:
            assert rev.low_hours <= rev.likely_hours <= rev.high_hours

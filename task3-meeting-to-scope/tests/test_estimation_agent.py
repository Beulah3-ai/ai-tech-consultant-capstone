"""Tests for EstimationAgent — effort lookup and estimate ranges."""

from __future__ import annotations

import pytest

from app.pipeline.estimation_agent import EstimationAgent
from app.schemas import ScopeDocument, ScopeItem


def _scope_with_items(*descriptions: str, transcript_id: str = "TEST") -> ScopeDocument:
    scope = ScopeDocument(transcript_id=transcript_id)
    for desc in descriptions:
        scope.deliverables.append(ScopeItem(description=desc, source_req_ids=[]))
    return scope


class TestEstimationAgent:
    def test_returns_list(self):
        agent = EstimationAgent()
        scope = _scope_with_items("We need a search bar.")
        items = agent.estimate(scope)
        assert isinstance(items, list)

    def test_high_gte_likely_gte_low(self):
        agent = EstimationAgent()
        scope = _scope_with_items(
            "We need full Stripe Checkout integration.",
            "We need multi-select faceted filters.",
            "We need automated transactional email notifications.",
        )
        items = agent.estimate(scope)
        for item in items:
            assert item.low_hours <= item.likely_hours <= item.high_hours, (
                f"{item.task}: low={item.low_hours} likely={item.likely_hours} high={item.high_hours}"
            )

    def test_stripe_keyword_matches(self):
        agent = EstimationAgent()
        scope = _scope_with_items("Stripe checkout integration with digital wallets.")
        items = agent.estimate(scope)
        assert len(items) == 1
        assert items[0].likely_hours >= 8  # stripe bucket

    def test_voice_search_keyword_matches(self):
        agent = EstimationAgent()
        scope = _scope_with_items("Voice search using browser Web Speech API.")
        items = agent.estimate(scope)
        assert len(items) == 1
        assert items[0].likely_hours >= 4

    def test_filter_keyword_matches(self):
        agent = EstimationAgent()
        scope = _scope_with_items("Multi-select faceted filter panel.")
        items = agent.estimate(scope)
        assert len(items) == 1
        assert items[0].likely_hours >= 6

    def test_assumptions_always_present(self):
        agent = EstimationAgent()
        scope = _scope_with_items("Order management dashboard.")
        items = agent.estimate(scope)
        for item in items:
            assert len(item.assumptions) > 0
            # Must explicitly state estimates are approximations
            combined_assumptions = " ".join(item.assumptions).upper()
            assert "ESTIMATED" in combined_assumptions or "not verified" in " ".join(item.assumptions).lower()

    def test_empty_scope_returns_empty_list(self):
        agent = EstimationAgent()
        scope = ScopeDocument(transcript_id="TEST")
        items = agent.estimate(scope)
        assert items == []

    def test_duplicate_deliverables_deduplicated(self):
        agent = EstimationAgent()
        scope = _scope_with_items("Search bar.", "Search bar.")
        items = agent.estimate(scope)
        assert len(items) == 1

    def test_estimation_from_transcript_a_scope(self, estimation_agent, scope_a):
        items = estimation_agent.estimate(scope_a)
        assert len(items) > 0

    def test_all_hours_non_negative(self, estimation_agent, scope_a):
        items = estimation_agent.estimate(scope_a)
        for item in items:
            assert item.low_hours >= 0
            assert item.likely_hours >= 0
            assert item.high_hours >= 0

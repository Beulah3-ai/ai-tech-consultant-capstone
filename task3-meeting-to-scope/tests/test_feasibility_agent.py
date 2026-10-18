"""Tests for FeasibilityAgent — KB API integration with mocked transport."""

from __future__ import annotations

import json

import httpx
import pytest

from app.pipeline.feasibility_agent import FeasibilityAgent
from app.schemas import FeasibilityFinding


def _make_kb_response(answered: bool, answer: str = "", confidence: float = 0.8, is_mock: bool = True):
    """Return an httpx.Response that simulates a KB API response."""
    payload = {
        "answer": answer,
        "answered": answered,
        "confidence": confidence,
        "is_mock": is_mock,
        "sources": [],
        "disclaimer": "Mock response" if is_mock else None,
        "provider": "mock" if is_mock else "local_retrieval",
    }
    return httpx.Response(200, json=payload)


class MockKBTransport(httpx.BaseTransport):
    def __init__(self, response: httpx.Response):
        self._response = response

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._response


class TimeoutTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Simulated timeout")


class ErrorTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")


class TestFeasibilityAgentSuccess:
    def test_answered_true(self):
        transport = MockKBTransport(_make_kb_response(True, "Yes, supported.", 0.9, is_mock=False))
        client = httpx.Client(transport=transport)
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Does the platform support voice search?")
        assert result.answered is True
        assert result.kb_answer == "Yes, supported."
        assert result.error is None

    def test_answered_false_abstention(self):
        transport = MockKBTransport(_make_kb_response(False, "I cannot answer that.", 0.0, is_mock=False))
        client = httpx.Client(transport=transport)
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Unknown question")
        assert result.answered is False
        assert result.error is None

    def test_is_mock_flag_preserved(self):
        transport = MockKBTransport(_make_kb_response(True, "Mock answer", 0.5, is_mock=True))
        client = httpx.Client(transport=transport)
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Some question")
        assert result.is_mock is True

    def test_confidence_in_range(self):
        transport = MockKBTransport(_make_kb_response(True, "Answer", 0.75, is_mock=False))
        client = httpx.Client(transport=transport)
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Question")
        assert 0.0 <= result.confidence <= 1.0

    def test_query_all_returns_list(self):
        transport = MockKBTransport(_make_kb_response(True, "Answer", 0.8))
        client = httpx.Client(transport=transport)
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        results = agent.query_all(["Q1", "Q2", "Q3"])
        assert len(results) == 3


class TestFeasibilityAgentFailures:
    def test_timeout_returns_error(self):
        client = httpx.Client(transport=TimeoutTransport())
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Will this timeout?")
        assert result.answered is False
        assert result.error is not None
        assert "timed out" in result.error.lower()

    def test_http_error_returns_error(self):
        client = httpx.Client(transport=ErrorTransport())
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        result = agent.query_single("Will this fail?")
        assert result.answered is False
        assert result.error is not None
        assert "503" in result.error

    def test_never_raises_exception(self):
        """FeasibilityAgent must never let exceptions propagate."""
        client = httpx.Client(transport=TimeoutTransport())
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        # Should not raise
        result = agent.query_single("Any question")
        assert isinstance(result, FeasibilityFinding)

    def test_query_all_partial_failure(self):
        """query_all should still return results for non-failing questions."""
        client = httpx.Client(transport=TimeoutTransport())
        agent = FeasibilityAgent(kb_url="http://fakehost", http_client=client)
        results = agent.query_all(["Q1", "Q2"])
        assert len(results) == 2
        for r in results:
            assert r.answered is False

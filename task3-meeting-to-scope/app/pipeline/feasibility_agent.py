"""Feasibility Agent: queries Task 1 Knowledge Brain API for technical questions.

Never fabricates answers.  If the KB is unreachable or returns an abstention,
that is reported transparently with answered=False.
"""

from __future__ import annotations

import math
import os
import re
from typing import Any, Dict, List, Optional

import httpx

from app.schemas import FeasibilityFinding


DEFAULT_KB_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 5.0  # seconds


def _normalize_sources(sources: Any) -> List[Dict[str, str]]:
    """Convert Task 1 string citations into Task 3's structured source format."""
    if not isinstance(sources, list):
        raise ValueError("sources must be a list of citations")

    normalized: List[Dict[str, str]] = []
    for source in sources:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("each source citation must be a non-empty string")

        citation = source.strip()
        match = re.fullmatch(r"(?P<title>.+?)\s+\((?P<url>https?://[^()\s]+)\)", citation)
        if match:
            normalized.append(
                {
                    "title": match.group("title").strip(),
                    "url": match.group("url"),
                    "citation": citation,
                }
            )
            continue

        url_match = re.search(r"https?://\S+", citation)
        if url_match:
            url = url_match.group().rstrip(").,;")
            title = citation[:url_match.start()].rstrip(" (")
            normalized.append(
                {"title": title, "url": url, "citation": citation}
            )
        else:
            normalized.append({"citation": citation})

    return normalized


def _parse_kb_response(question: str, data: Any) -> FeasibilityFinding:
    """Validate the KB payload and require evidence before marking it feasible."""
    if not isinstance(data, dict):
        raise ValueError("response body must be a JSON object")
    if not isinstance(data.get("answered"), bool):
        raise ValueError("'answered' must be a boolean")
    if not isinstance(data.get("answer"), str):
        raise ValueError("'answer' must be a string")

    confidence = data.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0.0 <= confidence <= 1.0
    ):
        raise ValueError("'confidence' must be a number between 0 and 1")

    if not isinstance(data.get("is_mock"), bool):
        raise ValueError("'is_mock' must be a boolean")
    disclaimer = data.get("disclaimer")
    if not isinstance(disclaimer, str):
        raise ValueError("'disclaimer' must be a string")

    sources = _normalize_sources(data.get("sources"))
    answered = data["answered"]
    answer = data["answer"].strip()
    if answered and not answer:
        raise ValueError("an answered response must include an answer")

    if answered and not sources:
        return FeasibilityFinding(
            question=question,
            kb_answer=answer,
            answered=False,
            confidence=0.0,
            sources=[],
            is_mock=data["is_mock"],
            error="Knowledge Brain response did not include source evidence.",
            disclaimer=disclaimer,
        )

    return FeasibilityFinding(
        question=question,
        kb_answer=answer or None,
        answered=answered,
        confidence=float(confidence),
        sources=sources,
        is_mock=data["is_mock"],
        error=None,
        disclaimer=disclaimer,
    )


def _failure_finding(question: str, error: str) -> FeasibilityFinding:
    return FeasibilityFinding(
        question=question,
        answered=False,
        confidence=0.0,
        sources=[],
        is_mock=False,
        error=error,
    )


class FeasibilityAgent:
    """Calls Task 1's POST /query endpoint for feasibility questions.

    If the Knowledge Brain is unavailable, returns FeasibilityFinding with
    answered=False and error message.  Never pretends the service responded.
    """

    def __init__(
        self,
        kb_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.kb_url = (kb_url or os.getenv("KNOWLEDGE_BRAIN_URL", DEFAULT_KB_URL)).rstrip("/")
        self.timeout = timeout
        # Allow injection of a mock client for testing
        self._client = http_client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self.timeout)

    def query_single(self, question: str) -> FeasibilityFinding:
        """Query the KB for a single question.  Returns FeasibilityFinding."""
        client = self._get_client()
        close_after = self._client is None  # only close if we created it

        try:
            return self._query_with_client(client, question)
        finally:
            if close_after:
                client.close()

    def query_all(self, questions: List[str]) -> List[FeasibilityFinding]:
        """Query the KB for each question in the list."""
        client = self._get_client()
        close_after = self._client is None
        try:
            return [self._query_with_client(client, q) for q in questions]
        finally:
            if close_after:
                client.close()

    def _query_with_client(
        self, client: httpx.Client, question: str
    ) -> FeasibilityFinding:
        payload = {"query": question, "provider": "local_retrieval"}
        try:
            response = client.post(f"{self.kb_url}/query", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException:
            return _failure_finding(question, "Knowledge Brain API timed out.")
        except httpx.HTTPStatusError as exc:
            return _failure_finding(
                question, f"Knowledge Brain returned HTTP {exc.response.status_code}."
            )
        except Exception as exc:  # noqa: BLE001
            return _failure_finding(
                question, f"Knowledge Brain unavailable: {exc}"
            )

        try:
            data: Any = response.json()
        except (TypeError, ValueError) as exc:
            return _failure_finding(
                question, f"Knowledge Brain returned invalid JSON: {exc}"
            )

        try:
            return _parse_kb_response(question, data)
        except (OverflowError, TypeError, ValueError) as exc:
            return _failure_finding(
                question, f"Knowledge Brain returned an invalid response: {exc}"
            )

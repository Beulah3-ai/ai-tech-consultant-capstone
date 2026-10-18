"""Feasibility Agent: queries Task 1 Knowledge Brain API for technical questions.

Never fabricates answers.  If the KB is unreachable or returns an abstention,
that is reported transparently with answered=False.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from app.schemas import FeasibilityFinding


DEFAULT_KB_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 5.0  # seconds


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
        payload = {"query": question, "provider": "local_retrieval"}

        client = self._get_client()
        close_after = self._client is None  # only close if we created it

        try:
            response = client.post(f"{self.kb_url}/query", json=payload)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()

            return FeasibilityFinding(
                question=question,
                kb_answer=data.get("answer"),
                answered=bool(data.get("answered", False)),
                confidence=float(data.get("confidence", 0.0)),
                sources=data.get("sources", []),
                is_mock=bool(data.get("is_mock", False)),
                error=None,
                disclaimer=data.get("disclaimer"),
            )

        except httpx.TimeoutException:
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error="Knowledge Brain API timed out.",
            )
        except httpx.HTTPStatusError as exc:
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error=f"Knowledge Brain returned HTTP {exc.response.status_code}.",
            )
        except Exception as exc:  # noqa: BLE001
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error=f"Knowledge Brain unavailable: {exc}",
            )
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
            data: Dict[str, Any] = response.json()
            return FeasibilityFinding(
                question=question,
                kb_answer=data.get("answer"),
                answered=bool(data.get("answered", False)),
                confidence=float(data.get("confidence", 0.0)),
                sources=data.get("sources", []),
                is_mock=bool(data.get("is_mock", False)),
                error=None,
                disclaimer=data.get("disclaimer"),
            )
        except httpx.TimeoutException:
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error="Knowledge Brain API timed out.",
            )
        except httpx.HTTPStatusError as exc:
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error=f"Knowledge Brain returned HTTP {exc.response.status_code}.",
            )
        except Exception as exc:  # noqa: BLE001
            return FeasibilityFinding(
                question=question,
                kb_answer=None,
                answered=False,
                confidence=0.0,
                sources=[],
                is_mock=False,
                error=f"Knowledge Brain unavailable: {exc}",
            )

"""Shared pytest fixtures for Task 3 tests."""

from __future__ import annotations

import gc
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.data.transcripts import (
    TRANSCRIPT_A_WEBSITE,
    TRANSCRIPT_B_ECOMMERCE,
    TRANSCRIPT_C_FOLLOWUP,
)
from app.pipeline.transcript_analyst import TranscriptAnalyst
from app.pipeline.scope_agent import ScopeAgent
from app.pipeline.estimation_agent import EstimationAgent
from app.pipeline.proposal_agent import ProposalAgent
from app.schemas import ProposalStatus


@pytest.fixture
def transcript_a():
    return TRANSCRIPT_A_WEBSITE


@pytest.fixture
def transcript_b():
    return TRANSCRIPT_B_ECOMMERCE


@pytest.fixture
def transcript_c():
    return TRANSCRIPT_C_FOLLOWUP


@pytest.fixture
def analyst():
    return TranscriptAnalyst()


@pytest.fixture
def scope_agent():
    return ScopeAgent()


@pytest.fixture
def estimation_agent():
    return EstimationAgent()


@pytest.fixture
def proposal_agent():
    return ProposalAgent()


@pytest.fixture
def reqs_a(analyst, transcript_a):
    return analyst.analyse(transcript_a)


@pytest.fixture
def reqs_b(analyst, transcript_b):
    return analyst.analyse(transcript_b)


@pytest.fixture
def reqs_c(analyst, transcript_c):
    return analyst.analyse(transcript_c)


@pytest.fixture
def scope_a(scope_agent, reqs_a):
    return scope_agent.generate_scope(reqs_a, [])


@pytest.fixture
def scope_b(scope_agent, reqs_b):
    return scope_agent.generate_scope(reqs_b, [])


@pytest.fixture
def estimated_a(estimation_agent, scope_a):
    return estimation_agent.estimate(scope_a)


@pytest.fixture
def proposal_a(proposal_agent, scope_a, estimated_a):
    return proposal_agent.generate_proposal(scope_a, estimated_a)


@pytest.fixture
def tmp_data_dir() -> Generator[Path, None, None]:
    """Temporary data directory for store tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
    gc.collect()


@pytest.fixture
def test_client(tmp_data_dir):
    """FastAPI TestClient with temporary data directory."""
    import os
    os.environ["DATA_DIR"] = str(tmp_data_dir)
    # Re-create store with temp dir
    from app import main as main_module
    from app.store import ProposalStore
    main_module._store = ProposalStore(data_dir=tmp_data_dir)

    from app.main import app
    with TestClient(app) as client:
        yield client

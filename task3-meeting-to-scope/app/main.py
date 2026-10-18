"""Task 3: Meeting to Scope — FastAPI application.

Endpoints:
  GET  /health
  POST /transcripts/{transcript_id}/process
  GET  /proposals/{proposal_id}
  POST /proposals/{proposal_id}/approve
  POST /proposals/{proposal_id}/reject
  POST /proposals/{proposal_id}/request-revision
  POST /transcripts/{followup_id}/compare/{baseline_proposal_id}
  GET  /audit
  GET  /transcripts
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.data.transcripts import get_all_transcripts, get_transcript_by_id
from app.pipeline.change_analyst import ChangeAnalyst
from app.pipeline.estimation_agent import EstimationAgent
from app.pipeline.feasibility_agent import FeasibilityAgent
from app.pipeline.proposal_agent import ProposalAgent
from app.pipeline.scope_agent import ScopeAgent
from app.pipeline.transcript_analyst import TranscriptAnalyst
from app.schemas import (
    ApprovalAction,
    ApprovalRecord,
    ApprovalRequest,
    AuditEntry,
    ChangeAnalysis,
    CompareTranscriptsResponse,
    HealthResponse,
    ProcessTranscriptRequest,
    ProcessTranscriptResponse,
    ProposalDocument,
    ProposalStatus,
)
from app.store import ProposalStore

app = FastAPI(
    title="Task 3: Meeting to Scope",
    description=(
        "Converts meeting transcripts into structured scope and proposal documents. "
        "Uses a deterministic pipeline (no LLM required). "
        "All outputs are explicitly labelled as mock/deterministic."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Shared services
# ---------------------------------------------------------------------------

_DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "data")))
_store = ProposalStore(data_dir=_DATA_DIR)
_analyst = TranscriptAnalyst()
_scope_agent = ScopeAgent()
_estimation_agent = EstimationAgent()
_proposal_agent = ProposalAgent()
_change_analyst = ChangeAnalyst()


def _get_kb_url() -> str:
    return os.getenv("KNOWLEDGE_BRAIN_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="task3-meeting-to-scope",
        provider="deterministic_pipeline",
        timestamp=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# GET /transcripts — list available transcripts
# ---------------------------------------------------------------------------


@app.get("/transcripts", tags=["Transcripts"])
def list_transcripts() -> List[Dict[str, Any]]:
    """Return metadata for all available synthetic transcripts."""
    return [
        {
            "transcript_id": t["transcript_id"],
            "title": t["title"],
            "client_name": t["client_name"],
            "date": t["date"],
            "segment_count": len(t.get("segments", [])),
        }
        for t in get_all_transcripts()
    ]


# ---------------------------------------------------------------------------
# POST /transcripts/{transcript_id}/process — run full pipeline
# ---------------------------------------------------------------------------


@app.post(
    "/transcripts/{transcript_id}/process",
    response_model=ProcessTranscriptResponse,
    tags=["Pipeline"],
)
def process_transcript(
    transcript_id: str,
    body: Optional[ProcessTranscriptRequest] = None,
) -> ProcessTranscriptResponse:
    """Run the full 5-stage pipeline on a transcript and return a DRAFT proposal."""
    try:
        transcript = get_transcript_by_id(transcript_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    kb_url = (body.knowledge_brain_url if body and body.knowledge_brain_url else None) or _get_kb_url()

    # Stage 1 — Extract requirements
    reqs = _analyst.analyse(transcript)

    # Stage 2 — Feasibility (open questions → KB queries)
    questions = [r.description for r in reqs.open_questions[:5]]  # limit per run
    feasibility_agent = FeasibilityAgent(kb_url=kb_url)
    findings = feasibility_agent.query_all(questions)

    # Stage 3 — Scope
    scope = _scope_agent.generate_scope(reqs, findings)

    # Stage 4 — Estimation
    estimation_items = _estimation_agent.estimate(scope)

    # Stage 5 — Proposal
    proposal = _proposal_agent.generate_proposal(scope, estimation_items)

    # Persist
    _store.save_proposal(proposal)

    return ProcessTranscriptResponse(
        proposal_id=proposal.proposal_id,
        version=proposal.version,
        transcript_id=transcript_id,
        status=proposal.status,
        proposal=proposal,
    )


# ---------------------------------------------------------------------------
# GET /proposals/{proposal_id} — retrieve a proposal
# ---------------------------------------------------------------------------


@app.get("/proposals/{proposal_id}", response_model=ProposalDocument, tags=["Proposals"])
def get_proposal(proposal_id: str, version: str = "1.0") -> ProposalDocument:
    try:
        return _store.load_proposal(proposal_id, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Human review endpoints
# ---------------------------------------------------------------------------


def _apply_review_action(
    proposal_id: str,
    version: str,
    body: ApprovalRequest,
    expected_new_status: ProposalStatus,
) -> Dict[str, Any]:
    try:
        proposal = _store.load_proposal(proposal_id, version)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} v{version} not found.")

    proposal.status = expected_new_status

    # If approving, save as baseline
    if expected_new_status == ProposalStatus.APPROVED:
        _store.save_baseline(proposal)

    _store.save_proposal(proposal)

    record = ApprovalRecord(
        document_id=proposal_id,
        version=version,
        action=body.action,
        reviewer_id=body.reviewer_id,
        timestamp=datetime.utcnow(),
        notes=body.notes,
    )
    _store.save_approval(record)

    return {
        "proposal_id": proposal_id,
        "version": version,
        "new_status": expected_new_status,
        "reviewer_id": body.reviewer_id,
        "timestamp": record.timestamp.isoformat(),
    }


@app.post("/proposals/{proposal_id}/approve", tags=["Human Review"])
def approve_proposal(
    proposal_id: str,
    body: ApprovalRequest,
    version: str = "1.0",
) -> Dict[str, Any]:
    """Approve a proposal.  Saves it as the canonical baseline."""
    body.action = ApprovalAction.APPROVE
    return _apply_review_action(proposal_id, version, body, ProposalStatus.APPROVED)


@app.post("/proposals/{proposal_id}/reject", tags=["Human Review"])
def reject_proposal(
    proposal_id: str,
    body: ApprovalRequest,
    version: str = "1.0",
) -> Dict[str, Any]:
    """Reject a proposal."""
    body.action = ApprovalAction.REJECT
    return _apply_review_action(proposal_id, version, body, ProposalStatus.REJECTED)


@app.post("/proposals/{proposal_id}/request-revision", tags=["Human Review"])
def request_revision(
    proposal_id: str,
    body: ApprovalRequest,
    version: str = "1.0",
) -> Dict[str, Any]:
    """Request revision of a proposal."""
    body.action = ApprovalAction.REQUEST_REVISION
    return _apply_review_action(proposal_id, version, body, ProposalStatus.REVISION_REQUESTED)


# ---------------------------------------------------------------------------
# POST /transcripts/{followup_id}/compare/{baseline_proposal_id}
# ---------------------------------------------------------------------------


@app.post(
    "/transcripts/{followup_id}/compare/{baseline_proposal_id}",
    response_model=CompareTranscriptsResponse,
    tags=["Change Analysis"],
)
def compare_transcripts(
    followup_id: str,
    baseline_proposal_id: str,
    version: str = "1.0",
) -> CompareTranscriptsResponse:
    """Compare a follow-up transcript against an approved baseline proposal."""
    try:
        baseline = _store.load_baseline(baseline_proposal_id, version)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Approved baseline {baseline_proposal_id} v{version} not found. "
                   "Approve a proposal first.",
        )

    try:
        followup_transcript = get_transcript_by_id(followup_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    followup_reqs = _analyst.analyse(followup_transcript)

    try:
        analysis = _change_analyst.analyse_changes(baseline, followup_reqs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return CompareTranscriptsResponse(change_analysis=analysis)


# ---------------------------------------------------------------------------
# GET /audit
# ---------------------------------------------------------------------------


@app.get("/audit", tags=["Audit"])
def get_audit(proposal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the audit trail, optionally filtered by proposal_id."""
    return _store.get_audit_trail(proposal_id=proposal_id)


# ---------------------------------------------------------------------------
# GET /proposals — list all proposals
# ---------------------------------------------------------------------------


@app.get("/proposals", tags=["Proposals"])
def list_proposals() -> List[Dict[str, str]]:
    return _store.list_proposals()

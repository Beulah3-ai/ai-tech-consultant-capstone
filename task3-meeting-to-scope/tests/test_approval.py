"""Tests for approval workflow: approve, reject, request revision, audit trail."""

from __future__ import annotations

import pytest

from app.schemas import ProposalStatus


class TestApprovalWorkflow:
    def _process_transcript(self, client, transcript_id: str) -> dict:
        r = client.post(f"/transcripts/{transcript_id}/process", json={})
        assert r.status_code == 200, f"process failed: {r.text}"
        return r.json()

    def test_approve_sets_status_approved(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-A")
        pid = data["proposal_id"]
        r = test_client.post(
            f"/proposals/{pid}/approve",
            json={"action": "approve", "reviewer_id": "reviewer1"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "approved"

    def test_reject_sets_status_rejected(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-A")
        pid = data["proposal_id"]
        r = test_client.post(
            f"/proposals/{pid}/reject",
            json={"action": "reject", "reviewer_id": "reviewer2", "notes": "Too vague"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "rejected"

    def test_request_revision_sets_status(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-B")
        pid = data["proposal_id"]
        r = test_client.post(
            f"/proposals/{pid}/request-revision",
            json={"action": "request_revision", "reviewer_id": "reviewer3"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "revision_requested"

    def test_approve_nonexistent_proposal_returns_404(self, test_client):
        r = test_client.post(
            "/proposals/NONEXISTENT/approve",
            json={"action": "approve", "reviewer_id": "r"},
        )
        assert r.status_code == 404

    def test_audit_trail_populated_after_approval(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-A")
        pid = data["proposal_id"]
        test_client.post(
            f"/proposals/{pid}/approve",
            json={"action": "approve", "reviewer_id": "auditor1"},
        )
        r = test_client.get("/audit")
        assert r.status_code == 200
        trail = r.json()
        assert len(trail) >= 1

    def test_audit_trail_filter_by_proposal_id(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-B")
        pid = data["proposal_id"]
        test_client.post(
            f"/proposals/{pid}/approve",
            json={"action": "approve", "reviewer_id": "auditor2"},
        )
        r = test_client.get(f"/audit?proposal_id={pid}")
        trail = r.json()
        assert all(entry["document_id"] == pid for entry in trail)

    def test_reviewer_id_persisted_in_audit(self, test_client):
        data = self._process_transcript(test_client, "TRANSCRIPT-A")
        pid = data["proposal_id"]
        test_client.post(
            f"/proposals/{pid}/approve",
            json={"action": "approve", "reviewer_id": "specific_reviewer"},
        )
        r = test_client.get(f"/audit?proposal_id={pid}")
        trail = r.json()
        reviewer_ids = [e["reviewer_id"] for e in trail]
        assert "specific_reviewer" in reviewer_ids

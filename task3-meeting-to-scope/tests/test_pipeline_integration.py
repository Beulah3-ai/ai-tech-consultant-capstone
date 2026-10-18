"""End-to-end integration tests for the full Task 3 pipeline and API."""

from __future__ import annotations

import pytest


class TestHealth:
    def test_health_returns_200(self, test_client):
        r = test_client.get("/health")
        assert r.status_code == 200

    def test_health_status_ok(self, test_client):
        r = test_client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_service_name(self, test_client):
        r = test_client.get("/health")
        assert r.json()["service"] == "task3-meeting-to-scope"

    def test_health_provider_is_deterministic(self, test_client):
        r = test_client.get("/health")
        assert r.json()["provider"] == "deterministic_pipeline"


class TestTranscripts:
    def test_list_transcripts_returns_three(self, test_client):
        r = test_client.get("/transcripts")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3

    def test_transcript_ids_correct(self, test_client):
        r = test_client.get("/transcripts")
        ids = {t["transcript_id"] for t in r.json()}
        assert "TRANSCRIPT-A" in ids
        assert "TRANSCRIPT-B" in ids
        assert "TRANSCRIPT-C" in ids


class TestProcessPipeline:
    def test_process_transcript_a_returns_200(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        assert r.status_code == 200

    def test_process_transcript_a_status_draft(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        assert r.json()["status"] == "draft"

    def test_process_transcript_a_has_proposal(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        data = r.json()
        assert "proposal" in data
        assert data["proposal"]["provider"] == "deterministic_pipeline"

    def test_process_transcript_b_returns_200(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-B/process", json={})
        assert r.status_code == 200

    def test_process_transcript_b_has_estimation_items(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-B/process", json={})
        items = r.json()["proposal"]["estimation_items"]
        assert len(items) > 0

    def test_process_nonexistent_transcript_returns_404(self, test_client):
        r = test_client.post("/transcripts/NONEXISTENT/process", json={})
        assert r.status_code == 404

    def test_proposal_is_mock_labelled(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        assert r.json()["proposal"]["is_mock"] is True

    def test_proposal_has_caveats(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        caveats = r.json()["proposal"]["caveats"]
        assert len(caveats) > 0

    def test_proposal_total_hours_non_negative(self, test_client):
        r = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        p = r.json()["proposal"]
        assert p["total_low_hours"] >= 0
        assert p["total_likely_hours"] >= 0
        assert p["total_high_hours"] >= 0


class TestGetProposal:
    def test_get_proposal_after_processing(self, test_client):
        r1 = test_client.post("/transcripts/TRANSCRIPT-A/process", json={})
        pid = r1.json()["proposal_id"]
        r2 = test_client.get(f"/proposals/{pid}")
        assert r2.status_code == 200
        assert r2.json()["proposal_id"] == pid

    def test_get_nonexistent_proposal_returns_404(self, test_client):
        r = test_client.get("/proposals/DOES-NOT-EXIST")
        assert r.status_code == 404


class TestChangeAnalysis:
    def _process_and_approve(self, client, transcript_id: str):
        r = client.post(f"/transcripts/{transcript_id}/process", json={})
        assert r.status_code == 200, r.text
        pid = r.json()["proposal_id"]
        client.post(
            f"/proposals/{pid}/approve",
            json={"action": "approve", "reviewer_id": "test_reviewer"},
        )
        return pid

    def test_compare_requires_approved_baseline(self, test_client):
        """Comparing against a non-existent/unapproved baseline returns 404."""
        r = test_client.post("/transcripts/TRANSCRIPT-C/compare/NONEXISTENT-PROP")
        assert r.status_code == 404

    def test_compare_after_approve_succeeds(self, test_client):
        pid = self._process_and_approve(test_client, "TRANSCRIPT-A")
        r = test_client.post(f"/transcripts/TRANSCRIPT-C/compare/{pid}")
        assert r.status_code == 200

    def test_compare_returns_change_analysis(self, test_client):
        pid = self._process_and_approve(test_client, "TRANSCRIPT-A")
        r = test_client.post(f"/transcripts/TRANSCRIPT-C/compare/{pid}")
        data = r.json()
        assert "change_analysis" in data
        assert data["change_analysis"]["followup_transcript_id"] == "TRANSCRIPT-C"

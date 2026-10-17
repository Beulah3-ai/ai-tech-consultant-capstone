import tempfile
from pathlib import Path
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ingestion import IngestionService
from app.services.html_extractor import ExtractedArticle
from app.db import init_db


@pytest.fixture
def custom_test_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    init_db(db_path)

    # Insert sample article for retrieval
    ingest = IngestionService(db_path=db_path)
    ingest._upsert_article(
        ExtractedArticle(
            title="Billing Settings & Invoices",
            canonical_url="https://support.brilliantdirectories.com/articles/billing-invoices",
            clean_text="Manage monthly membership invoices, automated receipts, and retry periods under Finance > Billing Settings.",
            content_hash="billinghash123",
            last_modified="2026-05-01",
        ),
        "https://support.brilliantdirectories.com/articles/billing-invoices",
    )

    with patch.dict("os.environ", {"DATABASE_PATH": db_path}):
        with TestClient(app) as test_client:
            yield test_client, db_path

    import gc
    gc.collect()
    try:
        Path(db_path).unlink(missing_ok=True)
    except OSError:
        pass



def test_api_health_endpoint(custom_test_env):
    client, _ = custom_test_env
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "knowledge-brain"
    assert data["total_articles"] == 1


def test_api_query_local_retrieval_grounded(custom_test_env):
    client, _ = custom_test_env
    res = client.post(
        "/query",
        json={"query": "Where do I manage membership invoices?", "provider": "local_retrieval"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["answered"] is True
    assert data["provider"] == "local_retrieval"
    assert data["is_mock"] is False
    assert "Billing Settings & Invoices" in data["sources"][0]
    assert "Finance > Billing Settings" in data["answer"]


def test_api_query_local_retrieval_abstention(custom_test_env):
    client, _ = custom_test_env
    res = client.post(
        "/query",
        json={"query": "What is the capital of Australia?", "provider": "local_retrieval"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["answered"] is False
    assert data["confidence"] == 0.0
    assert data["provider"] == "local_retrieval"
    assert data["is_mock"] is False
    assert "cannot answer this question" in data["answer"]


def test_api_query_mock_provider_fallback(custom_test_env):
    client, _ = custom_test_env
    res = client.post(
        "/query",
        json={"query": "What architecture is recommended for the AI tech consultant?", "provider": "mock"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_mock"] is True
    assert data["provider"] == "mock"
    assert "[MOCK PROVIDER]" in data["answer"]


def test_api_ingestion_run_and_status(custom_test_env):
    client, _ = custom_test_env

    mock_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://support.brilliantdirectories.com/article/test</loc></url>
    </urlset>"""

    mock_html = "<html><head><title>Test Doc</title></head><body><main><h1>Test Doc</h1><p>Test Content</p></main></body></html>"

    def mock_fetch(self, client_inner, url):
        if "sitemap.xml" in url:
            return mock_sitemap
        return mock_html

    with patch.object(IngestionService, "_fetch_with_retries", side_effect=mock_fetch, autospec=True):
        res = client.post("/ingestion/run", json={"max_pages": 1, "rate_limit_delay_seconds": 0.0})
        assert res.status_code == 200
        run_data = res.json()
        assert run_data["status"] == "completed"
        assert run_data["pages_processed"] == 1

        # Check status endpoint
        status_res = client.get("/ingestion/status")
        assert status_res.status_code == 200
        st_data = status_res.json()
        assert st_data["status"] == "completed"
        assert st_data["total_articles_stored"] >= 2


def test_api_escalation_lifecycle(custom_test_env):
    client, _ = custom_test_env

    # 1. Create escalation
    create_payload = {
        "query": "How do I setup custom SSO SAML auth with Azure AD?",
        "reason": "Not covered in public Solution Center docs",
        "context": "Enterprise client security questionnaire",
    }
    create_res = client.post("/escalations", json=create_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    esc_id = created_data["id"]
    assert created_data["status"] == "pending"

    # 2. Resolve escalation
    resolve_payload = {
        "expert_answer": "Azure AD SAML SSO requires the Enterprise Identity add-on and metadata XML import.",
        "resolved_by": "Lead Identity Architect",
    }
    resolve_res = client.post(f"/escalations/{esc_id}/resolve", json=resolve_payload)
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()
    assert resolved_data["status"] == "resolved"
    assert resolved_data["resolved_by"] == "Lead Identity Architect"
    assert resolved_data["resolved_at"] is not None


def test_api_escalation_errors(custom_test_env):
    client, _ = custom_test_env

    # 404 on nonexistent escalation resolution
    resolve_res = client.post(
        "/escalations/nonexistent_id/resolve",
        json={"expert_answer": "Some answer", "resolved_by": "Expert"},
    )
    assert resolve_res.status_code == 404
    assert "not found" in resolve_res.json()["detail"].lower()

    # 422 on invalid / empty payload
    bad_create = client.post("/escalations", json={"query": "", "reason": "   "})
    assert bad_create.status_code == 422

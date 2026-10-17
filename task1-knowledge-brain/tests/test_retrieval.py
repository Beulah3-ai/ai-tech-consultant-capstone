import tempfile
from pathlib import Path
import pytest

from app.services.retrieval import LocalRetrievalService
from app.services.html_extractor import ExtractedArticle
from app.services.ingestion import IngestionService


@pytest.fixture
def populated_retrieval_service():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    service = IngestionService(db_path=path)

    # Populate sample documentation articles
    art1 = ExtractedArticle(
        title="Connecting Custom Domains",
        canonical_url="https://support.brilliantdirectories.com/articles/custom-domains",
        clean_text=(
            "To connect your custom domain to Brilliant Directories, you must update your DNS settings.\n"
            "Point your A-Record to IP address 54.208.12.34 and set a CNAME record for www to point to your site.\n"
            "SSL certificates are automatically generated after DNS points to the server."
        ),
        content_hash="hash1",
        last_modified="2026-02-15",
    )
    service._upsert_article(art1, "https://support.brilliantdirectories.com/articles/custom-domains")

    art2 = ExtractedArticle(
        title="Setting Up Stripe Payment Gateway",
        canonical_url="https://support.brilliantdirectories.com/articles/stripe-gateway",
        clean_text=(
            "Configure Stripe in the Admin Dashboard under Finance > Payment Gateways.\n"
            "Enter your Publishable Key and Secret Key from the Stripe Dashboard.\n"
            "Enable webhook endpoints to handle recurring subscription renewals and payment failures."
        ),
        content_hash="hash2",
        last_modified="2026-03-20",
    )
    service._upsert_article(art2, "https://support.brilliantdirectories.com/articles/stripe-gateway")

    retriever = LocalRetrievalService(db_path=path)
    yield retriever
    import gc
    gc.collect()
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass



def test_retrieval_grounded_answer_with_citations(populated_retrieval_service):
    response = populated_retrieval_service.query("How do I connect an A-Record for my custom domain?")

    assert response.answered is True
    assert response.confidence > 0.0
    assert response.provider == "local_retrieval"
    assert response.is_mock is False
    assert "A-Record to IP address 54.208.12.34" in response.answer
    assert len(response.sources) > 0
    assert "Connecting Custom Domains" in response.sources[0]
    assert "https://support.brilliantdirectories.com/articles/custom-domains" in response.sources[0]
    assert "Grounding Notice:" in response.disclaimer


def test_retrieval_stripe_gateway_query(populated_retrieval_service):
    response = populated_retrieval_service.query("Where do I enter Stripe publishable and secret keys?")

    assert response.answered is True
    assert response.is_mock is False
    assert "Stripe" in response.answer
    assert "Finance > Payment Gateways" in response.answer
    assert any("stripe-gateway" in src for src in response.sources)


def test_retrieval_explicit_abstention_on_missing_evidence(populated_retrieval_service):
    response = populated_retrieval_service.query("How do I bake sourdough bread with olives and herbs?")

    assert response.answered is False
    assert response.confidence == 0.0
    assert response.provider == "local_retrieval"
    assert response.is_mock is False
    assert len(response.sources) == 0
    assert "cannot answer this question based on the currently indexed" in response.answer
    assert "Insufficient evidence was found" in response.answer


def test_retrieval_query_sanitization_special_characters(populated_retrieval_service):
    # Query with punctuation and symbols that could break raw FTS5 if unhandled
    complex_query = 'domain! & (A-Record) OR "54.208.12.34"* ???'
    response = populated_retrieval_service.query(complex_query)

    # Should execute cleanly without SQLite syntax error
    assert response.provider == "local_retrieval"
    assert response.answered is True
    assert "A-Record" in response.answer

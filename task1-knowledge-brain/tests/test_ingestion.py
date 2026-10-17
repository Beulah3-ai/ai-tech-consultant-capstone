import tempfile
from pathlib import Path
import httpx
import pytest

from app.services.ingestion import IngestionService, parse_sitemap_xml
from app.db import get_db_connection

SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://support.brilliantdirectories.com/article/1</loc>
        <lastmod>2026-03-01T10:00:00Z</lastmod>
    </url>
    <url>
        <loc>https://support.brilliantdirectories.com/article/2</loc>
        <lastmod>2026-03-02T11:00:00Z</lastmod>
    </url>
    <url>
        <loc>https://support.brilliantdirectories.com/article/3</loc>
        <lastmod>2026-03-03T12:00:00Z</lastmod>
    </url>
</urlset>
"""

HTML_ARTICLE_1 = """
<html>
<head><title>Setup Stripe Payments | Brilliant Directories</title></head>
<body><main><h1>Setup Stripe Payments</h1><p>Connect your Stripe API keys in the Payment Gateway tab.</p></main></body>
</html>
"""

HTML_ARTICLE_1_MODIFIED = """
<html>
<head><title>Setup Stripe Payments | Brilliant Directories</title></head>
<body><main><h1>Setup Stripe Payments</h1><p>Connect your Stripe API keys in the Payment Gateway tab. Now supports Apple Pay.</p></main></body>
</html>
"""

HTML_ARTICLE_2 = """
<html>
<head><title>Member Levels Configuration | Brilliant Directories</title></head>
<body><main><h1>Member Levels Configuration</h1><p>Define free, premium, and trial subscription tiers.</p></main></body>
</html>
"""


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    import gc
    gc.collect()
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass



def test_parse_sitemap_xml():
    items = parse_sitemap_xml(SAMPLE_SITEMAP)
    assert len(items) == 3
    assert items[0].url == "https://support.brilliantdirectories.com/article/1"
    assert items[0].lastmod == "2026-03-01T10:00:00Z"
    assert items[2].url == "https://support.brilliantdirectories.com/article/3"


def test_ingestion_new_pages_and_bounded_limit(temp_db_path):
    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "sitemap.xml" in url:
            return httpx.Response(200, text=SAMPLE_SITEMAP)
        elif "article/1" in url:
            return httpx.Response(200, text=HTML_ARTICLE_1)
        elif "article/2" in url:
            return httpx.Response(200, text=HTML_ARTICLE_2)
        return httpx.Response(404, text="Not Found")

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    service = IngestionService(db_path=temp_db_path, http_client=mock_client)

    # Ingest bounded to max 2 pages
    result = service.run(max_pages=2, rate_limit_delay_seconds=0.0)

    assert result["status"] == "completed"
    assert result["pages_discovered"] == 3
    assert result["pages_processed"] == 2
    assert result["pages_new"] == 2
    assert result["pages_changed"] == 0
    assert result["pages_unchanged"] == 0
    assert len(result["errors"]) == 0

    status = service.get_status()
    assert status["total_articles_stored"] == 2
    assert status["status"] == "completed"


def test_idempotent_ingestion(temp_db_path):
    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "sitemap.xml" in url:
            return httpx.Response(200, text=SAMPLE_SITEMAP)
        elif "article/1" in url:
            return httpx.Response(200, text=HTML_ARTICLE_1)
        return httpx.Response(404, text="Not Found")

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    service = IngestionService(db_path=temp_db_path, http_client=mock_client)

    # First run
    run1 = service.run(max_pages=1, rate_limit_delay_seconds=0.0)
    assert run1["pages_new"] == 1
    assert run1["pages_unchanged"] == 0

    # Second run with identical content -> idempotent: 0 new, 1 unchanged
    run2 = service.run(max_pages=1, rate_limit_delay_seconds=0.0)
    assert run2["pages_new"] == 0
    assert run2["pages_changed"] == 0
    assert run2["pages_unchanged"] == 1

    # Database should still have only 1 article, no duplicate entries
    with get_db_connection(temp_db_path) as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM articles").fetchone()["c"]
        assert count == 1


def test_changed_page_detection(temp_db_path):
    current_content = {"article_1": HTML_ARTICLE_1}

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "sitemap.xml" in url:
            return httpx.Response(200, text=SAMPLE_SITEMAP)
        elif "article/1" in url:
            return httpx.Response(200, text=current_content["article_1"])
        return httpx.Response(404, text="Not Found")

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    service = IngestionService(db_path=temp_db_path, http_client=mock_client)

    # Initial ingestion
    run1 = service.run(max_pages=1, rate_limit_delay_seconds=0.0)
    assert run1["pages_new"] == 1

    # Update article content
    current_content["article_1"] = HTML_ARTICLE_1_MODIFIED

    # Second ingestion -> detects change
    run2 = service.run(max_pages=1, rate_limit_delay_seconds=0.0)
    assert run2["pages_new"] == 0
    assert run2["pages_changed"] == 1
    assert run2["pages_unchanged"] == 0

    # Verify updated content stored in database
    with get_db_connection(temp_db_path) as conn:
        row = conn.execute("SELECT clean_text FROM articles WHERE url = ?", ("https://support.brilliantdirectories.com/article/1",)).fetchone()
        assert "Apple Pay" in row["clean_text"]


def test_inaccessible_pages_and_error_handling(temp_db_path):
    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "sitemap.xml" in url:
            return httpx.Response(200, text=SAMPLE_SITEMAP)
        elif "article/1" in url:
            return httpx.Response(500, text="Internal Server Error")
        elif "article/2" in url:
            return httpx.Response(200, text=HTML_ARTICLE_2)
        return httpx.Response(404, text="Not Found")

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    service = IngestionService(db_path=temp_db_path, http_client=mock_client, max_retries=1)

    result = service.run(max_pages=2, rate_limit_delay_seconds=0.0)

    # Pipeline should not crash, article 2 is processed, article 1 logged as error
    assert result["pages_processed"] == 1
    assert result["pages_new"] == 1
    assert len(result["errors"]) == 1
    assert "article/1" in result["errors"][0]["url"]
    assert result["status"] == "partial"

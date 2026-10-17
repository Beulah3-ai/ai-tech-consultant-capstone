import pytest
from app.services.html_extractor import HTMLExtractor


def test_html_extraction_standard_article():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>How to Connect a Custom Domain | Brilliant Directories</title>
        <meta property="og:title" content="How to Connect a Custom Domain" />
        <link rel="canonical" href="https://support.brilliantdirectories.com/support/solutions/articles/custom-domain" />
        <meta property="article:modified_time" content="2026-05-12T14:30:00Z" />
    </head>
    <body>
        <nav><a href="/">Home</a><a href="/support">Support</a></nav>
        <header><h1>Header Navigation</h1></header>
        <main>
            <h1>How to Connect a Custom Domain</h1>
            <p>To connect your domain, update your A-Record to point to 54.208.12.34 in your DNS manager.</p>
            <p>Wait 24 to 48 hours for DNS propagation.</p>
        </main>
        <footer><p>Copyright 2026 Brilliant Directories</p></footer>
        <script>console.log("analytics");</script>
    </body>
    </html>
    """
    article = HTMLExtractor.extract(
        html_content=html,
        source_url="https://support.brilliantdirectories.com/support/solutions/articles/custom-domain",
    )

    assert article.title == "How to Connect a Custom Domain"
    assert article.canonical_url == "https://support.brilliantdirectories.com/support/solutions/articles/custom-domain"
    assert "update your A-Record" in article.clean_text
    assert "Wait 24 to 48 hours" in article.clean_text
    # Boilerplate should be removed
    assert "Header Navigation" not in article.clean_text
    assert "analytics" not in article.clean_text
    assert "Copyright 2026" not in article.clean_text
    assert article.last_modified == "2026-05-12T14:30:00Z"
    assert len(article.content_hash) == 64  # SHA-256


def test_html_extraction_fallback_title_and_relative_canonical():
    html = """
    <html>
    <head>
        <title>Member Import Guide - Brilliant Directories</title>
        <link rel="canonical" href="/articles/member-import" />
        <time datetime="2026-01-10">January 10, 2026</time>
    </head>
    <body>
        <article>
            <p>Use the CSV template to import members in bulk.</p>
        </article>
    </body>
    </html>
    """
    article = HTMLExtractor.extract(
        html_content=html,
        source_url="https://support.brilliantdirectories.com/support/import",
    )

    assert article.title == "Member Import Guide"
    assert article.canonical_url == "https://support.brilliantdirectories.com/articles/member-import"
    assert "Use the CSV template" in article.clean_text
    assert article.last_modified == "2026-01-10"


def test_html_extraction_malformed_html():
    malformed = """
    <div>
        <h1>Broken Layout Page
        <p>This paragraph never closes
        <span>Some detail text
    """
    article = HTMLExtractor.extract(
        html_content=malformed,
        source_url="https://support.brilliantdirectories.com/broken-page",
        fallback_timestamp="2026-04-01T00:00:00Z",
    )

    assert "Broken Layout Page" in article.title
    assert "This paragraph never closes" in article.clean_text
    assert article.last_modified == "2026-04-01T00:00:00Z"
    assert len(article.content_hash) == 64


def test_content_hash_consistency():
    html1 = "<html><body><main><p>Same exact content</p></main></body></html>"
    html2 = "<html><body><main><p>Same exact content</p></main><script>track()</script></body></html>"

    art1 = HTMLExtractor.extract(html1, "https://example.com/1")
    art2 = HTMLExtractor.extract(html2, "https://example.com/1")

    assert art1.content_hash == art2.content_hash

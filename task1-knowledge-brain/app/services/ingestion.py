import json
import logging
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

from app.db import get_db_connection, init_db
from app.services.html_extractor import HTMLExtractor, ExtractedArticle

logger = logging.getLogger(__name__)


class SitemapItem:
    def __init__(self, url: str, lastmod: Optional[str] = None):
        self.url = url
        self.lastmod = lastmod


def parse_sitemap_xml(xml_content: str) -> List[SitemapItem]:
    """
    Parse a sitemap XML document and extract article URLs and last modification dates.
    Handles XML namespaces transparently.
    """
    items: List[SitemapItem] = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse sitemap XML: {e}")
        return items

    # Strip XML namespace if present
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"

    # Handle standard <urlset><url><loc>
    for url_el in root.findall(f"{namespace}url"):
        loc_el = url_el.find(f"{namespace}loc")
        if loc_el is not None and loc_el.text:
            url = loc_el.text.strip()
            lastmod_el = url_el.find(f"{namespace}lastmod")
            lastmod = lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None
            items.append(SitemapItem(url=url, lastmod=lastmod))

    # Handle <sitemapindex><sitemap><loc>
    if not items:
        for sitemap_el in root.findall(f"{namespace}sitemap"):
            loc_el = sitemap_el.find(f"{namespace}loc")
            if loc_el is not None and loc_el.text:
                url = loc_el.text.strip()
                lastmod_el = sitemap_el.find(f"{namespace}lastmod")
                lastmod = lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None
                items.append(SitemapItem(url=url, lastmod=lastmod))

    return items


class IngestionService:
    """
    Polite, resumable, and idempotent website ingestion pipeline.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        http_client: Optional[httpx.Client] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        self.db_path = db_path
        self.http_client = http_client
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        init_db(self.db_path)

    def _get_client(self) -> httpx.Client:
        if self.http_client:
            return self.http_client
        headers = {
            "User-Agent": "AITechConsultantBot/1.0 (+https://github.com/capstone/tech-consultant; polite knowledge crawler)"
        }
        return httpx.Client(timeout=self.timeout, headers=headers, follow_redirects=True)

    def _fetch_with_retries(self, client: httpx.Client, url: str) -> Optional[str]:
        """Fetch URL content with exponential backoff retries."""
        for attempt in range(self.max_retries):
            try:
                response = client.get(url)
                if response.status_code == 200:
                    return response.text
                elif response.status_code in (404, 410):
                    logger.warning(f"Page not found ({response.status_code}): {url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code} fetching {url}, attempt {attempt + 1}")
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(f"Network error fetching {url} on attempt {attempt + 1}: {exc}")

            if attempt < self.max_retries - 1:
                sleep_time = self.backoff_factor * (2 ** attempt)
                time.sleep(sleep_time)

        return None

    def run(
        self,
        sitemap_url: str = "https://support.brilliantdirectories.com/support/sitemap.xml",
        max_pages: int = 10,
        rate_limit_delay_seconds: float = 0.1,
        force_resync: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a bounded, resumable ingestion run.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        started_at = datetime.now(timezone.utc).isoformat()

        errors: List[Dict[str, Any]] = []
        pages_discovered = 0
        pages_processed = 0
        pages_new = 0
        pages_changed = 0
        pages_unchanged = 0
        pages_removed = 0

        # Initialize run record in database
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ingestion_runs (
                    run_id, started_at, status, pages_discovered, pages_processed,
                    pages_new, pages_changed, pages_unchanged, pages_removed, errors
                ) VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, ?)
                """,
                (run_id, started_at, "running", json.dumps([])),
            )
            conn.commit()

        client = self._get_client()
        should_close_client = self.http_client is None

        try:
            # 1. Fetch sitemap
            sitemap_xml = self._fetch_with_retries(client, sitemap_url)
            if not sitemap_xml:
                err_msg = f"Failed to fetch sitemap from {sitemap_url}"
                errors.append({"url": sitemap_url, "error": err_msg, "timestamp": datetime.now(timezone.utc).isoformat()})
                self._update_run_status(
                    run_id, "failed", pages_discovered, pages_processed,
                    pages_new, pages_changed, pages_unchanged, pages_removed, errors
                )
                return {
                    "run_id": run_id,
                    "status": "failed",
                    "pages_discovered": 0,
                    "pages_processed": 0,
                    "pages_new": 0,
                    "pages_changed": 0,
                    "pages_unchanged": 0,
                    "pages_removed": 0,
                    "errors": errors,
                    "started_at": started_at,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }

            # 2. Parse sitemap items
            sitemap_items = parse_sitemap_xml(sitemap_xml)
            pages_discovered = len(sitemap_items)

            # Cap pages to process based on max_pages limit
            target_items = sitemap_items[:max_pages]

            # 3. Process each page sequentially with polite delay
            for idx, item in enumerate(target_items):
                url = item.url
                if rate_limit_delay_seconds > 0 and idx > 0:
                    time.sleep(rate_limit_delay_seconds)

                try:
                    html_content = self._fetch_with_retries(client, url)
                    if not html_content:
                        errors.append({
                            "url": url,
                            "error": "Failed to retrieve page content after retries",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        continue

                    # Extract article metadata and clean text
                    extracted = HTMLExtractor.extract(html_content, source_url=url, fallback_timestamp=item.lastmod)

                    # Store in database with idempotency and change detection
                    change_type = self._upsert_article(extracted, source_url=url, force_resync=force_resync)
                    pages_processed += 1

                    if change_type == "new":
                        pages_new += 1
                    elif change_type == "changed":
                        pages_changed += 1
                    else:
                        pages_unchanged += 1

                    # Checkpoint after each page
                    self._save_checkpoint(run_id, url, pages_processed, pages_new, pages_changed, pages_unchanged)

                except Exception as ex:
                    logger.exception(f"Unexpected error processing page {url}: {ex}")
                    errors.append({
                        "url": url,
                        "error": str(ex),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            status = "completed" if not errors else ("partial" if pages_processed > 0 else "failed")
            completed_at = datetime.now(timezone.utc).isoformat()
            self._update_run_status(
                run_id, status, pages_discovered, pages_processed,
                pages_new, pages_changed, pages_unchanged, pages_removed, errors, completed_at
            )

            return {
                "run_id": run_id,
                "status": status,
                "pages_discovered": pages_discovered,
                "pages_processed": pages_processed,
                "pages_new": pages_new,
                "pages_changed": pages_changed,
                "pages_unchanged": pages_unchanged,
                "pages_removed": pages_removed,
                "errors": errors,
                "started_at": started_at,
                "completed_at": completed_at,
            }

        finally:
            if should_close_client:
                client.close()

    def _upsert_article(self, article: ExtractedArticle, source_url: str, force_resync: bool = False) -> str:
        """
        Idempotent article upsert with hash-based change detection.
        Returns 'new', 'changed', or 'unchanged'.
        """
        now = datetime.now(timezone.utc).isoformat()

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if article exists by source URL or canonical URL
            cursor.execute(
                "SELECT id, content_hash, title FROM articles WHERE url = ? OR canonical_url = ?",
                (source_url, article.canonical_url),
            )
            existing = cursor.fetchone()

            if not existing:
                # Insert brand new article
                cursor.execute(
                    """
                    INSERT INTO articles (
                        url, canonical_url, title, content_hash, clean_text,
                        last_modified, ingested_at, updated_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        source_url,
                        article.canonical_url,
                        article.title,
                        article.content_hash,
                        article.clean_text,
                        article.last_modified,
                        now,
                        now,
                    ),
                )
                # Insert into FTS table
                cursor.execute(
                    """
                    INSERT INTO articles_fts (title, clean_text, url, canonical_url)
                    VALUES (?, ?, ?, ?)
                    """,
                    (article.title, article.clean_text, source_url, article.canonical_url),
                )
                conn.commit()
                return "new"

            existing_hash = existing["content_hash"]
            article_id = existing["id"]

            if existing_hash != article.content_hash or force_resync:
                # Article has changed: update content and FTS
                cursor.execute(
                    """
                    UPDATE articles SET
                        canonical_url = ?,
                        title = ?,
                        content_hash = ?,
                        clean_text = ?,
                        last_modified = ?,
                        updated_at = ?,
                        status = 'active'
                    WHERE id = ?
                    """,
                    (
                        article.canonical_url,
                        article.title,
                        article.content_hash,
                        article.clean_text,
                        article.last_modified,
                        now,
                        article_id,
                    ),
                )
                # Re-index in FTS
                cursor.execute("DELETE FROM articles_fts WHERE url = ?", (source_url,))
                cursor.execute(
                    """
                    INSERT INTO articles_fts (title, clean_text, url, canonical_url)
                    VALUES (?, ?, ?, ?)
                    """,
                    (article.title, article.clean_text, source_url, article.canonical_url),
                )
                conn.commit()
                return "changed"

            # Identical content: mark last checked
            cursor.execute("UPDATE articles SET status = 'active' WHERE id = ?", (article_id,))
            conn.commit()
            return "unchanged"

    def _save_checkpoint(
        self,
        run_id: str,
        checkpoint_url: str,
        processed: int,
        pages_new: int,
        pages_changed: int,
        pages_unchanged: int,
    ) -> None:
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE ingestion_runs SET
                    checkpoint_url = ?,
                    pages_processed = ?,
                    pages_new = ?,
                    pages_changed = ?,
                    pages_unchanged = ?
                WHERE run_id = ?
                """,
                (checkpoint_url, processed, pages_new, pages_changed, pages_unchanged, run_id),
            )
            conn.commit()

    def _update_run_status(
        self,
        run_id: str,
        status: str,
        discovered: int,
        processed: int,
        pages_new: int,
        pages_changed: int,
        pages_unchanged: int,
        pages_removed: int,
        errors: List[Dict[str, Any]],
        completed_at: Optional[str] = None,
    ) -> None:
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE ingestion_runs SET
                    status = ?,
                    pages_discovered = ?,
                    pages_processed = ?,
                    pages_new = ?,
                    pages_changed = ?,
                    pages_unchanged = ?,
                    pages_removed = ?,
                    errors = ?,
                    completed_at = ?
                WHERE run_id = ?
                """,
                (
                    status,
                    discovered,
                    processed,
                    pages_new,
                    pages_changed,
                    pages_unchanged,
                    pages_removed,
                    json.dumps(errors),
                    completed_at,
                    run_id,
                ),
            )
            conn.commit()

    def get_status(self) -> Dict[str, Any]:
        """Fetch status of latest run and overall article count."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Total active articles in DB
            cursor.execute("SELECT COUNT(*) AS total FROM articles WHERE status = 'active'")
            total_articles = cursor.fetchone()["total"]

            # Latest run info
            cursor.execute("SELECT * FROM ingestion_runs ORDER BY started_at DESC LIMIT 1")
            latest_run = cursor.fetchone()

            if not latest_run:
                return {
                    "status": "idle",
                    "last_run_id": None,
                    "last_started_at": None,
                    "last_completed_at": None,
                    "total_articles_stored": total_articles,
                    "pages_new": 0,
                    "pages_changed": 0,
                    "pages_unchanged": 0,
                    "pages_removed": 0,
                    "errors_count": 0,
                    "recent_errors": [],
                }

            errors = []
            if latest_run["errors"]:
                try:
                    errors = json.loads(latest_run["errors"])
                except Exception:
                    errors = []

            return {
                "status": latest_run["status"],
                "last_run_id": latest_run["run_id"],
                "last_started_at": latest_run["started_at"],
                "last_completed_at": latest_run["completed_at"],
                "total_articles_stored": total_articles,
                "pages_new": latest_run["pages_new"],
                "pages_changed": latest_run["pages_changed"],
                "pages_unchanged": latest_run["pages_unchanged"],
                "pages_removed": latest_run["pages_removed"],
                "errors_count": len(errors),
                "recent_errors": errors[-5:],  # Return up to 5 most recent errors
            }

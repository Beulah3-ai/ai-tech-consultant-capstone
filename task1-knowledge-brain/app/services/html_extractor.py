import hashlib
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup


@dataclass
class ExtractedArticle:
    title: str
    canonical_url: str
    clean_text: str
    content_hash: str
    last_modified: Optional[str] = None


class HTMLExtractor:
    """
    Robust HTML extractor for articles and documentation pages.
    Extracts title, canonical URL, cleaned text, and modification timestamp,
    handling malformed HTML and removing noise/navigation elements.
    """

    UNWANTED_TAGS = {
        "script", "style", "nav", "footer", "header", "aside",
        "form", "noscript", "svg", "iframe", "button"
    }

    SITE_SUFFIXES = [
        re.compile(r"\s*[\|\-•]\s*Brilliant Directories.*$", re.IGNORECASE),
        re.compile(r"\s*[\|\-•]\s*Solution Center.*$", re.IGNORECASE),
        re.compile(r"\s*[\|\-•]\s*Support.*$", re.IGNORECASE),
    ]

    @classmethod
    def extract(cls, html_content: str, source_url: str, fallback_timestamp: Optional[str] = None) -> ExtractedArticle:
        """Parse HTML string and extract clean structured article metadata and text."""
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract canonical URL
        canonical_url = source_url
        canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r.lower())
        if canonical_tag and canonical_tag.get("href"):
            raw_href = canonical_tag["href"].strip()
            if raw_href:
                canonical_url = urljoin(source_url, raw_href)

        # 2. Extract Title
        title = ""
        # Check OpenGraph title
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

        # Check <h1> if og:title missing
        if not title:
            h1 = soup.find("h1")
            if h1 and h1.get_text():
                title = h1.get_text().strip()

        # Check <title> tag
        if not title:
            title_tag = soup.find("title")
            if title_tag and title_tag.get_text():
                title = title_tag.get_text().strip()

        # Strip common site suffixes from title
        if title:
            for pattern in cls.SITE_SUFFIXES:
                title = pattern.sub("", title).strip()

        if not title:
            # Fallback title from URL
            title = source_url.rstrip("/").split("/")[-1].replace("-", " ").title() or "Documentation Article"

        # 3. Extract last modified timestamp
        last_modified = fallback_timestamp
        for meta_prop in ["article:modified_time", "article:published_time", "og:updated_time"]:
            tag = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop})
            if tag and tag.get("content"):
                last_modified = tag["content"].strip()
                break

        if not last_modified:
            time_tag = soup.find("time")
            if time_tag and time_tag.get("datetime"):
                last_modified = time_tag["datetime"].strip()

        # 4. Clean text extraction
        # Remove noisy and boilerplate tags
        for tag_name in cls.UNWANTED_TAGS:
            for el in soup.find_all(tag_name):
                el.decompose()

        # Look for core article or main content container
        content_container = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id=re.compile(r"article|content|main", re.IGNORECASE))
            or soup.find(class_=re.compile(r"article-content|knowledge-base|entry-content", re.IGNORECASE))
            or soup.body
            or soup
        )

        raw_text = content_container.get_text(separator="\n")

        # Clean and normalize whitespace
        lines = [line.strip() for line in raw_text.splitlines()]
        # Remove empty lines and collapse excessive spacing
        clean_lines = [line for line in lines if line]
        clean_text = "\n".join(clean_lines).strip()

        if not clean_text:
            clean_text = title

        # 5. Content hash calculation
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        return ExtractedArticle(
            title=title,
            canonical_url=canonical_url,
            clean_text=clean_text,
            content_hash=content_hash,
            last_modified=last_modified,
        )

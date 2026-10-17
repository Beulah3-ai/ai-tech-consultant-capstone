import re
from dataclasses import dataclass
from typing import List, Optional, Set
from app.db import get_db_connection, init_db
from app.schemas import QueryResponse

GROUNDING_DISCLAIMER = (
    "Grounding Notice: Retrieved from local Brilliant Directories knowledge base "
    "via keyword and SQLite FTS5 search."
)

ABSTENTION_ANSWER = (
    "I cannot answer this question based on the currently indexed Brilliant Directories knowledge base. "
    "Insufficient evidence was found. You may escalate this question to an expert for review."
)

STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


@dataclass
class SearchResult:
    title: str
    canonical_url: str
    clean_text: str
    score: float


class BaseRetriever:
    """Base interface for knowledge retrieval services."""

    def retrieve(self, query_text: str, top_k: int = 3) -> List[SearchResult]:
        raise NotImplementedError

    def query(self, question: str) -> QueryResponse:
        raise NotImplementedError


class LocalRetrievalService(BaseRetriever):
    """
    Local retrieval service utilizing SQLite FTS5 full-text search with BM25 ranking.
    Provides grounded answers with citations and explicit abstention when evidence is insufficient.
    """

    def __init__(self, db_path: Optional[str] = None, relevance_threshold: float = 0.25):
        self.db_path = db_path
        self.relevance_threshold = relevance_threshold
        init_db(self.db_path)

    def _extract_meaningful_tokens(self, query_text: str) -> List[str]:
        """Extract alphanumeric tokens excluding short tokens and common English stopwords."""
        raw_tokens = re.findall(r"\w+", query_text)
        meaningful = [
            t.lower() for t in raw_tokens
            if len(t) >= 2 and t.lower() not in STOPWORDS
        ]
        return meaningful

    def _sanitize_fts_query(self, meaningful_tokens: List[str]) -> str:
        """Create sanitized FTS5 OR query from meaningful tokens."""
        if not meaningful_tokens:
            return ""
        return " OR ".join(f'"{token}"' for token in meaningful_tokens)

    def retrieve(self, query_text: str, top_k: int = 3) -> List[SearchResult]:
        """Query the SQLite knowledge base using FTS5 with BM25 ranking and keyword verification."""
        meaningful_tokens = self._extract_meaningful_tokens(query_text)
        if not meaningful_tokens:
            return []

        fts_query = self._sanitize_fts_query(meaningful_tokens)
        results: List[SearchResult] = []

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            if fts_query:
                try:
                    cursor.execute(
                        """
                        SELECT title, canonical_url, clean_text, bm25(articles_fts) AS rank
                        FROM articles_fts
                        WHERE articles_fts MATCH ?
                        ORDER BY rank ASC
                        LIMIT ?
                        """,
                        (fts_query, top_k * 2),
                    )
                    rows = cursor.fetchall()
                    for row in rows:
                        title_lower = row["title"].lower()
                        text_lower = row["clean_text"].lower()

                        # Verify at least one meaningful token is present in title or content
                        matched_tokens = {
                            t for t in meaningful_tokens
                            if t in title_lower or t in text_lower
                        }
                        if not matched_tokens:
                            continue

                        overlap_ratio = len(matched_tokens) / len(meaningful_tokens)
                        score = max(0.1, min(0.99, round(overlap_ratio, 2)))

                        if score >= self.relevance_threshold:
                            results.append(
                                SearchResult(
                                    title=row["title"],
                                    canonical_url=row["canonical_url"],
                                    clean_text=row["clean_text"],
                                    score=score,
                                )
                            )
                except Exception:
                    results = []

            # Fallback to LIKE query if FTS yielded no results
            if not results:
                like_patterns = [f"%{token}%" for token in meaningful_tokens[:4]]
                conditions = " OR ".join(["clean_text LIKE ? OR title LIKE ?" for _ in like_patterns])
                params = []
                for pat in like_patterns:
                    params.extend([pat, pat])
                params.append(top_k)

                cursor.execute(
                    f"""
                    SELECT title, canonical_url, clean_text
                    FROM articles
                    WHERE status = 'active' AND ({conditions})
                    LIMIT ?
                    """,
                    params,
                )
                for row in cursor.fetchall():
                    title_lower = row["title"].lower()
                    text_lower = row["clean_text"].lower()
                    matched_tokens = {
                        t for t in meaningful_tokens
                        if t in title_lower or t in text_lower
                    }
                    if not matched_tokens:
                        continue
                    score = max(0.1, min(0.99, round(len(matched_tokens) / len(meaningful_tokens), 2)))
                    if score >= self.relevance_threshold:
                        results.append(
                            SearchResult(
                                title=row["title"],
                                canonical_url=row["canonical_url"],
                                clean_text=row["clean_text"],
                                score=score,
                            )
                        )

        # Sort results by score descending and take top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _extract_relevant_excerpt(self, clean_text: str, query_tokens: List[str], max_len: int = 500) -> str:
        """Find matching paragraphs containing query tokens and combine them."""
        paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
        matching_paragraphs = []

        for p in paragraphs:
            if any(t.lower() in p.lower() for t in query_tokens):
                matching_paragraphs.append(p)

        if matching_paragraphs:
            combined = "\n".join(matching_paragraphs)
            if len(combined) <= max_len:
                return combined
            return combined[:max_len].rsplit(" ", 1)[0] + "..."

        return clean_text[:max_len]

    def query(self, question: str) -> QueryResponse:
        """Process question: retrieve documents and formulate grounded answer or abstain."""
        results = self.retrieve(question, top_k=3)

        if not results:
            return QueryResponse(
                query=question,
                answer=ABSTENTION_ANSWER,
                answered=False,
                confidence=0.0,
                provider="local_retrieval",
                is_mock=False,
                sources=[],
                disclaimer=GROUNDING_DISCLAIMER,
            )

        top_match = results[0]
        if top_match.score < self.relevance_threshold:
            return QueryResponse(
                query=question,
                answer=ABSTENTION_ANSWER,
                answered=False,
                confidence=0.0,
                provider="local_retrieval",
                is_mock=False,
                sources=[],
                disclaimer=GROUNDING_DISCLAIMER,
            )

        meaningful_tokens = self._extract_meaningful_tokens(question)
        excerpt = self._extract_relevant_excerpt(top_match.clean_text, meaningful_tokens)

        answer = (
            f"According to the Brilliant Directories documentation for '{top_match.title}':\n\n"
            f"{excerpt}\n\n"
            f"Source reference: {top_match.canonical_url}"
        )

        sources = [f"{r.title} ({r.canonical_url})" for r in results if r.canonical_url]

        return QueryResponse(
            query=question,
            answer=answer,
            answered=True,
            confidence=round(top_match.score, 2),
            provider="local_retrieval",
            is_mock=False,
            sources=sources,
            disclaimer=GROUNDING_DISCLAIMER,
        )

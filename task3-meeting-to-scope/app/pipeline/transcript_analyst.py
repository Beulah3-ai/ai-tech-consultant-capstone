"""Transcript Analyst: extracts structured requirements from a meeting transcript.

Uses deterministic keyword/rule-based extraction.  No LLM is called here.
All output is explicitly labelled as coming from a deterministic pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.schemas import (
    ExtractedRequirement,
    RequirementType,
    RequirementsDocument,
    TranscriptSegmentRef,
    VerificationStatus,
)


# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

_GOAL_KEYWORDS = [
    "goal", "objective", "aim", "purpose", "primary", "mission",
    "launch", "unified", "connect", "achieve",
]
_FUNCTIONAL_KEYWORDS = [
    "need", "require", "must", "should", "want", "implement",
    "support", "integrate", "allow", "enable", "provide",
    "search", "filter", "checkout", "notification", "dashboard",
    "import", "export", "refund", "sync", "automate",
]
_NON_FUNCTIONAL_KEYWORDS = [
    "performance", "availability", "accessibility", "wcag", "uptime",
    "scalable", "secure", "compliance", "pci", "gdpr", "saq",
    "response time", "latency", "concurrent", "reliability",
]
_CONSTRAINT_KEYWORDS = [
    "budget", "timeline", "deadline", "week", "cost", "cap",
    "cannot", "limit", "constraint", "no custom server", "shared hosting",
    "must not", "not allowed", "within", "no third-party", "browser-native only",
]
_ASSUMPTION_KEYWORDS = [
    "assume", "assumption", "expect", "believing", "presuming",
    "provided that", "based on", "as long as",
]
_OPEN_QUESTION_KEYWORDS = [
    "question", "open question", "unclear", "tbd", "to be determined",
    "feasible", "can we", "is it possible", "wondering", "inquire",
    "whether", "will you", "do you",
]
_DEPENDENCY_KEYWORDS = [
    "depend", "require third", "integration", "stripe", "salesforce",
    "apple pay", "google pay", "web speech api", "okta", "azure ad",
    "cms", "api", "webhook",
]
_USER_NEED_KEYWORDS = [
    "user", "customer", "visitor", "patient", "member", "provider",
    "reviewer", "shopper", "buyer",
]
_OUT_OF_SCOPE_KEYWORDS = [
    "out of scope", "not in scope", "separate project", "future phase",
    "not part of", "excluded", "will not", "not included",
]


def _score_text(text: str, keywords: List[str]) -> float:
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw in lower)
    return min(hits / max(len(keywords) * 0.15, 1), 1.0)


def _classify_segment(text: str) -> List[RequirementType]:
    """Return ordered list of best-matching requirement types for a segment."""
    lower = text.lower()

    # Unresolved questions are not commitments to deliver the feature.
    if (
        "?" in text
        or any(
            marker in lower
            for marker in (
                "open question",
                "to be determined",
                "tbd",
                "wondering",
                "want to know if",
                "want to know whether",
                "not sure",
                "is it possible",
                "can we",
                "could we",
            )
        )
    ):
        return [RequirementType.OPEN_QUESTION]

    # Hard rule: explicit out-of-scope marker → skip (return empty)
    if any(kw in lower for kw in _OUT_OF_SCOPE_KEYWORDS):
        return []

    scores: List[Tuple[float, RequirementType]] = [
        (_score_text(lower, _GOAL_KEYWORDS), RequirementType.BUSINESS_GOAL),
        (_score_text(lower, _FUNCTIONAL_KEYWORDS), RequirementType.FUNCTIONAL),
        (_score_text(lower, _NON_FUNCTIONAL_KEYWORDS), RequirementType.NON_FUNCTIONAL),
        (_score_text(lower, _CONSTRAINT_KEYWORDS), RequirementType.CONSTRAINT),
        (_score_text(lower, _ASSUMPTION_KEYWORDS), RequirementType.ASSUMPTION),
        (_score_text(lower, _OPEN_QUESTION_KEYWORDS), RequirementType.OPEN_QUESTION),
        (_score_text(lower, _DEPENDENCY_KEYWORDS), RequirementType.DEPENDENCY),
        (_score_text(lower, _USER_NEED_KEYWORDS), RequirementType.USER_NEED),
    ]

    # Use the strongest single type to avoid duplicating one statement.
    threshold = 0.08
    best_score, best_type = max(scores, key=lambda item: item[0])
    return [best_type] if best_score >= threshold else []


def _extract_tags(text: str) -> List[str]:
    tags = []
    lower = text.lower()
    if "stripe" in lower:
        tags.append("stripe")
    if any(k in lower for k in ["search", "full-text", "keyword"]):
        tags.append("search")
    if "filter" in lower:
        tags.append("filters")
    if "mobile" in lower:
        tags.append("mobile")
    if "wcag" in lower or "accessibility" in lower:
        tags.append("accessibility")
    if any(k in lower for k in ["checkout", "cart", "payment"]):
        tags.append("checkout")
    if any(k in lower for k in ["notification", "email alert"]):
        tags.append("notifications")
    if "voice" in lower:
        tags.append("voice-search")
    if any(k in lower for k in ["budget", "cost", "$"]):
        tags.append("budget")
    if any(k in lower for k in ["timeline", "week", "deadline"]):
        tags.append("timeline")
    return tags


def _is_consultant_speaker(speaker: str) -> bool:
    lower = speaker.lower()
    return any(word in lower for word in ["consultant", "architect", "analyst"])


def _normalise_requirement_text(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def _chunk_segment(text: str, max_chars: int = 1000) -> List[str]:
    """Split long segment text into overlapping chunks for analysis."""
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_chars and current:
            chunks.append(current.strip())
            # Overlap: keep last sentence for context
            current = sentence
        else:
            current = (current + " " + sentence).strip()
    if current:
        chunks.append(current.strip())
    return chunks


class TranscriptAnalyst:
    """Extracts structured requirements from a synthetic meeting transcript.

    This is a deterministic rule-based extractor.  It does NOT call any
    language model.  All outputs are labelled ``provider='deterministic_pipeline'``.
    """

    def analyse(self, transcript: Dict[str, Any]) -> RequirementsDocument:
        """Process all segments of a transcript and return a RequirementsDocument."""
        transcript_id: str = transcript["transcript_id"]
        doc = RequirementsDocument(transcript_id=transcript_id)
        counter: int = 0

        for seg in transcript.get("segments", []):
            seg_id: str = seg["segment_id"]
            line_num: int = seg["line_number"]
            speaker: str = seg["speaker"]
            text: str = seg["text"]

            if _is_consultant_speaker(speaker):
                continue

            ref = TranscriptSegmentRef(
                transcript_id=transcript_id,
                segment_id=seg_id,
                line_number=line_num,
                speaker=speaker,
            )

            # Chunk long segments
            chunks = [
                sentence.strip()
                for chunk in _chunk_segment(text, max_chars=800)
                for sentence in re.split(r"(?<=[.!?])\s+", chunk)
                if sentence.strip()
            ]

            for chunk in chunks:
                types = _classify_segment(chunk)
                if not types:
                    continue

                for req_type in types:
                    tags = _extract_tags(chunk)

                    req = ExtractedRequirement(
                        req_id=f"{transcript_id}-REQ-{counter + 1:03d}",
                        req_type=req_type,
                        description=chunk.strip(),
                        sources=[ref],
                        confidence=0.7,
                        verification_status=VerificationStatus.UNVERIFIED,
                        tags=tags,
                    )

                    if _add_to_document(doc, req):
                        counter += 1

        return doc


def _add_to_document(doc: RequirementsDocument, req: ExtractedRequirement) -> bool:
    """Append a requirement or merge its source into an equivalent one."""
    mapping = {
        RequirementType.BUSINESS_GOAL: doc.business_goals,
        RequirementType.USER_NEED: doc.user_needs,
        RequirementType.FUNCTIONAL: doc.functional_requirements,
        RequirementType.NON_FUNCTIONAL: doc.non_functional_requirements,
        RequirementType.CONSTRAINT: doc.constraints,
        RequirementType.ASSUMPTION: doc.assumptions,
        RequirementType.DEPENDENCY: doc.dependencies,
        RequirementType.OPEN_QUESTION: doc.open_questions,
    }
    destination = mapping[req.req_type]
    normalized = _normalise_requirement_text(req.description)
    for existing in destination:
        if _normalise_requirement_text(existing.description) == normalized:
            for source in req.sources:
                if source not in existing.sources:
                    existing.sources.append(source)
            existing.tags = list(dict.fromkeys(existing.tags + req.tags))
            existing.confidence = max(existing.confidence, req.confidence)
            return False

    destination.append(req)
    return True

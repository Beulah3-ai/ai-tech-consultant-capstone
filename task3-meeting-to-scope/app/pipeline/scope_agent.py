"""Scope Agent: maps extracted requirements to a structured ScopeDocument.

Deterministic rule-based mapping.  No LLM involved.
"""

from __future__ import annotations

import re
from typing import List

from app.schemas import (
    ExtractedRequirement,
    FeasibilityFinding,
    RequirementType,
    RequirementsDocument,
    ScopeDocument,
    ScopeItem,
)

_OUT_OF_SCOPE_PHRASES = [
    "out of scope",
    "not in scope",
    "separate project",
    "future phase",
    "not part of",
    "excluded",
    "will not",
    "is not designed to",
    "not included",
    "candidate for a future",
]


def _looks_out_of_scope(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in _OUT_OF_SCOPE_PHRASES)


def _normalise_text(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def _build_scope_item(
    req: ExtractedRequirement,
    feasibility_findings: List[FeasibilityFinding],
) -> ScopeItem:
    """Build a ScopeItem for a requirement, attaching any relevant KB note."""
    note: str | None = None
    for f in feasibility_findings:
        if f.answered and any(
            tag in f.question.lower() for tag in req.tags
        ):
            note = f"KB: {f.kb_answer[:200]}" if f.kb_answer else None
            break
    return ScopeItem(
        description=req.description,
        source_req_ids=[req.req_id],
        feasibility_note=note,
    )


class ScopeAgent:
    """Maps RequirementsDocument + FeasibilityFindings → ScopeDocument."""

    def generate_scope(
        self,
        reqs: RequirementsDocument,
        findings: List[FeasibilityFinding],
    ) -> ScopeDocument:
        doc = ScopeDocument(transcript_id=reqs.transcript_id)
        open_question_text = {
            _normalise_text(req.description) for req in reqs.open_questions
        }

        # --- Objectives from business goals ---
        for req in reqs.business_goals:
            if (
                not _looks_out_of_scope(req.description)
                and _normalise_text(req.description) not in open_question_text
            ):
                doc.objectives.append(req.description)

        # --- Deliverables from functional requirements ---
        for req in reqs.functional_requirements:
            if _normalise_text(req.description) in open_question_text:
                continue
            if _looks_out_of_scope(req.description):
                doc.out_of_scope.append(req.description)
            else:
                doc.deliverables.append(_build_scope_item(req, findings))
                doc.in_scope.append(_build_scope_item(req, findings))

        # --- User needs → in_scope ---
        for req in reqs.user_needs:
            if (
                not _looks_out_of_scope(req.description)
                and _normalise_text(req.description) not in open_question_text
            ):
                doc.in_scope.append(
                    ScopeItem(
                        description=req.description,
                        source_req_ids=[req.req_id],
                    )
                )

        # --- Constraints → assumptions or out of scope ---
        for req in reqs.constraints:
            if _looks_out_of_scope(req.description):
                doc.out_of_scope.append(req.description)
            else:
                doc.assumptions.append(req.description)

        # --- Assumptions ---
        for req in reqs.assumptions:
            doc.assumptions.append(req.description)

        # --- Dependencies ---
        for req in reqs.dependencies:
            if not _looks_out_of_scope(req.description):
                doc.dependencies.append(req.description)

        # --- Open questions ---
        for req in reqs.open_questions:
            doc.open_questions.append(req.description)

        # --- Non-functional → acceptance criteria ---
        for req in reqs.non_functional_requirements:
            doc.acceptance_criteria.append(req.description)

        # --- Risks from unanswered feasibility questions ---
        for f in findings:
            if not f.answered:
                risk = f"Unresolved feasibility question: '{f.question}'"
                if f.error:
                    risk += f" (KB error: {f.error})"
                doc.risks.append(risk)

        # --- Acceptance criteria: add KB-confirmed items ---
        for f in findings:
            if f.answered and f.confidence >= 0.5:
                doc.acceptance_criteria.append(
                    f"Confirmed feasible via Knowledge Brain: {f.question}"
                )

        # De-duplicate
        doc.out_of_scope = list(dict.fromkeys(doc.out_of_scope))
        doc.assumptions = list(dict.fromkeys(doc.assumptions))
        doc.dependencies = list(dict.fromkeys(doc.dependencies))
        doc.open_questions = list(dict.fromkeys(doc.open_questions))
        doc.risks = list(dict.fromkeys(doc.risks))
        doc.acceptance_criteria = list(dict.fromkeys(doc.acceptance_criteria))

        return doc

"""Proposal Agent: assembles and validates a ProposalDocument (always DRAFT).

No LLM used.  Consistency is validated deterministically.
"""

from __future__ import annotations

import uuid
from datetime import datetime
import math
import re
from typing import List, Optional

from app.schemas import (
    EstimationItem,
    Milestone,
    ProposalDocument,
    ProposalStatus,
    ScopeDocument,
)

_TIMELINE_PATTERNS = (
    re.compile(r"\bwithin\s+(\d+)\s+weeks?\b", re.IGNORECASE),
    re.compile(
        r"\bdelivery\s+timeline\s+(?:of\s+)?(\d+)\s+weeks?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\btimeline\s+(?:(?:remains|is|of)\s+)?(\d+)\s+weeks?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdeadline\s+(?:(?:is|of)\s+)?(\d+)\s+weeks?\b",
        re.IGNORECASE,
    ),
)


class ProposalAgent:
    """Assembles ProposalDocument from ScopeDocument + EstimationItem list.

    Status is always DRAFT until a human approves via the API.
    """

    def generate_proposal(
        self,
        scope: ScopeDocument,
        estimation_items: List[EstimationItem],
        proposal_id: Optional[str] = None,
        version: str = "1.0",
    ) -> ProposalDocument:
        pid = proposal_id or f"PROP-{scope.transcript_id}-{uuid.uuid4().hex[:8].upper()}"

        caveats = [
            "All estimates are approximations produced by a deterministic rule-based pipeline.",
            "No AI language model was used to generate this proposal.",
            "Estimates must be reviewed and confirmed by a qualified consultant before quoting.",
            "Knowledge Brain integration notes are sourced from the Task 1 retrieval service.",
        ]

        # Consistency check: deliverables without estimates
        warnings: List[str] = []
        deliverable_descs = {d.description[:60] for d in scope.deliverables}
        estimated_descs = {i.source_deliverable[:60] for i in estimation_items if i.source_deliverable}
        unestimated = deliverable_descs - estimated_descs
        for d in unestimated:
            warnings.append(f"Deliverable has no estimate: '{d}'")

        if not scope.deliverables:
            warnings.append("No deliverables found in scope document.")

        if not estimation_items:
            warnings.append("No estimation items produced; proposal totals will be zero.")

        deadline_weeks, ambiguous_deadline = _extract_deadline_weeks(scope)
        if ambiguous_deadline:
            warnings.append(
                "Project timeline is ambiguous; milestone scheduling is omitted until clarified."
            )
        elif deadline_weeks is None:
            warnings.append(
                "No project deadline was found; milestone scheduling is omitted."
            )
        else:
            warnings.append(
                "Timeline feasibility is unverified; estimated effort has not been "
                "validated against team capacity, availability, or dependencies."
            )

        # Compute totals
        total_low = sum(e.low_hours for e in estimation_items)
        total_likely = sum(e.likely_hours for e in estimation_items)
        total_high = sum(e.high_hours for e in estimation_items)

        milestones = _generate_milestones(estimation_items, deadline_weeks)

        return ProposalDocument(
            proposal_id=pid,
            version=version,
            transcript_id=scope.transcript_id,
            created_at=datetime.utcnow(),
            scope=scope,
            estimation_items=estimation_items,
            milestones=milestones,
            total_low_hours=total_low,
            total_likely_hours=total_likely,
            total_high_hours=total_high,
            caveats=caveats,
            status=ProposalStatus.DRAFT,
            consistency_warnings=warnings,
            provider="deterministic_pipeline",
            is_mock=True,
        )


def _generate_milestones(
    items: List[EstimationItem],
    deadline_weeks: Optional[int] = None,
) -> List[Milestone]:
    """Generate rough phase milestones bounded by an explicit project deadline."""
    if not items or deadline_weeks is None:
        return []

    n = len(items)
    first_end = n // 3
    second_end = (2 * n) // 3
    milestone_weeks = (
        math.ceil(deadline_weeks / 3),
        math.ceil(2 * deadline_weeks / 3),
        deadline_weeks,
    )

    phase_items = (
        items[:first_end],
        items[first_end:second_end],
        items[second_end:],
    )
    phase_names = (
        "Discovery & Setup",
        "Core Development",
        "Testing & Delivery",
    )

    milestones: List[Milestone] = []
    for index, (name, week, deliverables) in enumerate(
        zip(phase_names, milestone_weeks, phase_items)
    ):
        if deliverables or index == len(phase_names) - 1:
            milestones.append(
                Milestone(
                    name=name,
                    week=week,
                    deliverables=[item.task[:80] for item in deliverables],
                )
            )

    return milestones


def _extract_deadline_weeks(scope: ScopeDocument) -> tuple[Optional[int], bool]:
    """Return a unique explicit week deadline found in the extracted scope."""
    texts = [
        *scope.objectives,
        *(item.description for item in scope.deliverables),
        *(item.description for item in scope.in_scope),
        *scope.assumptions,
    ]
    deadlines = {
        int(match.group(1))
        for text in texts
        for pattern in _TIMELINE_PATTERNS
        for match in pattern.finditer(text)
        if int(match.group(1)) > 0
    }
    if len(deadlines) > 1:
        return None, True
    if not deadlines:
        return None, False
    return deadlines.pop(), False

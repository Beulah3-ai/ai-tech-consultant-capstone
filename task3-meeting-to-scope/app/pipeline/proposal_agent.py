"""Proposal Agent: assembles and validates a ProposalDocument (always DRAFT).

No LLM used.  Consistency is validated deterministically.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas import (
    EstimationItem,
    Milestone,
    ProposalDocument,
    ProposalStatus,
    ScopeDocument,
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

        # Compute totals
        total_low = sum(e.low_hours for e in estimation_items)
        total_likely = sum(e.likely_hours for e in estimation_items)
        total_high = sum(e.high_hours for e in estimation_items)

        # Generate simple milestones
        milestones = _generate_milestones(scope, estimation_items)

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
    scope: ScopeDocument,
    items: List[EstimationItem],
) -> List[Milestone]:
    """Generate rough phase milestones from deliverables."""
    if not items:
        return []

    # Split deliverables into thirds for 3 milestones
    n = len(items)
    third = max(1, n // 3)

    milestones = []
    phases = [
        ("Discovery & Setup", 2, items[:third]),
        ("Core Development", 5, items[third : third * 2]),
        ("Testing & Delivery", 7, items[third * 2 :]),
    ]

    for name, week, phase_items in phases:
        if phase_items:
            milestones.append(
                Milestone(
                    name=name,
                    week=week,
                    deliverables=[i.task[:80] for i in phase_items],
                )
            )

    return milestones

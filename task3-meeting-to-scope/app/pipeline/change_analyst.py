"""Change Analyst: compares a follow-up transcript against an approved baseline proposal.

Classifies changes as ADDITION, MODIFICATION, REMOVAL, or OUT_OF_SCOPE.
Requires an approved baseline; rejects unapproved baselines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.schemas import (
    ChangeAnalysis,
    ChangeRecord,
    ChangeType,
    ExtractedRequirement,
    ProposalDocument,
    ProposalStatus,
    RequirementsDocument,
    RevisedEstimateItem,
    TranscriptSegmentRef,
)

_ADDITION_KEYWORDS = ["add", "addition", "new requirement", "we need to add", "scope addition"]
_MODIFICATION_KEYWORDS = ["modify", "modification", "change", "update", "revised", "instead of", "replaces"]
_REMOVAL_KEYWORDS = ["remove", "removal", "drop", "eliminate", "no longer", "removed", "removing"]
_OUT_OF_SCOPE_KEYWORDS = [
    "out of scope", "not in scope", "separate project", "future phase",
    "not designed to", "excluded",
]

_EFFORT_DELTA_TABLE: Dict[ChangeType, str] = {
    ChangeType.ADDITION: "Additional effort required — see estimation agent for new items.",
    ChangeType.MODIFICATION: "Existing estimate may need revision; pending scope review.",
    ChangeType.REMOVAL: "Removes corresponding estimate from total.",
    ChangeType.OUT_OF_SCOPE: "No estimate impact; item explicitly out of scope.",
}


def _detect_change_type(text: str) -> Optional[ChangeType]:
    lower = text.lower()
    if any(kw in lower for kw in _OUT_OF_SCOPE_KEYWORDS):
        return ChangeType.OUT_OF_SCOPE
    if any(kw in lower for kw in _REMOVAL_KEYWORDS):
        return ChangeType.REMOVAL
    if any(kw in lower for kw in _MODIFICATION_KEYWORDS):
        return ChangeType.MODIFICATION
    if any(kw in lower for kw in _ADDITION_KEYWORDS):
        return ChangeType.ADDITION
    return None


def _build_revised_estimate(change: ChangeRecord) -> Optional[RevisedEstimateItem]:
    if change.change_type == ChangeType.REMOVAL:
        return RevisedEstimateItem(
            task=change.description[:80],
            reason="Removed from scope",
            low_hours=0,
            likely_hours=0,
            high_hours=0,
        )
    if change.change_type == ChangeType.ADDITION:
        return RevisedEstimateItem(
            task=change.description[:80],
            reason="New scope addition — estimate TBD after technical review",
            low_hours=4,
            likely_hours=8,
            high_hours=16,
        )
    if change.change_type == ChangeType.MODIFICATION:
        return RevisedEstimateItem(
            task=change.description[:80],
            reason="Scope modified — existing estimate needs revision",
            low_hours=2,
            likely_hours=6,
            high_hours=12,
        )
    return None


class ChangeAnalyst:
    """Compares a follow-up RequirementsDocument against an approved baseline ProposalDocument."""

    def analyse_changes(
        self,
        baseline: ProposalDocument,
        followup_reqs: RequirementsDocument,
    ) -> ChangeAnalysis:
        if baseline.status != ProposalStatus.APPROVED:
            raise ValueError(
                f"Baseline proposal '{baseline.proposal_id}' is not APPROVED "
                f"(status={baseline.status}). Change analysis requires an approved baseline."
            )

        changes: List[ChangeRecord] = []
        revised: List[RevisedEstimateItem] = []

        all_followup_reqs: List[ExtractedRequirement] = followup_reqs.all_requirements()

        for req in all_followup_reqs:
            change_type = _detect_change_type(req.description)
            if change_type is None:
                # Not explicitly a change signal — check if it's new vs baseline
                change_type = _check_if_new(req, baseline)
                if change_type is None:
                    continue

            followup_ref: Optional[TranscriptSegmentRef] = (
                req.sources[0] if req.sources else None
            )
            original_ref = _find_baseline_ref(req, baseline)

            cr = ChangeRecord(
                change_type=change_type,
                description=req.description[:300],
                original_ref=original_ref,
                followup_ref=followup_ref,
                scope_impact=_scope_impact(change_type, req.description),
                estimate_impact=_EFFORT_DELTA_TABLE[change_type],
            )
            changes.append(cr)

            rev = _build_revised_estimate(cr)
            if rev:
                revised.append(rev)

        summary = _summarise(changes)

        return ChangeAnalysis(
            baseline_proposal_id=baseline.proposal_id,
            baseline_version=baseline.version,
            followup_transcript_id=followup_reqs.transcript_id,
            analyzed_at=datetime.utcnow(),
            changes=changes,
            scope_delta_summary=summary,
            revised_estimates=revised,
            status=ProposalStatus.DRAFT,
        )


def _check_if_new(req: ExtractedRequirement, baseline: ProposalDocument) -> Optional[ChangeType]:
    """Check if the requirement is genuinely new relative to the baseline scope."""
    baseline_text = " ".join(
        d.description.lower() for d in baseline.scope.deliverables
    ) + " ".join(o.lower() for o in baseline.scope.objectives)

    req_words = set(req.description.lower().split())
    # Rough novelty check: if fewer than 20% of words overlap with baseline
    overlap = sum(1 for w in req_words if w in baseline_text and len(w) > 4)
    novelty = 1 - (overlap / max(len(req_words), 1))
    if novelty > 0.8 and len(req.description.split()) >= 5:
        return ChangeType.ADDITION
    return None


def _find_baseline_ref(
    req: ExtractedRequirement,
    baseline: ProposalDocument,
) -> Optional[TranscriptSegmentRef]:
    """Attempt to find a baseline source ref that overlaps with the requirement."""
    # We don't have original segment refs in the proposal directly, return None
    return None


def _scope_impact(change_type: ChangeType, description: str) -> str:
    impacts = {
        ChangeType.ADDITION: f"Increases scope: {description[:80]}",
        ChangeType.MODIFICATION: f"Modifies existing deliverable: {description[:80]}",
        ChangeType.REMOVAL: f"Reduces scope: {description[:80]}",
        ChangeType.OUT_OF_SCOPE: f"Explicitly excluded: {description[:80]}",
    }
    return impacts[change_type]


def _summarise(changes: List[ChangeRecord]) -> str:
    counts: Dict[ChangeType, int] = {}
    for c in changes:
        counts[c.change_type] = counts.get(c.change_type, 0) + 1
    parts = [f"{v} {k.value}(s)" for k, v in counts.items()]
    if not parts:
        return "No changes detected."
    return "Scope delta: " + ", ".join(parts) + "."

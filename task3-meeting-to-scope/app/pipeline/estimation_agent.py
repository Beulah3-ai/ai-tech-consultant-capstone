"""Estimation Agent: produces task-level hour estimates from a ScopeDocument.

All estimates are deterministic (not AI-generated).  Every estimate is labelled
as an assumption-based approximation.  Never presented as verified.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.schemas import EstimationItem, ScopeDocument

# ---------------------------------------------------------------------------
# Effort lookup table  (keyword → (low, likely, high) hours)
# Each deliverable description is matched against the first matching keyword.
# ---------------------------------------------------------------------------
_EFFORT_TABLE: List[Tuple[List[str], float, float, float, str]] = [
    # (keywords, low, likely, high, assumption)
    (
        ["voice search", "web speech api", "microphone"],
        4, 8, 14,
        "Browser Web Speech API; compatibility limited to Chrome/Edge/Safari.",
    ),
    (
        ["stripe checkout", "stripe integration", "stripe", "payment"],
        8, 16, 28,
        "Stripe hosted fields used; SAQ A scope preserved. Includes test mode validation.",
    ),
    (
        ["filter", "facet", "multi-select", "filter pill", "filter chip"],
        6, 12, 20,
        "Client-side filtering for <10 k records; server-side needed for larger sets.",
    ),
    (
        ["full-text search", "relevance search", "keyword search", "search"],
        8, 14, 22,
        "FTS5 or equivalent built-in search; typo tolerance via trigram index.",
    ),
    (
        ["mobile-first redesign", "bottom navigation", "mobile redesign"],
        16, 28, 48,
        "Full theme redesign; WCAG 2.1 AA compliance required.",
    ),
    (
        ["responsive", "wcag", "accessibility", "mobile optimisation"],
        4, 8, 14,
        "Responsive optimisation within existing theme framework.",
    ),
    (
        ["checkout", "cart", "single page checkout", "two step checkout"],
        8, 16, 26,
        "Depends on existing checkout framework complexity.",
    ),
    (
        ["order notification", "transactional email", "email notification", "email alert"],
        4, 8, 14,
        "Requires transactional email provider (e.g., SendGrid, Mailgun).",
    ),
    (
        ["order management", "fulfillment dashboard", "dashboard", "order dashboard"],
        8, 14, 22,
        "Tablet-friendly UI; real-time updates via polling or WebSocket.",
    ),
    (
        ["refund", "partial refund", "chargeback"],
        4, 8, 14,
        "Stripe refund API; staff-only permission required.",
    ),
    (
        ["csv export", "reconciliation", "bookkeeping"],
        2, 4, 8,
        "Simple CSV generation; format to match existing spreadsheet schema.",
    ),
    (
        ["saml", "sso", "single sign-on", "okta", "azure ad"],
        12, 20, 32,
        "SAML SP implementation; IdP metadata exchange required; test with provider sandbox.",
    ),
    (
        ["salesforce", "crm sync", "webhook sync", "bidirectional"],
        8, 16, 24,
        "Webhook handler + Salesforce Connected App credentials required.",
    ),
    (
        ["bulk import", "csv import", "data migration", "mysql migration"],
        8, 16, 28,
        "Data cleaning and field mapping needed before import.",
    ),
    (
        ["saved search", "email alert", "search alert"],
        4, 8, 14,
        "Requires background job scheduler; out of MVP scope unless specified.",
    ),
    (
        ["multi-currency", "eur", "gbp", "usd"],
        4, 8, 14,
        "Currency conversion rates via third-party API; rounding rules needed.",
    ),
    (
        ["custom domain", "ssl", "domain mapping"],
        2, 4, 8,
        "DNS propagation outside consultant control; allow extra days.",
    ),
]

_DEFAULT_EFFORT = (2, 6, 12)
_DEFAULT_ASSUMPTION = "No specific effort table entry; estimate based on general complexity."


def _match_effort(description: str) -> Tuple[float, float, float, str]:
    lower = description.lower()
    for keywords, low, likely, high, assumption in _EFFORT_TABLE:
        if any(kw in lower for kw in keywords):
            return low, likely, high, assumption
    return (*_DEFAULT_EFFORT, _DEFAULT_ASSUMPTION)


class EstimationAgent:
    """Produces EstimationItem list from a ScopeDocument.

    All estimates are deterministic table lookups.  They are explicitly
    labelled as estimated/approximate and must be reviewed before quoting.
    """

    def estimate(self, scope: ScopeDocument) -> List[EstimationItem]:
        items: List[EstimationItem] = []
        seen: Dict[str, bool] = {}

        for deliverable in scope.deliverables:
            desc = deliverable.description
            if desc in seen:
                continue
            seen[desc] = True

            low, likely, high, assumption = _match_effort(desc)

            items.append(
                EstimationItem(
                    task=desc[:120],  # truncate for readability
                    low_hours=low,
                    likely_hours=likely,
                    high_hours=high,
                    assumptions=[
                        assumption,
                        "ESTIMATED — not verified; subject to revision after technical discovery.",
                    ],
                    source_deliverable=desc,
                )
            )

        # Fallback: if no deliverables, estimate in-scope items
        if not items:
            for scope_item in scope.in_scope:
                desc = scope_item.description
                if desc in seen:
                    continue
                seen[desc] = True
                low, likely, high, assumption = _match_effort(desc)
                items.append(
                    EstimationItem(
                        task=desc[:120],
                        low_hours=low,
                        likely_hours=likely,
                        high_hours=high,
                        assumptions=[
                            assumption,
                            "ESTIMATED — not verified.",
                        ],
                        source_deliverable=desc,
                    )
                )

        return items

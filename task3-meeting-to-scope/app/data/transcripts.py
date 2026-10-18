"""Synthetic meeting transcripts for Task 3: Meeting to Scope.

All transcripts are synthetic test artifacts created for capstone evaluation purposes.
No real customer information, proprietary data, or trade secrets are used.

Transcripts:
  TRANSCRIPT-A : Website improvements — search, filters, mobile UI (discovery meeting)
  TRANSCRIPT-B : E-commerce — checkout flow, order notifications, Stripe payments
  TRANSCRIPT-C : Follow-up to A — adds voice search, modifies filter UX, removes
                  full mobile-first redesign
"""

from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# TRANSCRIPT A — Website Improvements Discovery
# ---------------------------------------------------------------------------
TRANSCRIPT_A_WEBSITE: Dict[str, Any] = {
    "transcript_id": "TRANSCRIPT-A",
    "title": "LocalBiz Directory — Website Search, Filters & Mobile Improvements",
    "client_name": "LocalBiz Connections (Synthetic)",
    "date": "2026-10-06",
    "attendees": [
        "Rachel Torres (Client Product Manager)",
        "Kevin Singh (Client Operations Director)",
        "Sam Okafor (Consultant Lead Architect)",
        "Priya Mehta (Consultant Business Analyst)",
    ],
    "segments": [
        {
            "segment_id": "SEG-A-01",
            "line_number": 1,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:01:00",
            "text": (
                "Good afternoon Rachel and Kevin. Today we are scoping improvements "
                "to your Brilliant Directories site. Let's start with your primary "
                "goals — what is working poorly right now?"
            ),
        },
        {
            "segment_id": "SEG-A-02",
            "line_number": 2,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:01:30",
            "text": (
                "Our biggest pain point is search. Members complain that the keyword "
                "search returns too many irrelevant results. We need relevance-ranked "
                "full-text search across member name, business category, and location. "
                "Typo tolerance would also be a significant improvement."
            ),
        },
        {
            "segment_id": "SEG-A-03",
            "line_number": 3,
            "speaker": "Kevin Singh (Client Operations Director)",
            "timestamp": "00:02:20",
            "text": (
                "Filtering is equally critical. Right now visitors can only filter by "
                "category. We need multi-select faceted filters covering category, "
                "geographic radius, membership tier, ratings range, and whether the "
                "member accepts online bookings."
            ),
        },
        {
            "segment_id": "SEG-A-04",
            "line_number": 4,
            "speaker": "Priya Mehta (Consultant Business Analyst)",
            "timestamp": "00:03:10",
            "text": (
                "Understood. These filters will appear as a sidebar on the search "
                "results page? Or as a collapsible drawer on mobile?"
            ),
        },
        {
            "segment_id": "SEG-A-05",
            "line_number": 5,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:03:40",
            "text": (
                "Sidebar on desktop. On mobile we want a completely rethought "
                "mobile-first redesign — simplified navigation, thumb-friendly filter "
                "controls, and a bottom navigation bar replacing the current top menu."
            ),
        },
        {
            "segment_id": "SEG-A-06",
            "line_number": 6,
            "speaker": "Kevin Singh (Client Operations Director)",
            "timestamp": "00:04:20",
            "text": (
                "The mobile experience is causing us real business loss. Our analytics "
                "show 68 percent of visitors are on mobile but our mobile conversion "
                "rate is only 12 percent versus 34 percent on desktop. "
                "We cannot afford to wait on this."
            ),
        },
        {
            "segment_id": "SEG-A-07",
            "line_number": 7,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:05:00",
            "text": (
                "That is a significant gap. What is the timeline constraint and "
                "budget range you are working with?"
            ),
        },
        {
            "segment_id": "SEG-A-08",
            "line_number": 8,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:05:30",
            "text": (
                "We need the search and filter improvements live within 6 weeks. "
                "Budget is approximately $18,000 for this phase. The mobile redesign "
                "must be part of this phase — it is not optional."
            ),
        },
        {
            "segment_id": "SEG-A-09",
            "line_number": 9,
            "speaker": "Kevin Singh (Client Operations Director)",
            "timestamp": "00:06:10",
            "text": (
                "One open question from our side: can the directory support saved "
                "searches and email alerts when new members matching the criteria "
                "are added? We have not budgeted for it but we want to know "
                "if it is feasible."
            ),
        },
        {
            "segment_id": "SEG-A-10",
            "line_number": 10,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:06:55",
            "text": (
                "Saved searches and email alerts are feasible but would add scope. "
                "I will note it as an open question and we can price it separately "
                "in the proposal. Any constraints we should know about — "
                "hosting environment, third-party integrations, accessibility standards?"
            ),
        },
        {
            "segment_id": "SEG-A-11",
            "line_number": 11,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:07:40",
            "text": (
                "We are on shared hosting with our Brilliant Directories provider. "
                "No custom server access. All customizations must use the available "
                "plugin and widget framework. WCAG 2.1 AA accessibility compliance "
                "is required for the redesigned mobile interface."
            ),
        },
        {
            "segment_id": "SEG-A-12",
            "line_number": 12,
            "speaker": "Priya Mehta (Consultant Business Analyst)",
            "timestamp": "00:08:25",
            "text": (
                "Understood. We will document the WCAG 2.1 AA requirement as "
                "a non-functional requirement and include it in acceptance criteria."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# TRANSCRIPT B — E-commerce Checkout, Order Notifications, Payment Integration
# ---------------------------------------------------------------------------
TRANSCRIPT_B_ECOMMERCE: Dict[str, Any] = {
    "transcript_id": "TRANSCRIPT-B",
    "title": "CraftMarket Pro — E-commerce Checkout, Order Notifications & Stripe Integration",
    "client_name": "CraftMarket Pro (Synthetic)",
    "date": "2026-10-08",
    "attendees": [
        "Diana Walsh (Client CEO)",
        "Tom Reyes (Client Head of E-commerce)",
        "Sam Okafor (Consultant Lead Architect)",
        "Priya Mehta (Consultant Business Analyst)",
    ],
    "segments": [
        {
            "segment_id": "SEG-B-01",
            "line_number": 1,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:01:00",
            "text": (
                "Hello Diana and Tom. We are here to scope your e-commerce checkout "
                "improvements and payment integration. Please walk us through the "
                "current customer journey and the key pain points."
            ),
        },
        {
            "segment_id": "SEG-B-02",
            "line_number": 2,
            "speaker": "Diana Walsh (Client CEO)",
            "timestamp": "00:01:40",
            "text": (
                "Our biggest problem is cart abandonment during checkout. We have "
                "a seven-step checkout flow that customers drop at step four — "
                "the payment entry screen. We need to simplify checkout to a single "
                "page or a maximum of two steps, with a clear order summary visible "
                "at all times."
            ),
        },
        {
            "segment_id": "SEG-B-03",
            "line_number": 3,
            "speaker": "Tom Reyes (Client Head of E-commerce)",
            "timestamp": "00:02:30",
            "text": (
                "Payment is the core issue. We are currently using an older payment "
                "gateway that does not support digital wallets. We want full Stripe "
                "Checkout integration supporting credit cards, Apple Pay, Google Pay, "
                "and Stripe's built-in saved payment methods."
            ),
        },
        {
            "segment_id": "SEG-B-04",
            "line_number": 4,
            "speaker": "Priya Mehta (Consultant Business Analyst)",
            "timestamp": "00:03:15",
            "text": (
                "For order confirmation: what communications do customers currently "
                "receive after completing a purchase?"
            ),
        },
        {
            "segment_id": "SEG-B-05",
            "line_number": 5,
            "speaker": "Diana Walsh (Client CEO)",
            "timestamp": "00:03:50",
            "text": (
                "Currently nothing automated. We manually email order confirmations "
                "once a day in batches. We need automated transactional email "
                "notifications: order placed, payment confirmed, order shipped with "
                "tracking number, and delivery confirmed. All within minutes of the "
                "triggering event."
            ),
        },
        {
            "segment_id": "SEG-B-06",
            "line_number": 6,
            "speaker": "Tom Reyes (Client Head of E-commerce)",
            "timestamp": "00:04:40",
            "text": (
                "We also want an order management dashboard for our fulfillment team: "
                "view open orders, mark as shipped, enter tracking numbers, and "
                "trigger the shipping notification email. The interface needs to be "
                "usable on a tablet on the warehouse floor."
            ),
        },
        {
            "segment_id": "SEG-B-07",
            "line_number": 7,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:05:30",
            "text": (
                "Understood. What is the expected order volume? And do you require "
                "refund or chargeback handling through Stripe?"
            ),
        },
        {
            "segment_id": "SEG-B-08",
            "line_number": 8,
            "speaker": "Tom Reyes (Client Head of E-commerce)",
            "timestamp": "00:06:00",
            "text": (
                "We process approximately 200 orders per day currently, targeting "
                "500 per day within 12 months. Yes, we need Stripe refund initiation "
                "from the dashboard — full and partial refunds — and automatic "
                "reconciliation with our bookkeeping spreadsheet via CSV export."
            ),
        },
        {
            "segment_id": "SEG-B-09",
            "line_number": 9,
            "speaker": "Diana Walsh (Client CEO)",
            "timestamp": "00:06:45",
            "text": (
                "Budget is $28,000 with a delivery timeline of 10 weeks. An open "
                "question: can we add a loyalty points programme in the same phase, "
                "or does that need to be a separate project?"
            ),
        },
        {
            "segment_id": "SEG-B-10",
            "line_number": 10,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:07:20",
            "text": (
                "A full loyalty points programme would be out of scope for this "
                "phase given the timeline and budget. I will document it as an "
                "out-of-scope item and a candidate for a future phase."
            ),
        },
        {
            "segment_id": "SEG-B-11",
            "line_number": 11,
            "speaker": "Priya Mehta (Consultant Business Analyst)",
            "timestamp": "00:07:55",
            "text": (
                "Are there any compliance or data residency constraints for the "
                "payment and order data? PCI DSS, GDPR, or similar?"
            ),
        },
        {
            "segment_id": "SEG-B-12",
            "line_number": 12,
            "speaker": "Diana Walsh (Client CEO)",
            "timestamp": "00:08:25",
            "text": (
                "We are a UK-based business so GDPR applies to customer personal data. "
                "For PCI DSS, Stripe handles card data directly so we are SAQ A "
                "compliant as long as we use Stripe-hosted payment fields — "
                "no raw card numbers touch our servers. The consultant must confirm "
                "the integration preserves that SAQ A scope."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# TRANSCRIPT C — Follow-up to Transcript A (adds voice search, modifies
#                filter UX, removes full mobile-first redesign)
# ---------------------------------------------------------------------------
TRANSCRIPT_C_FOLLOWUP: Dict[str, Any] = {
    "transcript_id": "TRANSCRIPT-C",
    "title": "LocalBiz Directory — Follow-up Scope Revision",
    "client_name": "LocalBiz Connections (Synthetic)",
    "date": "2026-10-13",
    "attendees": [
        "Rachel Torres (Client Product Manager)",
        "Kevin Singh (Client Operations Director)",
        "Sam Okafor (Consultant Lead Architect)",
    ],
    "segments": [
        {
            "segment_id": "SEG-C-01",
            "line_number": 1,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:01:00",
            "text": (
                "Good morning Rachel and Kevin. We are reviewing the baseline scope "
                "we agreed in the discovery session last week and incorporating the "
                "change requests your team submitted. Let us go through each one."
            ),
        },
        {
            "segment_id": "SEG-C-02",
            "line_number": 2,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:01:40",
            "text": (
                "First, a scope ADDITION. We want to add voice search support. "
                "Members should be able to tap a microphone icon on the search bar "
                "and speak their query. The platform should transcribe it using "
                "the browser Web Speech API and populate the search field. "
                "No third-party cloud transcription service — browser-native only."
            ),
        },
        {
            "segment_id": "SEG-C-03",
            "line_number": 3,
            "speaker": "Kevin Singh (Client Operations Director)",
            "timestamp": "00:02:30",
            "text": (
                "Second, a scope MODIFICATION to the filter UX. In the original "
                "scope we agreed to a sidebar filter panel on desktop. We now want "
                "a floating filter pill row — displayed horizontally above the "
                "results — that collapses applied filters into chips. This replaces "
                "the sidebar design entirely."
            ),
        },
        {
            "segment_id": "SEG-C-04",
            "line_number": 4,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:03:15",
            "text": (
                "Understood. The sidebar filter panel is replaced with horizontal "
                "filter chips. I am noting this as a MODIFICATION to the original "
                "filter UX requirement. The multi-select facets and filter categories "
                "themselves remain the same?"
            ),
        },
        {
            "segment_id": "SEG-C-05",
            "line_number": 5,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:03:45",
            "text": (
                "Yes, all filter categories are unchanged — only the visual "
                "presentation changes."
            ),
        },
        {
            "segment_id": "SEG-C-06",
            "line_number": 6,
            "speaker": "Kevin Singh (Client Operations Director)",
            "timestamp": "00:04:15",
            "text": (
                "Third, a scope REMOVAL. We are dropping the full mobile-first "
                "redesign with the bottom navigation bar. After reviewing our "
                "analytics more carefully with the UX team, we believe a "
                "responsive-only approach using the existing template framework "
                "is sufficient and will deliver 80 percent of the mobile conversion "
                "gain at roughly a third of the cost."
            ),
        },
        {
            "segment_id": "SEG-C-07",
            "line_number": 7,
            "speaker": "Sam Okafor (Consultant Lead Architect)",
            "timestamp": "00:05:00",
            "text": (
                "Confirmed. The full mobile-first redesign and bottom navigation bar "
                "are REMOVED from scope. We will deliver responsive optimisation "
                "within the existing theme instead. This reduces the budget "
                "requirement significantly. What is the revised budget?"
            ),
        },
        {
            "segment_id": "SEG-C-08",
            "line_number": 8,
            "speaker": "Rachel Torres (Client Product Manager)",
            "timestamp": "00:05:40",
            "text": (
                "Revised budget is $14,000 — down from $18,000 — reflecting the "
                "removal of the redesign and the addition of the browser-native "
                "voice search feature. Timeline remains 6 weeks."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------
_ALL_TRANSCRIPTS: List[Dict[str, Any]] = [
    TRANSCRIPT_A_WEBSITE,
    TRANSCRIPT_B_ECOMMERCE,
    TRANSCRIPT_C_FOLLOWUP,
]

# Defines which transcript is the follow-up baseline pair for change analysis
CHANGE_ANALYSIS_PAIRS = [
    {"baseline_id": "TRANSCRIPT-A", "followup_id": "TRANSCRIPT-C"},
]


def get_all_transcripts() -> List[Dict[str, Any]]:
    """Return all available synthetic meeting transcripts."""
    return list(_ALL_TRANSCRIPTS)


def get_transcript_by_id(transcript_id: str) -> Dict[str, Any]:
    """Lookup transcript by unique identifier. Raises ValueError if not found."""
    for t in _ALL_TRANSCRIPTS:
        if t["transcript_id"] == transcript_id:
            return t
    raise ValueError(f"Transcript '{transcript_id}' not found.")

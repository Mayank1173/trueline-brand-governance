"""Test fixtures for Trueline AI Review Engine."""

from trueline.models import ApprovedFact, Guideline, ReviewRequest

SAMPLE_GUIDELINES = [
    Guideline(
        id="RULE_001",
        title="Avoid guaranteed outcomes",
        text='Do not use "guaranteed" or "guarantee" in marketing claims.',
        category="unsupported_claim",
        source="Northstar Brand Guidelines",
    ),
    Guideline(
        id="RULE_002",
        title="Required disclaimer",
        text='Must include "Results may vary" disclaimer.',
        category="missing_disclaimer",
        source="Northstar Brand Guidelines",
    ),
    Guideline(
        id="RULE_003",
        title="Banned term: revolutionary",
        text='Avoid "revolutionary" - use "innovative" instead.',
        category="banned_term",
        source="Northstar Brand Guidelines",
    ),
    Guideline(
        id="RULE_004",
        title="Preferred terminology",
        text='Use "client" not "customer".',
        category="preferred_terminology",
        source="Northstar Brand Guidelines",
    ),
    Guideline(
        id="RULE_005",
        title="Tone guideline",
        text="Maintain professional, confident tone. Avoid hyperbolic language.",
        category="tone",
        source="Northstar Brand Guidelines",
    ),
]


SAMPLE_APPROVED_FACTS = [
    ApprovedFact(
        id="FACT_001",
        claim="Northstar processes 10M transactions daily",
        evidence="Internal metrics dashboard Q3 2024",
        category="performance",
    ),
    ApprovedFact(
        id="FACT_002",
        claim="Northstar uptime is 99.99%",
        evidence="SLA report 2024",
        category="reliability",
    ),
]


def create_review_request(
    draft_text: str,
    brand_id: str = "northstar",
    content_purpose: str = "marketing_email",
    guidelines: list[Guideline] = None,
    approved_facts: list[ApprovedFact] = None,
) -> ReviewRequest:
    """Create a ReviewRequest with sample data."""
    return ReviewRequest(
        draft_text=draft_text,
        brand_id=brand_id,
        content_purpose=content_purpose,
        guidelines=guidelines or SAMPLE_GUIDELINES,
        approved_facts=approved_facts or SAMPLE_APPROVED_FACTS,
    )


# Test drafts
CLEAN_DRAFT = (
    "Our innovative platform helps clients achieve their goals. "
    "Results may vary based on individual usage."
)

DIRTY_DRAFT = (
    "Our revolutionary platform guarantees success for every customer. "
    "You are guaranteed to see results!"
)

MIXED_DRAFT = (
    "Our innovative platform helps clients achieve their goals. "
    "Results may vary based on individual usage. "
    "This revolutionary approach guarantees success."
)

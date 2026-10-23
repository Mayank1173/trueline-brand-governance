"""ILLUSTRATIVE DEMONSTRATION DATA.

None of these rules, sources, or facts are official Trueline brand policy.
They exist so the hackathon demo and tests have clearly labelled sample data.
Real brand configuration must replace this data before any production use.
"""

from __future__ import annotations

from datetime import date

DEMO_NOTICE = "ILLUSTRATIVE DEMO DATA - NOT OFFICIAL TRUELINE BRAND POLICY"
DEMO_RULESET_VERSION = "demo-ruleset-2026.10"

DEMO_BRANDS = [
    {
        "id": "brand_001",
        "name": "Sample Brand (illustrative demo)",
        "description": "Fictional brand used by the existing frontend mock.",
    },
    {
        "id": "brand-demo",
        "name": "Trueline Demo Brand (illustrative)",
        "description": "Fictional brand used in backend request examples.",
    },
]


def demo_guidelines(brand_id: str, prefix: str) -> list[dict]:
    title = f"Trueline Demo Brand Guidelines ({DEMO_NOTICE})"

    def source_id(rule_id: str) -> str:
        return f"GL-{prefix}-{rule_id.removeprefix('BR-')}"

    def guideline(
        *,
        rule_id: str,
        section: str,
        content: str,
        category: str,
        severity: str,
        match_type: str,
        explanation: str,
        config: dict,
        suggested_fix: str | None = None,
        confidence: float = 1.0,
        requires_human_review: bool = False,
    ) -> dict:
        return {
            "id": source_id(rule_id),
            "brand_id": brand_id,
            "rule_id": rule_id,
            "title": title,
            "section": section,
            "version": DEMO_RULESET_VERSION,
            "content": content,
            "category": category,
            "severity": severity,
            "match_type": match_type,
            "config_json": config,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
            "confidence": confidence,
            "requires_human_review": requires_human_review,
            "is_active": True,
        }

    return [
        guideline(
            rule_id="BR-CLAIM-001",
            section="4.2",
            content=(
                "Do not promise guaranteed outcomes unless an approved, current "
                "fact supports it."
            ),
            category="unsupported_claim",
            severity="high",
            match_type="term",
            explanation=(
                "This wording makes an absolute guarantee. The deterministic "
                "check found the claim language; a human must confirm whether an "
                "approved, current fact supports it."
            ),
            config={"patterns": ["guaranteed"], "word_boundary": True},
            suggested_fix="designed to help",
            requires_human_review=True,
        ),
        guideline(
            rule_id="BR-TERM-014",
            section="2.3",
            content=("Avoid 'cheapest' and other unverifiable price superlatives."),
            category="banned_term",
            severity="medium",
            match_type="term",
            explanation=(
                "The draft uses a banned price superlative that is not supported "
                "by the illustrative brand guidelines."
            ),
            config={"patterns": ["cheapest"], "word_boundary": True},
            suggested_fix="great value",
        ),
        guideline(
            rule_id="BR-VOICE-003",
            section="1.1",
            content=(
                "Voice is confident and factual. Avoid exaggerated hype words "
                "such as 'revolutionary'."
            ),
            category="tone",
            severity="low",
            match_type="term",
            explanation=(
                "The draft uses a hype word that conflicts with the illustrative "
                "brand voice guidance. Context still needs a human judgment."
            ),
            config={"patterns": ["revolutionary"], "word_boundary": True},
            suggested_fix="innovative",
            requires_human_review=True,
        ),
        guideline(
            rule_id="BR-FMT-002",
            section="3.4",
            content="Use at most one exclamation mark per post.",
            category="formatting",
            severity="low",
            match_type="regex",
            explanation=(
                "Multiple exclamation marks are not allowed in the illustrative "
                "brand formatting guidance."
            ),
            config={"patterns": ["!{2,}"]},
            suggested_fix="!",
        ),
        guideline(
            rule_id="BR-TERM-020",
            section="2.1",
            content="Use 'customers' instead of 'users' in customer-facing copy.",
            category="preferred_terminology",
            severity="medium",
            match_type="term",
            explanation=(
                "The draft uses a term that the illustrative guidance replaces "
                "with preferred wording."
            ),
            config={"patterns": ["users"], "word_boundary": True},
            suggested_fix="customers",
        ),
        guideline(
            rule_id="BR-PRODUCT-001",
            section="2.4",
            content="Write the product name as 'Trueline' (one word, capital T).",
            category="product_name",
            severity="medium",
            match_type="term",
            explanation=(
                "The draft uses a non-standard spelling of the product name. "
                "The approved spelling is 'Trueline'."
            ),
            config={
                "patterns": ["TrueLine", "True Line", "True-Line"],
                "case_sensitive": True,
                "word_boundary": True,
            },
            suggested_fix="Trueline",
        ),
        guideline(
            rule_id="BR-LEGAL-002",
            section="6.1",
            content="All promotional content must include 'Terms apply.'",
            category="required_phrase",
            severity="medium",
            match_type="required_phrase",
            explanation=("Promotional copy must include the required disclaimer."),
            config={
                "patterns": ["Terms apply."],
                "word_boundary": False,
                "applies_to_purposes": [],
            },
            suggested_fix="Terms apply.",
        ),
        guideline(
            rule_id="BR-LIMIT-001",
            section="7.1",
            content="Promotional copy must not exceed 1,200 characters.",
            category="length_limit",
            severity="medium",
            match_type="length_limit",
            explanation=(
                "The draft exceeds the illustrative length limit for promotional copy."
            ),
            config={"max_chars": 1200},
            suggested_fix=None,
        ),
        guideline(
            rule_id="BR-CLAIM-002",
            section="4.3",
            content=(
                "Avoid 'world-class' and other unverifiable superlatives unless "
                "a current approved fact supports them."
            ),
            category="unsupported_claim",
            severity="medium",
            match_type="term",
            explanation=(
                "The draft uses an unverifiable superlative. No approved fact is "
                "attached automatically; a human must verify or remove the claim."
            ),
            config={"patterns": ["world-class"], "word_boundary": True},
            suggested_fix=None,
            requires_human_review=True,
        ),
    ]


def demo_facts(brand_id: str, prefix: str) -> list[dict]:
    source = f"Illustrative Demo Fact Library ({DEMO_NOTICE})"
    return [
        {
            "id": f"FACT-{prefix}-001",
            "brand_id": brand_id,
            "statement": "Free shipping on orders over $50.",
            "source_label": source,
            "source_version": DEMO_RULESET_VERSION,
            "valid_from": date(2000, 1, 1),
            "valid_until": None,
            "is_active": True,
        },
        {
            "id": f"FACT-{prefix}-002",
            "brand_id": brand_id,
            "statement": "Battery lasts up to 10 hours.",
            "source_label": source,
            "source_version": DEMO_RULESET_VERSION,
            "valid_from": date(2000, 1, 1),
            "valid_until": None,
            "is_active": True,
        },
        {
            "id": f"FACT-{prefix}-003",
            "brand_id": brand_id,
            "statement": "Free returns within 30 days.",
            "source_label": source,
            "source_version": DEMO_RULESET_VERSION,
            "valid_from": date(2000, 1, 1),
            "valid_until": date(2020, 1, 1),
            "is_active": True,
        },
    ]


def demo_seed_payload() -> tuple[list[dict], list[dict], list[dict]]:
    brands = list(DEMO_BRANDS)
    guidelines: list[dict] = []
    facts: list[dict] = []

    for brand, prefix in (("brand_001", "B1"), ("brand-demo", "BD")):
        guidelines.extend(demo_guidelines(brand, prefix))
        facts.extend(demo_facts(brand, prefix))

    return brands, guidelines, facts

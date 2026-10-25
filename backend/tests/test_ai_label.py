from __future__ import annotations

from datetime import date

import pytest

from app.ai_labels import AILabel
from app.models import Review, ReviewFinding
from app.schemas import FindingResponse


def make_finding(ai_label: str | AILabel | None) -> ReviewFinding:
    return ReviewFinding(
        id="finding-ai-label",
        review_id="review-ai-label",
        rule_id="BR-TEST-001",
        matched_text="bad",
        start_offset=0,
        end_offset=3,
        category="banned_term",
        severity="medium",
        explanation="Test finding.",
        confidence=1.0,
        requires_human_review=False,
        ai_label=ai_label,
    )


@pytest.mark.parametrize("label", list(AILabel))
def test_valid_ai_labels_are_persisted_as_their_wire_value(label: AILabel):
    assert make_finding(label).ai_label == label.value


def test_missing_ai_label_remains_null():
    assert make_finding(None).ai_label is None


def test_unknown_ai_label_is_rejected_before_persistence():
    with pytest.raises(ValueError, match="Unsupported ai_label"):
        make_finding("BOGUS")


def test_ai_label_is_exposed_by_the_review_detail_endpoint(client):
    review_id = "review_ai_label_roundtrip"
    with client.app.state.db.session_factory() as session:
        session.add(
            Review(
                id=review_id,
                brand_id="brand_001",
                draft_text="A draft.",
                purpose="marketing",
                status="needs_human_review",
                ruleset_version="test",
                engine_version="test",
                evaluation_date=date(2026, 10, 24),
            )
        )
        session.add(
            ReviewFinding(
                id=f"{review_id}-F-0001",
                review_id=review_id,
                rule_id="BR-TEST-001",
                matched_text="draft",
                start_offset=2,
                end_offset=7,
                category="banned_term",
                severity="medium",
                explanation="Persisted test finding.",
                confidence=1.0,
                requires_human_review=True,
                ai_label="CONTRADICTED",
            )
        )
        session.commit()

    response = client.get(f"/api/reviews/{review_id}")
    assert response.status_code == 200
    finding = response.json()["findings"][0]
    assert finding["ai_label"] == "CONTRADICTED"


def test_response_schema_rejects_unknown_ai_label():
    with pytest.raises(ValueError):
        FindingResponse(
            id="finding-1",
            finding_id="finding-1",
            rule_id="BR-TEST-001",
            matched_text="bad",
            category="banned_term",
            severity="medium",
            explanation="Test.",
            confidence=1.0,
            requires_human_review=False,
            ai_label="BOGUS",
        )

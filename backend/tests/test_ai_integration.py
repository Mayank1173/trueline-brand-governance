from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from app.ai_review import (
    AI_STATUS_DEGRADED,
    AI_STATUS_DISABLED,
    AI_STATUS_NOT_CONFIGURED,
    AI_STATUS_SKIPPED,
    AI_STATUS_SUCCESS,
    AI_STATUS_TIMEOUT,
    build_ai_inputs,
    run_ai_review,
)
from app.api.deps import get_review_service
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.models import ApprovedFact, Guideline
from app.repositories import fact_is_current
from app.schemas import ReviewRequest
from app.seed import seed_demo_data
from app.services import ReviewService
from fastapi.testclient import TestClient
from trueline.config import settings as ai_settings
from trueline.models import Category, Citation, Finding, Severity
from trueline.providers.base import AIProviderError


class FakeProvider:
    def __init__(self, findings=None, error: Exception | None = None) -> None:
        self.findings = findings or []
        self.error = error
        self.calls: list[dict] = []

    async def analyze(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.findings


@pytest.fixture
def database(tmp_path):
    settings = Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite:///{(tmp_path / 'ai.db').as_posix()}",
        auto_create_tables=True,
        seed_demo_data=False,
        max_purpose_chars=200,
    )
    db = Database(settings.database_url)
    db.create_all()
    with db.session_factory() as session:
        seed_demo_data(session)
    yield settings, db
    db.dispose()


def _service(settings, provider=None, *, ai_enabled=False):
    return ReviewService(
        settings.model_copy(update={"ai_enabled": ai_enabled}),
        ai_provider=provider,
    )


def _api_settings(tmp_path, *, ai_enabled=False):
    return Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite:///{(tmp_path / 'api.db').as_posix()}",
        auto_create_tables=True,
        seed_demo_data=True,
        max_purpose_chars=200,
        ai_enabled=ai_enabled,
    )


def _mark_guideline(session, source_id: str, method: str) -> Guideline:
    guideline = session.get(Guideline, source_id)
    assert guideline is not None
    guideline.config_json = {**(guideline.config_json or {}), "check_method": method}
    session.commit()
    return guideline


def _finding(
    *,
    rule_id: str,
    matched_text: str,
    start: int,
    category: Category = Category.TONE,
    severity: Severity = Severity.LOW,
    requires_human_review: bool = True,
) -> Finding:
    return Finding(
        id=f"ai-{rule_id}",
        matched_text=matched_text,
        start=start,
        end=start + len(matched_text),
        category=category,
        severity=severity,
        explanation="AI finding.",
        citation=Citation(
            rule_id=rule_id,
            source="Approved source",
            excerpt="Approved source text.",
        ),
        suggested_fix=None,
        confidence=0.9,
        requires_human_review=requires_human_review,
    )


def test_computed_rules_never_call_ai(database):
    settings, db = database
    provider = FakeProvider(error=AssertionError("provider must not be called"))
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Cheapest. Terms apply.",
                purpose="marketing",
            ),
        )

    assert provider.calls == []
    assert review.ai_status == AI_STATUS_SKIPPED
    assert review.ai_error is None
    assert review.findings


def test_ai_only_guideline_run_persists_grounded_citation(database):
    settings, db = database
    with db.session_factory() as session:
        guideline = _mark_guideline(session, "GL-B1-VOICE-003", "ai")
        content = guideline.content

    provider = FakeProvider(
        findings=[
            Finding(
                id="ai-voice",
                matched_text="revolutionary",
                start=0,
                end=13,
                category=Category.TONE,
                severity=Severity.LOW,
                explanation="Tone issue.",
                citation=Citation(
                    rule_id="BR-VOICE-003",
                    source="Approved source",
                    excerpt=content,
                ),
                suggested_fix="innovative",
                confidence=0.9,
                requires_human_review=True,
            )
        ]
    )
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="revolutionary. Terms apply.",
                purpose="marketing",
            ),
        )

    assert review.ai_status == AI_STATUS_SUCCESS
    assert review.ai_error is None
    assert len(review.findings) == 1
    finding = review.findings[0]
    assert finding.rule_id == "BR-VOICE-003"
    assert finding.citation_source_id == "GL-B1-VOICE-003"
    assert finding.citation_source_version == "demo-ruleset-2026.10"
    assert finding.start_offset == 0
    assert finding.end_offset == 13


def test_ai_success_never_automatically_approves_clean_review(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-VOICE-003", "ai")

    service = _service(settings, FakeProvider(findings=[]), ai_enabled=True)
    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Trueline helps customers. Terms apply.",
                purpose="marketing",
            ),
        )
        assert review.findings == []

    assert review.ai_status == AI_STATUS_SUCCESS
    assert review.status == "pending_approval"


def test_invalid_ai_citation_rejects_the_whole_finding(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-VOICE-003", "ai")

    provider = FakeProvider(
        findings=[
            _finding(
                rule_id="BR-UNKNOWN-999",
                matched_text="revolutionary",
                start=0,
            )
        ]
    )
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="revolutionary. Terms apply.",
                purpose="marketing",
            ),
        )
        assert review.ai_status == AI_STATUS_DEGRADED
        assert "rejected" in (review.ai_error or "")
        assert review.findings == []
        assert review.status == "needs_human_review"


def test_ai_cannot_cite_a_computed_only_guideline(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-VOICE-003", "ai")
        computed = session.get(Guideline, "GL-B1-TERM-014")
        assert computed is not None

    provider = FakeProvider(
        findings=[
            _finding(
                rule_id="BR-TERM-014",
                matched_text="cheapest",
                start=4,
            )
        ]
    )
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Our cheapest plan is guaranteed. Terms apply.",
                purpose="marketing",
            ),
        )
        assert review.ai_status == AI_STATUS_DEGRADED
        term_findings = [finding for finding in review.findings if finding.rule_id == "BR-TERM-014"]
        assert len(term_findings) == 1
        assert "banned price superlative" in term_findings[0].explanation


def test_ai_finding_without_citation_is_rejected(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-VOICE-003", "ai")

    finding = _finding(rule_id="BR-VOICE-003", matched_text="revolutionary", start=0)
    finding.citation = None
    provider = FakeProvider(findings=[finding])
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="revolutionary. Terms apply.",
                purpose="marketing",
            ),
        )
        assert review.ai_status == AI_STATUS_DEGRADED
        assert review.findings == []


def test_ai_can_cite_approved_fact_with_correct_source_row(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-CLAIM-001", "ai")

    provider = FakeProvider(
        findings=[
            Finding(
                id="ai-fact",
                matched_text="Free shipping on orders over $50.",
                start=0,
                end=33,
                category=Category.APPROVED_FACT,
                severity=Severity.MEDIUM,
                explanation="Fact reference.",
                citation=Citation(
                    rule_id="FACT-B1-001",
                    source="Approved fact source",
                    excerpt="Free shipping on orders over $50.",
                ),
                suggested_fix=None,
                confidence=0.8,
                requires_human_review=False,
            )
        ]
    )
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Free shipping on orders over $50. Terms apply.",
                purpose="marketing",
            ),
        )

    assert review.ai_status == AI_STATUS_SUCCESS
    finding = next(item for item in review.findings if item.rule_id == "FACT-B1-001")
    assert finding.citation_source_type == "approved_fact"
    assert finding.citation_source_id == "FACT-B1-001"
    assert finding.citation_source_version == "demo-ruleset-2026.10"


def test_disabled_ai_rule_requires_human_review(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-VOICE-003", "ai")

    provider = FakeProvider(error=AssertionError("provider must not be called"))
    service = _service(settings, provider, ai_enabled=False)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="revolutionary. Terms apply.",
                purpose="marketing",
            ),
        )

    assert provider.calls == []
    assert review.ai_status == AI_STATUS_DISABLED
    assert review.status == "needs_human_review"


def test_ai_timeout_is_reported_and_deterministic_results_survive(database):
    settings, db = database
    with db.session_factory() as session:
        _mark_guideline(session, "GL-B1-CLAIM-001", "hybrid")

    provider = FakeProvider(error=AIProviderError("request timed out after 30s", provider="fake"))
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Guaranteed. Terms apply.",
                purpose="marketing",
            ),
        )

    assert review.ai_status == AI_STATUS_TIMEOUT
    error = (review.ai_error or "").lower()
    assert "timeout" in error or "timed out" in error
    assert any(finding.rule_id == "BR-CLAIM-001" for finding in review.findings)
    assert review.status == "needs_human_review"


def test_hybrid_duplicate_keeps_deterministic_finding(database):
    settings, db = database
    with db.session_factory() as session:
        guideline = _mark_guideline(session, "GL-B1-VOICE-003", "hybrid")
        content = guideline.content

    provider = FakeProvider(
        findings=[
            Finding(
                id="ai-duplicate",
                matched_text="revolutionary",
                start=38,
                end=51,
                category=Category.TONE,
                severity=Severity.LOW,
                explanation="AI duplicate.",
                citation=Citation(
                    rule_id="BR-VOICE-003",
                    source="Approved source",
                    excerpt=content,
                ),
                suggested_fix="innovative",
                confidence=0.9,
                requires_human_review=True,
            )
        ]
    )
    service = _service(settings, provider, ai_enabled=True)

    with db.session_factory() as session:
        review = service.submit(
            session,
            ReviewRequest(
                brand_id="brand_001",
                draft_text="Our cheapest plan is guaranteed to be revolutionary!!!",
                purpose="marketing",
            ),
        )

    voice_findings = [finding for finding in review.findings if finding.rule_id == "BR-VOICE-003"]
    assert len(voice_findings) == 1
    assert voice_findings[0].explanation.startswith("The draft uses a hype word")
    assert review.ai_status == AI_STATUS_SUCCESS


def test_api_ai_only_mocked_provider_returns_ai_finding_and_detail(tmp_path):
    settings = _api_settings(tmp_path, ai_enabled=True)
    app = create_app(settings)

    with TestClient(app, raise_server_exceptions=False) as client:
        with app.state.db.session_factory() as session:
            guideline = _mark_guideline(session, "GL-B1-VOICE-003", "ai")
            content = guideline.content

        provider = FakeProvider(
            findings=[
                Finding(
                    id="api-ai-voice",
                    matched_text="revolutionary",
                    start=38,
                    end=51,
                    category=Category.TONE,
                    severity=Severity.LOW,
                    explanation="AI tone finding.",
                    citation=Citation(
                        rule_id="BR-VOICE-003",
                        source="Approved source",
                        excerpt=content,
                    ),
                    suggested_fix="innovative",
                    confidence=0.9,
                    requires_human_review=True,
                )
            ]
        )
        service = ReviewService(settings, ai_provider=provider)
        app.dependency_overrides[get_review_service] = lambda: service

        response = client.post(
            "/api/review",
            json={
                "brand_id": "brand_001",
                "draft_text": ("Our cheapest plan is guaranteed to be revolutionary!!!"),
                "purpose": "marketing",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ai_status"] == "success"
        assert body["ai_error"] is None
        assert len(provider.calls) == 1
        voice_findings = [
            finding for finding in body["findings"] if finding["rule_id"] == "BR-VOICE-003"
        ]
        assert len(voice_findings) == 1
        assert voice_findings[0]["citation"]["source_id"] == "GL-B1-VOICE-003"

        detail = client.get(f"/api/reviews/{body['review_id']}")
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["ai_status"] == "success"
        assert detail_body["ai_error"] is None
        assert detail_body["findings"] == body["findings"]


def test_api_hybrid_ai_disabled_preserves_deterministic_findings(tmp_path):
    settings = _api_settings(tmp_path, ai_enabled=False)
    app = create_app(settings)

    with TestClient(app, raise_server_exceptions=False) as client:
        with app.state.db.session_factory() as session:
            _mark_guideline(session, "GL-B1-VOICE-003", "hybrid")

        response = client.post(
            "/api/review",
            json={
                "brand_id": "brand_001",
                "draft_text": ("Our cheapest plan is guaranteed to be revolutionary!!!"),
                "purpose": "marketing",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ai_status"] == "disabled"
        assert body["ai_error"]
        assert body["status"] == "needs_human_review"
        voice_findings = [
            finding for finding in body["findings"] if finding["rule_id"] == "BR-VOICE-003"
        ]
        assert len(voice_findings) == 1
        assert voice_findings[0]["explanation"].startswith("The draft uses a hype word")

        detail = client.get(f"/api/reviews/{body['review_id']}")
        assert detail.status_code == 200
        assert detail.json()["ai_status"] == "disabled"


def test_api_provider_timeout_preserves_deterministic_results(tmp_path):
    settings = _api_settings(tmp_path, ai_enabled=True)
    app = create_app(settings)

    with TestClient(app, raise_server_exceptions=False) as client:
        with app.state.db.session_factory() as session:
            _mark_guideline(session, "GL-B1-CLAIM-001", "hybrid")

        provider = FakeProvider(
            error=AIProviderError("request timed out after 30s", provider="fake")
        )
        service = ReviewService(settings, ai_provider=provider)
        app.dependency_overrides[get_review_service] = lambda: service

        response = client.post(
            "/api/review",
            json={
                "brand_id": "brand_001",
                "draft_text": "Guaranteed. Terms apply.",
                "purpose": "marketing",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ai_status"] == "timeout"
        error = (body["ai_error"] or "").lower()
        assert "timeout" in error or "timed out" in error
        assert body["status"] == "needs_human_review"
        assert any(finding["rule_id"] == "BR-CLAIM-001" for finding in body["findings"])

        detail = client.get(f"/api/reviews/{body['review_id']}")
        assert detail.status_code == 200
        assert detail.json()["ai_status"] == "timeout"
        assert len(provider.calls) == 1


def test_not_configured_is_reported_without_calling_provider():
    guideline = Guideline(
        id="GL-1",
        brand_id="brand_001",
        rule_id="BR-1",
        title="AI rule",
        version="v1",
        content="Rule text.",
        category="tone",
        severity="low",
        match_type="term",
        config_json={"check_method": "ai"},
        explanation="Test.",
        confidence=1.0,
        requires_human_review=False,
        is_active=True,
    )
    with (
        patch.object(ai_settings, "trueline_ai_enabled", False),
        patch.object(ai_settings, "anthropic_api_key", None),
    ):
        outcome = run_ai_review(
            draft_text="Text.",
            brand_id="brand_001",
            purpose="marketing",
            guidelines=[guideline],
            facts=[],
            evaluation_date=date(2026, 10, 24),
            provider=None,
            enabled=True,
        )

    assert outcome.status == AI_STATUS_NOT_CONFIGURED
    assert outcome.findings == []


def test_computed_only_skips_even_when_ai_package_is_unavailable():
    guideline = Guideline(
        id="GL-1",
        brand_id="brand_001",
        rule_id="BR-1",
        title="Computed rule",
        version="v1",
        content="Rule text.",
        category="tone",
        severity="low",
        match_type="term",
        config_json={"check_method": "computed"},
        explanation="Test.",
        confidence=1.0,
        requires_human_review=False,
        is_active=True,
    )
    with patch("app.ai_review.AI_ENGINE_AVAILABLE", False):
        outcome = run_ai_review(
            draft_text="Text.",
            brand_id="brand_001",
            purpose="marketing",
            guidelines=[guideline],
            facts=[],
            evaluation_date=date(2026, 10, 24),
            provider=None,
            enabled=True,
        )

    assert outcome.status == AI_STATUS_SKIPPED


def test_ai_guideline_reports_unavailable_without_package():
    guideline = Guideline(
        id="GL-1",
        brand_id="brand_001",
        rule_id="BR-1",
        title="AI rule",
        version="v1",
        content="Rule text.",
        category="tone",
        severity="low",
        match_type="term",
        config_json={"check_method": "ai"},
        explanation="Test.",
        confidence=1.0,
        requires_human_review=False,
        is_active=True,
    )
    with patch("app.ai_review.AI_ENGINE_AVAILABLE", False):
        outcome = run_ai_review(
            draft_text="Text.",
            brand_id="brand_001",
            purpose="marketing",
            guidelines=[guideline],
            facts=[],
            evaluation_date=date(2026, 10, 24),
            provider=None,
            enabled=True,
        )

    assert outcome.status == "unavailable"


def test_fact_status_and_supersession_are_preserved_and_filtered():
    guideline = Guideline(
        id="GL-1",
        brand_id="brand_001",
        rule_id="BR-1",
        title="AI rule",
        version="v1",
        content="Rule text.",
        category="tone",
        severity="low",
        match_type="term",
        config_json={"check_method": "ai"},
        explanation="Test.",
        confidence=1.0,
        requires_human_review=False,
        is_active=True,
    )
    active = ApprovedFact(
        id="FACT-ACTIVE",
        brand_id="brand_001",
        statement="Active fact.",
        source_label="Source",
        source_version="v1",
        is_active=True,
    )
    superseded = ApprovedFact(
        id="FACT-SUPERSEDED",
        brand_id="brand_001",
        statement="Old fact.",
        source_label="Source",
        source_version="v1",
        superseded_by="FACT-ACTIVE",
        is_active=True,
    )
    inactive = ApprovedFact(
        id="FACT-INACTIVE",
        brand_id="brand_001",
        statement="Inactive fact.",
        source_label="Source",
        source_version="v1",
        is_active=False,
    )
    provider = FakeProvider(findings=[])

    _, ai_facts = build_ai_inputs([guideline], [active, superseded, inactive], date(2026, 10, 24))
    statuses = {fact.id: fact.status_on_evaluation_date for fact in ai_facts}
    assert statuses == {
        "FACT-ACTIVE": "active",
        "FACT-SUPERSEDED": "superseded",
        "FACT-INACTIVE": "inactive",
    }
    superseded_fact = next(fact for fact in ai_facts if fact.id == "FACT-SUPERSEDED")
    assert superseded_fact.superseded_by == "FACT-ACTIVE"
    assert fact_is_current(superseded, date(2026, 10, 24)) is False
    assert fact_is_current(active, date(2026, 10, 24)) is True

    outcome = run_ai_review(
        draft_text="Text.",
        brand_id="brand_001",
        purpose="marketing",
        guidelines=[guideline],
        facts=[active, superseded, inactive],
        evaluation_date=date(2026, 10, 24),
        provider=provider,
        enabled=True,
    )

    assert outcome.status == AI_STATUS_SUCCESS
    assert [fact.id for fact in provider.calls[0]["approved_facts"]] == ["FACT-ACTIVE"]

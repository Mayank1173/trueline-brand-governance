"""Checks against frontend/src/lib/types.ts and the mock service contract."""

from __future__ import annotations

FRONTEND_STATUSES = {
    "approved",
    "changes_requested",
    "needs_human_review",
    "pending_approval",
    "rejected",
}
FRONTEND_SEVERITIES = {"low", "medium", "high"}
REQUIRED_FINDING_FIELDS = {
    "id",
    "finding_id",
    "rule_id",
    "matched_text",
    "start",
    "end",
    "category",
    "severity",
    "explanation",
    "citation",
    "suggested_fix",
    "confidence",
    "requires_human_review",
    "ai_label",
}


def test_response_shape_is_compatible_with_frontend(client, demo_payload):
    response = client.post("/api/review", json=demo_payload)
    assert response.status_code == 200
    body = response.json()

    assert set(body) == {
        "review_id",
        "status",
        "findings",
        "ai_status",
        "ai_error",
    }
    assert isinstance(body["review_id"], str) and body["review_id"]
    assert body["status"] in FRONTEND_STATUSES
    assert body["ai_status"] == "skipped"
    assert body["ai_error"] is None
    assert isinstance(body["findings"], list)

    for finding in body["findings"]:
        assert set(finding) == REQUIRED_FINDING_FIELDS
        assert isinstance(finding["id"], str)
        assert finding["id"] == finding["finding_id"]
        assert finding["severity"] in FRONTEND_SEVERITIES
        assert isinstance(finding["requires_human_review"], bool)
        assert finding["ai_label"] is None
        assert isinstance(finding["confidence"], float)
        assert finding["suggested_fix"] is None or isinstance(
            finding["suggested_fix"], str
        )
        citation = finding["citation"]
        if citation is not None:
            assert {
                "rule_id",
                "source",
                "excerpt",
                "source_type",
                "source_id",
                "source_version",
                "quoted_text",
                "valid_until",
            } <= set(citation)
            assert citation["rule_id"] == finding["rule_id"]
            assert citation["source"]
            assert citation["excerpt"] == citation["quoted_text"]


def test_clean_review_response_uses_frontend_pending_status(client):
    response = client.post(
        "/api/review",
        json={
            "brand_id": "brand_001",
            "draft_text": "Trueline helps customers. Terms apply.",
            "purpose": "marketing",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_approval"
    assert body["findings"] == []


def test_offsets_can_replace_matched_text_like_applyFix(client):
    draft = "Our cheapest plan is guaranteed. Terms apply."
    response = client.post(
        "/api/review",
        json={"brand_id": "brand_001", "draft_text": draft, "purpose": "marketing"},
    )
    assert response.status_code == 200
    findings = response.json()["findings"]
    fixable = [
        finding
        for finding in findings
        if finding["suggested_fix"] is not None and finding["matched_text"]
    ]
    assert fixable

    for finding in fixable:
        assert draft[finding["start"] : finding["end"]] == finding["matched_text"]
        updated = (
            draft[: finding["start"]]
            + finding["suggested_fix"]
            + draft[finding["end"] :]
        )
        assert finding["suggested_fix"] in updated


def test_missing_phrase_allows_frontend_append_behaviour(client):
    response = client.post(
        "/api/review",
        json={
            "brand_id": "brand_001",
            "draft_text": "A promotional offer.",
            "purpose": "marketing",
        },
    )
    finding = response.json()["findings"][0]
    assert finding["matched_text"] == ""
    assert finding["start"] is None
    assert finding["end"] is None
    updated = f"{'A promotional offer.'.rstrip()} {finding['suggested_fix']}"
    assert updated.endswith("Terms apply.")


def test_citation_source_ids_exist_in_guideline_endpoint(client):
    response = client.post(
        "/api/review",
        json={
            "brand_id": "brand_001",
            "draft_text": "Cheapest and guaranteed. Terms apply.",
            "purpose": "marketing",
        },
    )
    findings = response.json()["findings"]
    source_ids = {
        finding["citation"]["source_id"]
        for finding in findings
        if finding["citation"] and finding["citation"]["source_type"] == "guideline"
    }
    guidelines = client.get("/api/brands/brand_001/guidelines").json()["guidelines"]
    known_ids = {guideline["source_id"] for guideline in guidelines}
    assert source_ids
    assert source_ids <= known_ids

from __future__ import annotations


def review(
    client, text: str, *, brand_id: str = "brand_001", purpose: str = "marketing"
):
    return client.post(
        "/api/review",
        json={"brand_id": brand_id, "draft_text": text, "purpose": purpose},
    )


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_brands_and_guidelines_are_scoped(client):
    brands = client.get("/api/brands")
    assert brands.status_code == 200
    assert {brand["id"] for brand in brands.json()} == {"brand_001", "brand-demo"}

    response = client.get("/api/brands/brand_001/guidelines")
    assert response.status_code == 200
    body = response.json()
    assert body["brand"]["id"] == "brand_001"
    assert body["guidelines"]
    assert all(rule["source_id"].startswith("GL-B1-") for rule in body["guidelines"])

    other = client.get("/api/brands/brand-demo/guidelines")
    assert other.status_code == 200
    assert all(
        rule["source_id"].startswith("GL-BD-") for rule in other.json()["guidelines"]
    )


def test_valid_review_returns_grounded_findings(client, demo_payload):
    response = client.post("/api/review", json=demo_payload)
    assert response.status_code == 200
    body = response.json()

    assert body["review_id"].startswith("review_")
    assert body["status"] == "needs_human_review"
    assert body["findings"]

    rules = {finding["rule_id"] for finding in body["findings"]}
    assert {
        "BR-TERM-014",
        "BR-CLAIM-001",
        "BR-VOICE-003",
        "BR-FMT-002",
        "BR-TERM-020",
        "BR-PRODUCT-001",
        "BR-LEGAL-002",
    } <= rules

    for finding in body["findings"]:
        assert finding["id"] == finding["finding_id"]
        assert finding["severity"] in {"low", "medium", "high"}
        assert 0.0 <= finding["confidence"] <= 1.0
        if finding["matched_text"]:
            start, end = finding["start"], finding["end"]
            assert demo_payload["draft_text"][start:end] == finding["matched_text"]
            assert finding["citation"] is not None
            citation = finding["citation"]
            assert citation["source_id"]
            assert citation["source_version"] == "demo-ruleset-2026.10"
            assert citation["quoted_text"]
            assert citation["excerpt"] == citation["quoted_text"]


def test_multiple_findings_are_returned(client):
    response = review(client, "Cheapest and guaranteed and revolutionary!!!")
    assert response.status_code == 200
    rule_ids = {finding["rule_id"] for finding in response.json()["findings"]}
    assert {"BR-TERM-014", "BR-CLAIM-001", "BR-VOICE-003", "BR-FMT-002"} <= rule_ids


def test_clean_draft_is_approved(client):
    response = review(client, "Trueline helps customers. Terms apply.")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["findings"] == []


def test_case_insensitive_matching_preserves_original_text(client):
    response = review(client, "USERS and Cheapest. TERMS APPLY.")
    assert response.status_code == 200
    findings = response.json()["findings"]
    matched = {finding["matched_text"] for finding in findings}
    assert {"USERS", "Cheapest"} <= matched
    assert all(finding["rule_id"] != "BR-LEGAL-002" for finding in findings)


def test_missing_required_phrase_uses_empty_match_and_no_offsets(client):
    response = review(client, "A simple promotional offer.")
    assert response.status_code == 200
    findings = response.json()["findings"]
    assert len(findings) == 1
    finding = findings[0]
    assert finding["rule_id"] == "BR-LEGAL-002"
    assert finding["category"] == "required_phrase"
    assert finding["matched_text"] == ""
    assert finding["start"] is None
    assert finding["end"] is None
    assert finding["suggested_fix"] == "Terms apply."
    assert response.json()["status"] == "changes_requested"


def test_length_limit_is_enforced(client):
    text = ("a" * 1201) + " Terms apply."
    response = review(client, text)
    assert response.status_code == 200
    findings = response.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "BR-LIMIT-001"
    assert findings[0]["category"] == "length_limit"
    assert findings[0]["start"] is None


def test_expired_fact_is_flagged_and_cites_approved_fact(client):
    response = review(client, "Offer: Free returns within 30 days. Terms apply.")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_human_review"
    findings = [f for f in body["findings"] if f["category"] == "fact_metadata"]
    assert len(findings) == 1
    finding = findings[0]
    assert finding["matched_text"] == "Free returns within 30 days."
    assert finding["citation"]["source_type"] == "approved_fact"
    assert finding["citation"]["source_id"].startswith("FACT-B1-")
    assert finding["requires_human_review"] is True


def test_current_approved_fact_is_not_flagged(client):
    response = review(client, "Free shipping on orders over $50. Terms apply.")
    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_brand_scoping_uses_that_brands_sources(client):
    response = review(client, "Cheapest. Terms apply.", brand_id="brand-demo")
    assert response.status_code == 200
    source_ids = [
        finding["citation"]["source_id"]
        for finding in response.json()["findings"]
        if finding["citation"]
    ]
    assert source_ids
    assert all(source_id.startswith("GL-BD-") for source_id in source_ids)


def test_empty_draft_is_rejected(client):
    response = review(client, "   \n\t ")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_missing_required_fields_are_rejected(client):
    response = client.post("/api/review", json={"brand_id": "brand_001"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_invalid_types_are_rejected(client):
    response = client.post(
        "/api/review",
        json={"brand_id": "brand_001", "draft_text": 123, "purpose": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_brand_returns_404(client):
    response = review(client, "Terms apply.", brand_id="does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_oversized_draft_returns_413(client):
    response = review(client, "a" * 5001)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "draft_too_large"


def test_unknown_fields_are_rejected(client, demo_payload):
    payload = {**demo_payload, "admin": True}
    response = client.post("/api/review", json=payload)
    assert response.status_code == 422


def test_review_is_persisted_and_retrievable(client, demo_payload):
    created = client.post("/api/review", json=demo_payload)
    assert created.status_code == 200
    review_id = created.json()["review_id"]

    fetched = client.get(f"/api/reviews/{review_id}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["review_id"] == review_id
    assert body["draft_text"] == demo_payload["draft_text"]
    assert body["brand_id"] == "brand_001"
    assert body["created_at"].endswith(("Z", "+00:00"))
    assert len(body["findings"]) == len(created.json()["findings"])
    assert body["findings"][0]["id"] == created.json()["findings"][0]["id"]


def test_review_history_is_recorded(client, demo_payload):
    created = client.post("/api/review", json=demo_payload)
    review_id = created.json()["review_id"]

    history = client.get(f"/api/reviews/{review_id}/history")
    assert history.status_code == 200
    events = history.json()["events"]
    assert [event["event_type"] for event in events] == [
        "review_created",
        "review_completed",
    ]
    assert events[0]["actor_type"] == "system"
    assert events[0]["at"].endswith(("Z", "+00:00"))


def test_review_list_pagination(client):
    for index in range(3):
        response = review(client, f"Cheapest offer number {index}. Terms apply.")
        assert response.status_code == 200

    first_page = client.get("/api/reviews", params={"limit": 2, "offset": 0})
    assert first_page.status_code == 200
    body = first_page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0

    second_page = client.get("/api/reviews", params={"limit": 2, "offset": 2})
    assert second_page.status_code == 200
    assert len(second_page.json()["items"]) == 1

    filtered = client.get("/api/reviews", params={"brand_id": "brand-demo"})
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0


def test_invalid_pagination_is_rejected(client):
    assert client.get("/api/reviews", params={"limit": 0}).status_code == 422
    assert client.get("/api/reviews", params={"limit": 101}).status_code == 422
    assert client.get("/api/reviews", params={"offset": -1}).status_code == 422


def test_unknown_review_returns_404(client):
    assert client.get("/api/reviews/review_missing").status_code == 404
    assert client.get("/api/reviews/review_missing/history").status_code == 404


def test_unknown_brand_filter_returns_404(client):
    response = client.get("/api/reviews", params={"brand_id": "missing"})
    assert response.status_code == 404


def test_facts_endpoint_reports_validity(client):
    response = client.get("/api/brands/brand_001/facts")
    assert response.status_code == 200
    facts = response.json()["approved_facts"]
    expired = [fact for fact in facts if fact["valid_until"] == "2020-01-01"]
    assert len(expired) == 1
    assert expired[0]["is_current"] is False
    assert all(
        fact["source"].startswith("Illustrative Demo Fact Library") for fact in facts
    )


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/api/review",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in {200, 204}
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )
    assert response.headers.get("access-control-allow-credentials") is None

"""Review submission, retrieval, and history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from ..presenters import (
    finding_response,
    review_detail,
    review_event_response,
    review_summary,
)
from ..schemas import (
    ReviewDetail,
    ReviewHistoryResponse,
    ReviewListResponse,
    ReviewRequest,
    ReviewResponse,
)
from .deps import ReviewServiceDep, SessionDep

router = APIRouter(prefix="/api", tags=["reviews"])


@router.post("/review", response_model=ReviewResponse)
def submit_review(
    payload: ReviewRequest,
    request: Request,
    session: SessionDep,
    service: ReviewServiceDep,
) -> ReviewResponse:
    settings = request.app.state.settings

    if len(payload.draft_text) > settings.max_draft_chars:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "draft_too_large",
                "message": (
                    f"draft_text exceeds the configured limit of "
                    f"{settings.max_draft_chars} characters."
                ),
            },
        )
    if len(payload.purpose or "") > settings.max_purpose_chars:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "purpose_too_long",
                "message": (
                    f"purpose exceeds the configured limit of "
                    f"{settings.max_purpose_chars} characters."
                ),
            },
        )

    review = service.submit(session, payload)
    return ReviewResponse(
        review_id=review.id,
        status=review.status,
        findings=[finding_response(finding) for finding in review.findings],
    )


@router.get("/reviews", response_model=ReviewListResponse)
def list_reviews(
    session: SessionDep,
    service: ReviewServiceDep,
    brand_id: str | None = Query(default=None, min_length=1, max_length=64),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ReviewListResponse:
    reviews, total = service.list_reviews(
        session, brand_id=brand_id, limit=limit, offset=offset
    )
    return ReviewListResponse(
        items=[review_summary(review) for review in reviews],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/reviews/{review_id}", response_model=ReviewDetail)
def get_review(
    review_id: str,
    session: SessionDep,
    service: ReviewServiceDep,
) -> ReviewDetail:
    review = service.get_review(session, review_id)
    return review_detail(review)


@router.get("/reviews/{review_id}/history", response_model=ReviewHistoryResponse)
def get_review_history(
    review_id: str,
    session: SessionDep,
    service: ReviewServiceDep,
) -> ReviewHistoryResponse:
    review = service.get_review(session, review_id)
    return ReviewHistoryResponse(
        review_id=review.id,
        events=[review_event_response(event) for event in review.events],
    )

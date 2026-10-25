"""Read-only brand, guideline, and approved-fact endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Path

from ..presenters import (
    brand_response,
    fact_response,
    guideline_response,
)
from ..schemas import (
    BrandFactsResponse,
    BrandGuidelinesResponse,
    BrandResponse,
)
from .deps import ReviewServiceDep, SessionDep

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("", response_model=list[BrandResponse])
def list_brands(
    session: SessionDep,
    service: ReviewServiceDep,
) -> list[BrandResponse]:
    return [brand_response(brand) for brand in service.list_brands(session)]


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(
    session: SessionDep,
    service: ReviewServiceDep,
    brand_id: str = Path(min_length=1, max_length=64),
) -> BrandResponse:
    brand, _guidelines = service.get_guidelines(session, brand_id)
    return brand_response(brand)


@router.get("/{brand_id}/guidelines", response_model=BrandGuidelinesResponse)
def get_guidelines(
    session: SessionDep,
    service: ReviewServiceDep,
    brand_id: str = Path(min_length=1, max_length=64),
) -> BrandGuidelinesResponse:
    brand, guidelines = service.get_guidelines(session, brand_id)
    return BrandGuidelinesResponse(
        brand=brand_response(brand),
        guidelines=[guideline_response(row) for row in guidelines],
    )


@router.get("/{brand_id}/facts", response_model=BrandFactsResponse)
def get_facts(
    session: SessionDep,
    service: ReviewServiceDep,
    brand_id: str = Path(min_length=1, max_length=64),
) -> BrandFactsResponse:
    brand, facts = service.get_facts(session, brand_id)
    return BrandFactsResponse(
        brand=brand_response(brand),
        approved_facts=[fact_response(row) for row in facts],
    )

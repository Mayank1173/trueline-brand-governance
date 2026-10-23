"""Database models for brands, guidelines, facts, reviews, and audit events."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Brand(TimestampMixin, Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    guidelines: Mapped[list[Guideline]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )
    approved_facts: Mapped[list[ApprovedFact]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )


class Guideline(TimestampMixin, Base):
    """One approved guideline rule and the exact source text it cites."""

    __tablename__ = "guidelines"
    __table_args__ = (
        UniqueConstraint("brand_id", "rule_id", name="uq_guidelines_brand_rule"),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    brand_id: Mapped[str] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    brand: Mapped[Brand] = relationship(back_populates="guidelines")


class ApprovedFact(TimestampMixin, Base):
    __tablename__ = "approved_facts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    brand_id: Mapped[str] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    source_version: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    brand: Mapped[Brand] = relationship(back_populates="approved_facts")


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    brand_id: Mapped[str] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    ruleset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)

    brand: Mapped[Brand] = relationship(back_populates="reviews")
    findings: Mapped[list[ReviewFinding]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="ReviewFinding.created_at, ReviewFinding.id",
    )
    events: Mapped[list[ReviewEvent]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="ReviewEvent.sequence, ReviewEvent.created_at, ReviewEvent.id",
    )


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    matched_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    citation_source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    citation_source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    citation_source_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    citation_source_label: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    citation_quoted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    review: Mapped[Review] = relationship(back_populates="findings")


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    review: Mapped[Review] = relationship(back_populates="events")

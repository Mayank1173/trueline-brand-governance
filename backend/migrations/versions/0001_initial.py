"""Initial Trueline review schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "guidelines",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("brand_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("section", sa.String(length=64), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("match_type", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_id", "rule_id", name="uq_guidelines_brand_rule"),
    )
    op.create_index("ix_guidelines_brand_id", "guidelines", ["brand_id"])
    op.create_index("ix_guidelines_rule_id", "guidelines", ["rule_id"])
    op.create_index("ix_guidelines_category", "guidelines", ["category"])

    op.create_table(
        "approved_facts",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("brand_id", sa.String(length=64), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("source_version", sa.String(length=64), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approved_facts_brand_id", "approved_facts", ["brand_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("brand_id", sa.String(length=64), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ruleset_version", sa.String(length=64), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_brand_id", "reviews", ["brand_id"])
    op.create_index("ix_reviews_status", "reviews", ["status"])

    op.create_table(
        "review_findings",
        sa.Column("id", sa.String(length=160), nullable=False),
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("matched_text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("citation_source_type", sa.String(length=32), nullable=True),
        sa.Column("citation_source_id", sa.String(length=128), nullable=True),
        sa.Column("citation_source_version", sa.String(length=64), nullable=True),
        sa.Column("citation_source_label", sa.String(length=255), nullable=True),
        sa.Column("citation_quoted_text", sa.Text(), nullable=True),
        sa.Column("citation_valid_until", sa.Date(), nullable=True),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_findings_review_id", "review_findings", ["review_id"])
    op.create_index("ix_review_findings_rule_id", "review_findings", ["rule_id"])

    op.create_table(
        "review_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_events_review_id", "review_events", ["review_id"])


def downgrade() -> None:
    op.drop_index("ix_review_events_review_id", table_name="review_events")
    op.drop_table("review_events")

    op.drop_index("ix_review_findings_rule_id", table_name="review_findings")
    op.drop_index("ix_review_findings_review_id", table_name="review_findings")
    op.drop_table("review_findings")

    op.drop_index("ix_reviews_status", table_name="reviews")
    op.drop_index("ix_reviews_brand_id", table_name="reviews")
    op.drop_table("reviews")

    op.drop_index("ix_approved_facts_brand_id", table_name="approved_facts")
    op.drop_table("approved_facts")

    op.drop_index("ix_guidelines_category", table_name="guidelines")
    op.drop_index("ix_guidelines_rule_id", table_name="guidelines")
    op.drop_index("ix_guidelines_brand_id", table_name="guidelines")
    op.drop_table("guidelines")

    op.drop_table("brands")

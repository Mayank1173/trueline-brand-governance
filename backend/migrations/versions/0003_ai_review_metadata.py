"""Persist AI execution status and approved-fact supersession.

Revision ID: 0003_ai_review_metadata
Revises: 0002_nullable_versions_ai_label
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ai_review_metadata"
down_revision: str | None = "0002_nullable_versions_ai_label"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.add_column(sa.Column("ai_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("ai_error", sa.Text(), nullable=True))

    with op.batch_alter_table("approved_facts") as batch_op:
        batch_op.add_column(sa.Column("superseded_by", sa.String(length=128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("approved_facts") as batch_op:
        batch_op.drop_column("superseded_by")

    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_column("ai_error")
        batch_op.drop_column("ai_status")

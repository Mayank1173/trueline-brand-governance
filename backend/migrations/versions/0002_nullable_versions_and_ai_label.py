"""Allow unversioned approved sources and add the nullable AI label.

Revision ID: 0002_nullable_versions_ai_label
Revises: 0001_initial
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_nullable_versions_ai_label"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("guidelines") as batch_op:
        batch_op.alter_column(
            "version",
            existing_type=sa.String(length=64),
            existing_nullable=False,
            nullable=True,
        )

    with op.batch_alter_table("approved_facts") as batch_op:
        batch_op.alter_column(
            "source_version",
            existing_type=sa.String(length=64),
            existing_nullable=False,
            nullable=True,
        )

    with op.batch_alter_table("review_findings") as batch_op:
        batch_op.add_column(sa.Column("ai_label", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("review_findings") as batch_op:
        batch_op.drop_column("ai_label")

    with op.batch_alter_table("approved_facts") as batch_op:
        batch_op.alter_column(
            "source_version",
            existing_type=sa.String(length=64),
            existing_nullable=True,
            nullable=False,
        )

    with op.batch_alter_table("guidelines") as batch_op:
        batch_op.alter_column(
            "version",
            existing_type=sa.String(length=64),
            existing_nullable=True,
            nullable=False,
        )

"""Contractor on a realized dedication, and a close-chance on meetings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261102_0008"
down_revision: str | None = "20261102_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dedication_contractors",
        sa.Column("dedication_id", sa.String(length=36), sa.ForeignKey("dedications.id"), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
    )
    op.create_index("ix_dedication_contractors_synagogue_id", "dedication_contractors", ["synagogue_id"])
    op.add_column("meetings", sa.Column("close_chance", sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "close_chance")
    op.drop_index("ix_dedication_contractors_synagogue_id", table_name="dedication_contractors")
    op.drop_table("dedication_contractors")

"""Calculator settings and proposal tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0003"
down_revision: str | None = "20261031_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    _create_calculator_settings()
    _create_proposals()


def downgrade() -> None:
    op.drop_table("proposals")
    op.drop_table("calculator_settings")


def _create_calculator_settings() -> None:
    op.create_table(
        "calculator_settings",
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("min_monthly", sa.Numeric(14, 2), nullable=False),
        sa.Column("max_monthly", sa.Numeric(14, 2), nullable=False),
        sa.Column("max_months", sa.Integer(), nullable=False),
        sa.Column("min_per_donor", sa.Numeric(14, 2), nullable=False),
        sa.Column("max_per_donor", sa.Numeric(14, 2), nullable=False),
        sa.Column("min_donors", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
    )
    op.create_index("ix_calculator_settings_synagogue_id", "calculator_settings", ["synagogue_id"])


def _create_proposals() -> None:
    op.create_table(
        "proposals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("dedication_id", sa.String(length=36), sa.ForeignKey("dedications.id"), nullable=False),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("months", sa.Integer(), nullable=False),
        sa.Column("donor_count", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("financed_total", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_proposals_project_id", "proposals", ["project_id"])
    op.create_index("ix_proposals_synagogue_id", "proposals", ["synagogue_id"])
    op.create_index("ix_proposals_synagogue_project", "proposals", ["synagogue_id", "project_id"])

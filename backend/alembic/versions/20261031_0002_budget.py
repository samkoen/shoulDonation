"""Budget tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0002"
down_revision: str | None = "20261031_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "construction_budgets",
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("construction_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("target_percent", sa.Numeric(7, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
    )
    op.create_index("ix_construction_budgets_synagogue_id", "construction_budgets", ["synagogue_id"])
    op.create_table(
        "dedications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_dedications_project_name"),
    )
    op.create_index("ix_dedications_project_id", "dedications", ["project_id"])
    op.create_index("ix_dedications_synagogue_id", "dedications", ["synagogue_id"])


def downgrade() -> None:
    op.drop_table("dedications")
    op.drop_table("construction_budgets")

"""Building plan image stored with the project."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0005"
down_revision: str | None = "20261031_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_plans",
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
    )
    op.create_index("ix_project_plans_synagogue_id", "project_plans", ["synagogue_id"])


def downgrade() -> None:
    op.drop_index("ix_project_plans_synagogue_id", table_name="project_plans")
    op.drop_table("project_plans")

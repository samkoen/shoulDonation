"""Colored region on the building plan for each dedication."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261102_0009"
down_revision: str | None = "20261102_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("dedications") as batch:
        batch.add_column(sa.Column("plan_region", sa.String(length=8000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dedications") as batch:
        batch.drop_column("plan_region")

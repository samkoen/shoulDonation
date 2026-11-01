"""Dedication position on the building plan."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261101_0006"
down_revision: str | None = "20261031_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("dedications") as batch:
        batch.add_column(sa.Column("plan_x", sa.Numeric(5, 2), nullable=True))
        batch.add_column(sa.Column("plan_y", sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dedications") as batch:
        batch.drop_column("plan_y")
        batch.drop_column("plan_x")

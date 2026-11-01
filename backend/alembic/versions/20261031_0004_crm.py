"""Lead and meeting tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0004"
down_revision: str | None = "20261031_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    _create_leads()
    _create_meetings()


def downgrade() -> None:
    op.drop_table("meetings")
    op.drop_table("leads")


def _create_leads() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("dedication_id", sa.String(length=36), sa.ForeignKey("dedications.id"), nullable=True),
        sa.Column("assignee_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("requested_synagogue_name", sa.String(length=200), nullable=True),
    )
    op.create_index("ix_leads_synagogue_id", "leads", ["synagogue_id"])
    op.create_index("ix_leads_project_id", "leads", ["project_id"])
    op.create_index("ix_leads_assignee_id", "leads", ["assignee_id"])
    op.create_index("ix_leads_synagogue_project", "leads", ["synagogue_id", "project_id"])


def _create_meetings() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lead_id", sa.String(length=36), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=False),
    )
    op.create_index("ix_meetings_lead_id", "meetings", ["lead_id"])

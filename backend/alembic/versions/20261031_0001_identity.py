"""Identity tables. Types stay portable so the same migration can target PostgreSQL later."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synagogues",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_memberships_synagogue_id", "memberships", ["synagogue_id"])
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.UniqueConstraint("synagogue_id", "name", name="uq_projects_synagogue_name"),
    )
    op.create_index("ix_projects_synagogue_id", "projects", ["synagogue_id"])
    op.create_table(
        "project_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("synagogue_id", sa.String(length=36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_assignments_project_user"),
    )
    op.create_index("ix_project_assignments_synagogue_id", "project_assignments", ["synagogue_id"])
    op.create_index("ix_project_assignments_user_id", "project_assignments", ["user_id"])


def downgrade() -> None:
    op.drop_table("project_assignments")
    op.drop_table("projects")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("synagogues")

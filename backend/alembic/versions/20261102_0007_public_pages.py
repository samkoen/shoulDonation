"""Public project pages and their gallery images."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261102_0007"
down_revision: str | None = "20261101_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "public_pages",
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column("synagogue_id", sa.String(36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("vision", sa.String(2000), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_public_pages_slug"),
    )
    op.create_index("ix_public_pages_synagogue_id", "public_pages", ["synagogue_id"])
    op.create_table(
        "gallery_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("synagogue_id", sa.String(36), sa.ForeignKey("synagogues.id"), nullable=False),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index("ix_gallery_images_project_id", "gallery_images", ["project_id"])
    op.create_index("ix_gallery_images_synagogue_id", "gallery_images", ["synagogue_id"])


def downgrade() -> None:
    op.drop_index("ix_gallery_images_synagogue_id", table_name="gallery_images")
    op.drop_index("ix_gallery_images_project_id", table_name="gallery_images")
    op.drop_table("gallery_images")
    op.drop_index("ix_public_pages_synagogue_id", table_name="public_pages")
    op.drop_table("public_pages")

"""Apply Alembic migrations. The same scripts will run later on PostgreSQL."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from shoul_donation.infrastructure.database import ensure_sqlite_parent


def upgrade_to_head(database_url: str) -> None:
    ensure_sqlite_parent(database_url)
    backend_root = Path(__file__).resolve().parents[3]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    config.set_main_option("script_location", (backend_root / "alembic").as_posix())
    command.upgrade(config, "head")

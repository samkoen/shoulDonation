"""SQLite constraints that the repositories rely on."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from shoul_donation.infrastructure.database import create_engine_from_url, sqlite_url
from shoul_donation.infrastructure.migrations import upgrade_to_head


def test_upgrade_creates_the_sqlite_directory(tmp_path) -> None:
    database = tmp_path / "nested" / "app.db"
    upgrade_to_head(sqlite_url(database))
    assert database.exists()


def test_project_requires_an_existing_synagogue(tmp_path) -> None:
    engine = create_engine_from_url(sqlite_url(tmp_path / "constraints.db"))
    upgrade_to_head(sqlite_url(tmp_path / "constraints.db"))
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO projects (id, synagogue_id, name) VALUES (:id, :synagogue_id, :name)"),
                {"id": str(uuid4()), "synagogue_id": str(uuid4()), "name": "Orphan"},
            )
    engine.dispose()

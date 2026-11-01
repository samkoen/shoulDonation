"""The API process also serves the built public UI when the dist folder exists."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shoul_donation.config import Settings
from shoul_donation.infrastructure.api.app import create_app
from shoul_donation.infrastructure.database import create_engine_from_url, session_factory_for, sqlite_url
from shoul_donation.infrastructure.migrations import upgrade_to_head


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    database_url = sqlite_url(tmp_path / "ui.db")
    upgrade_to_head(database_url)
    engine = create_engine_from_url(database_url)
    settings = Settings(_env_file=None, database_url=database_url, jwt_secret="test-secret-key-with-enough-length")
    app = create_app(settings, session_factory_for(engine))
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def test_the_ui_is_served_next_to_the_api(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert b"ui" in page.content
    assert client.get("/login").status_code == 200
    assert client.get("/api/health").json() == {"status": "ok"}

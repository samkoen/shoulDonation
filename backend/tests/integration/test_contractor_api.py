"""Contractor HTTP flow against a migrated SQLite file."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shoul_donation.config import Settings
from shoul_donation.infrastructure.api.app import create_app
from shoul_donation.infrastructure.database import create_engine_from_url, session_factory_for, sqlite_url
from shoul_donation.infrastructure.migrations import upgrade_to_head

ADMIN_EMAIL = "admin@shoul.test"
ADMIN_PASSWORD = "admin-pass-1"
USER_PASSWORD = "user-pass-1"


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    database_url = sqlite_url(tmp_path / "contractor.db")
    upgrade_to_head(database_url)
    engine = create_engine_from_url(database_url)
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret="test-secret-key-with-enough-length",
        password_iterations=1_000,
        platform_admin_email=ADMIN_EMAIL,
        platform_admin_password=ADMIN_PASSWORD,
    )
    app = create_app(settings, session_factory_for(engine))
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def test_a_contractor_is_saved_only_after_the_dedication_is_realized(client: TestClient) -> None:
    admin = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create(client, admin, "/api/synagogues", {"name": "North"})
    project = _create(client, admin, "/api/projects", {"synagogue_id": synagogue["id"], "name": "Hall"})
    dedication = _create(client, admin, f"/api/projects/{project['id']}/dedications", {"name": "Aron", "price": "100.00"})
    early = client.put(
        f"/api/dedications/{dedication['id']}/contractor",
        headers=_headers(admin),
        json={"name": "Amos", "phone": "0501112233", "amount": "80.00"},
    )
    assert early.status_code == 422
    client.patch(f"/api/dedications/{dedication['id']}", headers=_headers(admin), json={"status": "realized"})
    saved = client.put(
        f"/api/dedications/{dedication['id']}/contractor",
        headers=_headers(admin),
        json={"name": "Amos", "phone": "0501112233", "amount": "80.00"},
    )
    assert saved.status_code == 200
    assert saved.json()["amount"] == "80.00"
    listed = client.get(f"/api/dedications/{dedication['id']}/contractor", headers=_headers(admin))
    assert listed.json()["name"] == "Amos"


def _create(client: TestClient, token: str, path: str, body: dict) -> dict:
    response = client.post(path, headers=_headers(token), json=body)
    assert response.status_code == 200
    return response.json()


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

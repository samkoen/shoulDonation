"""HTTP flow against a migrated SQLite file."""

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
    database_url = sqlite_url(tmp_path / "identity.db")
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


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_invalid_login_is_rejected(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-pass-1"})
    assert response.status_code == 401


def test_sub_projector_sees_only_the_assigned_project(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    north = _create_synagogue(client, admin_token, "North")
    south = _create_synagogue(client, admin_token, "South")
    lead = _create_user(client, admin_token, "lead@shoul.test", "lead_projector", north["id"])
    sub = _create_user(client, admin_token, "sub@shoul.test", "sub_projector", north["id"])
    lead_token = _login(client, "lead@shoul.test", USER_PASSWORD)
    hall = _create_project(client, lead_token, north["id"], "Main hall")
    _create_project(client, admin_token, south["id"], "Other hall")
    assert [item["name"] for item in _projects(client, lead_token)] == ["Main hall"]
    _assign(client, lead_token, hall["id"], sub["id"])
    sub_token = _login(client, "sub@shoul.test", USER_PASSWORD)
    assert [item["name"] for item in _projects(client, sub_token)] == ["Main hall"]
    forbidden = client.post(
        "/api/projects",
        headers=_headers(sub_token),
        json={"synagogue_id": north["id"], "name": "Secret hall"},
    )
    assert forbidden.status_code == 403
    assert lead["email"] == "lead@shoul.test"


def test_lead_projector_cannot_list_every_synagogue(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin_token, "North")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", synagogue["id"])
    response = client.get("/api/synagogues", headers=_headers(_login(client, "lead@shoul.test", USER_PASSWORD)))
    assert response.status_code == 403


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_synagogue(client: TestClient, token: str, name: str) -> dict[str, str]:
    response = client.post("/api/synagogues", headers=_headers(token), json={"name": name})
    assert response.status_code == 200
    return response.json()


def _create_user(client: TestClient, token: str, email: str, role: str, synagogue_id: str) -> dict[str, str]:
    response = client.post(
        "/api/users",
        headers=_headers(token),
        json={"email": email, "password": USER_PASSWORD, "role": role, "synagogue_id": synagogue_id},
    )
    assert response.status_code == 200
    return response.json()


def _create_project(client: TestClient, token: str, synagogue_id: str, name: str) -> dict[str, str]:
    response = client.post(
        "/api/projects",
        headers=_headers(token),
        json={"synagogue_id": synagogue_id, "name": name},
    )
    assert response.status_code == 200
    return response.json()


def _assign(client: TestClient, token: str, project_id: str, user_id: str) -> None:
    response = client.post(
        f"/api/projects/{project_id}/assignments",
        headers=_headers(token),
        json={"user_id": user_id},
    )
    assert response.status_code == 200


def _projects(client: TestClient, token: str) -> list[dict[str, str]]:
    response = client.get("/api/projects", headers=_headers(token))
    assert response.status_code == 200
    return response.json()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

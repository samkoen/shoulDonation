"""Budget HTTP flow against a migrated SQLite file."""

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
    database_url = sqlite_url(tmp_path / "budget.db")
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


def test_prices_and_status_follow_the_role(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin_token, "North")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", synagogue["id"])
    sub = _create_user(client, admin_token, "sub@shoul.test", "sub_projector", synagogue["id"])
    lead_token = _login(client, "lead@shoul.test", USER_PASSWORD)
    project = _create_project(client, lead_token, synagogue["id"], "Main hall")
    _assign(client, lead_token, project["id"], sub["id"])
    _set_budget(client, lead_token, project["id"])
    first = _add_dedication(client, lead_token, project["id"], "Aron", "700.00")
    _add_dedication(client, lead_token, project["id"], "Bimah", "300.00")
    assert _budget(client, lead_token, project["id"])["gap"] == "200.00"
    sub_token = _login(client, "sub@shoul.test", USER_PASSWORD)
    updated = _patch(client, sub_token, first["id"], {"status": "fundraising"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "fundraising"
    refused = _patch(client, sub_token, first["id"], {"price": "10.00"})
    assert refused.status_code == 403


def test_another_synagogue_cannot_read_the_budget(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    north = _create_synagogue(client, admin_token, "North")
    south = _create_synagogue(client, admin_token, "South")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", north["id"])
    project = _create_project(client, admin_token, south["id"], "Other hall")
    response = client.get(
        f"/api/projects/{project['id']}/budget",
        headers=_headers(_login(client, "lead@shoul.test", USER_PASSWORD)),
    )
    assert response.status_code == 403


def _set_budget(client: TestClient, token: str, project_id: str) -> None:
    response = client.put(
        f"/api/projects/{project_id}/budget",
        headers=_headers(token),
        json={"construction_cost": "1000.00", "target_percent": "120"},
    )
    assert response.status_code == 200
    assert response.json()["target_amount"] == "1200.00"


def _add_dedication(client: TestClient, token: str, project_id: str, name: str, price: str) -> dict[str, str]:
    response = client.post(
        f"/api/projects/{project_id}/dedications",
        headers=_headers(token),
        json={"name": name, "price": price},
    )
    assert response.status_code == 200
    return response.json()


def _budget(client: TestClient, token: str, project_id: str) -> dict[str, str]:
    response = client.get(f"/api/projects/{project_id}/budget", headers=_headers(token))
    assert response.status_code == 200
    return response.json()


def _patch(client: TestClient, token: str, dedication_id: str, body: dict[str, str]):
    return client.patch(f"/api/dedications/{dedication_id}", headers=_headers(token), json=body)


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


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

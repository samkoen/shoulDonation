"""Building-plan HTTP flow against a migrated SQLite file."""

import base64
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
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    database_url = sqlite_url(tmp_path / "plan.db")
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


def test_the_plan_is_stored_in_the_database_and_replaced(client: TestClient) -> None:
    admin = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin, "North")
    project = _create_project(client, admin, synagogue["id"], "Hall")
    missing = client.get(f"/api/projects/{project['id']}/plan", headers=_headers(admin))
    assert missing.status_code == 404
    uploaded = _upload(client, admin, project["id"], PNG)
    assert uploaded.status_code == 204
    stored = client.get(f"/api/projects/{project['id']}/plan", headers=_headers(admin))
    assert stored.status_code == 200
    assert stored.headers["content-type"].startswith("image/png")
    assert stored.content == PNG
    replaced = PNG + b"next"
    assert _upload(client, admin, project["id"], replaced).status_code == 204
    assert client.get(f"/api/projects/{project['id']}/plan", headers=_headers(admin)).content == replaced


def test_a_sub_projector_can_read_the_plan_but_not_replace_it(client: TestClient) -> None:
    admin = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin, "North")
    sub = _create_user(client, admin, "sub@shoul.test", "sub_projector", synagogue["id"])
    project = _create_project(client, admin, synagogue["id"], "Hall")
    _assign(client, admin, project["id"], sub["id"])
    assert _upload(client, admin, project["id"], PNG).status_code == 204
    sub_token = _login(client, "sub@shoul.test", USER_PASSWORD)
    read = client.get(f"/api/projects/{project['id']}/plan", headers=_headers(sub_token))
    assert read.status_code == 200
    assert read.content == PNG
    refused = _upload(client, sub_token, project["id"], PNG)
    assert refused.status_code == 403


def test_painting_a_region_stores_the_brush_strokes(client: TestClient) -> None:
    admin = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin, "North")
    project = _create_project(client, admin, synagogue["id"], "Hall")
    created = client.post(
        f"/api/projects/{project['id']}/dedications",
        headers=_headers(admin),
        json={"name": "Hall", "price": "100.00"},
    )
    dedication_id = created.json()["id"]
    painted = client.put(
        f"/api/dedications/{dedication_id}/region",
        headers=_headers(admin),
        json={"kind": "brush", "width": "3.50", "strokes": [[{"x": "40", "y": "30"}, {"x": "45", "y": "32"}]]},
    )
    assert painted.status_code == 200
    region = painted.json()["plan_region"]
    assert region["kind"] == "brush"
    assert region["width"] == "3.50"
    assert region["strokes"][0][0] == {"x": "40.00", "y": "30.00"}
    assert painted.json()["plan_x"] == "40.00"


def test_another_synagogue_cannot_read_the_plan(client: TestClient) -> None:
    admin = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    north = _create_synagogue(client, admin, "North")
    south = _create_synagogue(client, admin, "South")
    _create_user(client, admin, "lead@shoul.test", "lead_projector", north["id"])
    project = _create_project(client, admin, south["id"], "Other hall")
    _upload(client, admin, project["id"], PNG)
    response = client.get(
        f"/api/projects/{project['id']}/plan",
        headers=_headers(_login(client, "lead@shoul.test", USER_PASSWORD)),
    )
    assert response.status_code == 403


def _upload(client: TestClient, token: str, project_id: str, content: bytes):
    return client.put(
        f"/api/projects/{project_id}/plan",
        headers=_headers(token),
        files={"file": ("plan.png", content, "image/png")},
    )


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

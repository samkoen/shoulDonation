"""Public page HTTP flow: owner settings behind login, visitor routes without any token."""

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
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    database_url = sqlite_url(tmp_path / "public.db")
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


def test_visitors_see_the_enabled_page_without_a_token(client: TestClient) -> None:
    admin = _login(client)
    project = _project(client, admin)
    _add_dedication(client, admin, project["id"])
    _upload_plan(client, admin, project["id"])
    image_id = _upload_gallery(client, admin, project["id"])
    assert client.get("/api/public/hall").status_code == 404
    saved = client.put(
        f"/api/projects/{project['id']}/public-page",
        headers=_headers(admin),
        json={"slug": "hall", "vision": "A home for the community", "enabled": True},
    )
    assert saved.status_code == 200
    view = client.get("/api/public/hall")
    assert view.status_code == 200
    body = view.json()
    assert body["project_name"] == "Hall"
    assert body["synagogue_name"] == "North"
    assert body["has_plan"] is True
    assert body["gallery_image_ids"] == [image_id]
    assert body["dedications"][0] == {
        "id": body["dedications"][0]["id"],
        "name": "Aron",
        "price": "1000.00",
        "status": "open",
        "plan_x": None,
        "plan_y": None,
        "plan_region": None,
    }
    assert client.get("/api/public/hall/plan").content == PNG
    assert client.get(f"/api/public/hall/gallery/{image_id}").content == PNG


def test_the_contact_form_creates_a_customer_lead(client: TestClient) -> None:
    admin = _login(client)
    project = _project(client, admin)
    client.put(
        f"/api/projects/{project['id']}/public-page",
        headers=_headers(admin),
        json={"slug": "hall", "vision": "", "enabled": True},
    )
    sent = client.post(
        "/api/public/hall/contact",
        json={"name": "Moshe", "phone": "0501234567", "synagogue_name": "Beit Yaakov"},
    )
    assert sent.status_code == 204
    leads = client.get("/api/customer-leads", headers=_headers(admin)).json()
    assert [lead["requested_synagogue_name"] for lead in leads] == ["Beit Yaakov"]


def test_settings_require_a_token_and_a_valid_slug(client: TestClient) -> None:
    admin = _login(client)
    project = _project(client, admin)
    assert client.get(f"/api/projects/{project['id']}/public-page").status_code == 401
    assert client.get(f"/api/projects/{project['id']}/public-page", headers=_headers(admin)).status_code == 404
    rejected = client.put(
        f"/api/projects/{project['id']}/public-page",
        headers=_headers(admin),
        json={"slug": "not valid", "vision": "", "enabled": True},
    )
    assert rejected.status_code == 422


def _project(client: TestClient, token: str) -> dict[str, str]:
    synagogue = client.post("/api/synagogues", headers=_headers(token), json={"name": "North"}).json()
    response = client.post(
        "/api/projects",
        headers=_headers(token),
        json={"synagogue_id": synagogue["id"], "name": "Hall"},
    )
    assert response.status_code == 200
    return response.json()


def _add_dedication(client: TestClient, token: str, project_id: str) -> None:
    response = client.post(
        f"/api/projects/{project_id}/dedications",
        headers=_headers(token),
        json={"name": "Aron", "price": "1000"},
    )
    assert response.status_code == 200


def _upload_plan(client: TestClient, token: str, project_id: str) -> None:
    response = client.put(
        f"/api/projects/{project_id}/plan",
        headers=_headers(token),
        files={"file": ("plan.png", PNG, "image/png")},
    )
    assert response.status_code == 204


def _upload_gallery(client: TestClient, token: str, project_id: str) -> str:
    response = client.post(
        f"/api/projects/{project_id}/gallery",
        headers=_headers(token),
        files={"file": ("render.png", PNG, "image/png")},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _login(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

"""Pricing and marker HTTP flow against a migrated SQLite file."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shoul_donation.config import Settings
from shoul_donation.infrastructure.api.app import create_app
from shoul_donation.infrastructure.database import create_engine_from_url, session_factory_for, sqlite_url
from shoul_donation.infrastructure.migrations import upgrade_to_head

ADMIN_EMAIL = "admin@shoul.test"
ADMIN_PASSWORD = "admin-pass-1"


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    database_url = sqlite_url(tmp_path / "pricing.db")
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


def test_preview_then_apply_updates_only_the_chosen_dedications(client: TestClient) -> None:
    token, project = _project(client)
    kept = _add(client, token, project, "Aron", "400.00")
    first = _add(client, token, project, "Bimah", "1.00")
    second = _add(client, token, project, "Door", "1.00")
    body = {"items": [{"dedication_id": first, "weight": "1"}, {"dedication_id": second, "weight": "1"}]}
    preview = client.post(f"/api/projects/{project}/pricing/preview", headers=_headers(token), json=body)
    assert preview.status_code == 200
    assert preview.json()["amount_to_split"] == "800.00"
    assert [item["suggested_price"] for item in preview.json()["items"]] == ["400.00", "400.00"]
    applied = client.post(f"/api/projects/{project}/pricing/apply", headers=_headers(token), json=body)
    assert applied.status_code == 200
    prices = {item["id"]: item["price"] for item in _dedications(client, token, project)}
    assert prices == {kept: "400.00", first: "400.00", second: "400.00"}


def test_a_marker_is_stored_and_removed(client: TestClient) -> None:
    token, project = _project(client)
    dedication = _add(client, token, project, "Aron", "100.00")
    placed = client.put(
        f"/api/dedications/{dedication}/marker",
        headers=_headers(token),
        json={"x": "25.5", "y": "70"},
    )
    assert placed.status_code == 200
    assert (placed.json()["plan_x"], placed.json()["plan_y"]) == ("25.50", "70.00")
    listed = _dedications(client, token, project)[0]
    assert listed["plan_x"] == "25.50"
    assert listed["plan_region"] is None
    removed = client.delete(f"/api/dedications/{dedication}/marker", headers=_headers(token))
    assert removed.status_code == 200
    assert removed.json()["plan_x"] is None
    out_of_range = client.put(
        f"/api/dedications/{dedication}/marker",
        headers=_headers(token),
        json={"x": "120", "y": "10"},
    )
    assert out_of_range.status_code == 422


def _project(client: TestClient) -> tuple[str, str]:
    token = _login(client)
    synagogue = client.post("/api/synagogues", headers=_headers(token), json={"name": "North"}).json()
    project = client.post(
        "/api/projects",
        headers=_headers(token),
        json={"synagogue_id": synagogue["id"], "name": "Hall"},
    ).json()
    budget = client.put(
        f"/api/projects/{project['id']}/budget",
        headers=_headers(token),
        json={"construction_cost": "1200.00", "target_percent": "100"},
    )
    assert budget.status_code == 200
    return token, project["id"]


def _add(client: TestClient, token: str, project_id: str, name: str, price: str) -> str:
    response = client.post(
        f"/api/projects/{project_id}/dedications",
        headers=_headers(token),
        json={"name": name, "price": price},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _dedications(client: TestClient, token: str, project_id: str) -> list[dict[str, str]]:
    response = client.get(f"/api/projects/{project_id}/dedications", headers=_headers(token))
    assert response.status_code == 200
    return response.json()


def _login(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

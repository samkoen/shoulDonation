"""Calculator HTTP flow against a migrated SQLite file."""

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
    database_url = sqlite_url(tmp_path / "calculator.db")
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


def test_sub_projector_issues_a_proposal_without_a_payment_or_a_total(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin_token, "North")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", synagogue["id"])
    sub = _create_user(client, admin_token, "sub@shoul.test", "sub_projector", synagogue["id"])
    lead_token = _login(client, "lead@shoul.test", USER_PASSWORD)
    project = _create_project(client, lead_token, synagogue["id"], "Main hall")
    _assign(client, lead_token, project["id"], sub["id"])
    dedication = _add_dedication(client, lead_token, project["id"])
    sub_token = _login(client, "sub@shoul.test", USER_PASSWORD)
    defaults = client.get(f"/api/projects/{project['id']}/calculator-settings", headers=_headers(sub_token))
    assert defaults.status_code == 200
    assert defaults.json()["max_months"] == 96
    preview = _preview(client, sub_token, project["id"], dedication["id"], "120.00", 36, 10)
    assert preview["financed_total"] is None
    assert preview["monthly_within_range"] is True
    created = _propose(client, sub_token, project["id"], dedication["id"], "120.00", 36, 10)
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "awaiting_rate_table"
    assert body["financed_total"] is None
    assert "payment" not in body
    listed = client.get(f"/api/projects/{project['id']}/proposals", headers=_headers(lead_token))
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["id"]


def test_a_proposal_outside_the_saved_bounds_is_rejected(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin_token, "North")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", synagogue["id"])
    lead_token = _login(client, "lead@shoul.test", USER_PASSWORD)
    project = _create_project(client, lead_token, synagogue["id"], "Main hall")
    dedication = _add_dedication(client, lead_token, project["id"])
    saved = client.put(
        f"/api/projects/{project['id']}/calculator-settings",
        headers=_headers(lead_token),
        json=_bounds(max_months=24),
    )
    assert saved.status_code == 200
    refused = _propose(client, lead_token, project["id"], dedication["id"], "120.00", 36, 10)
    assert refused.status_code == 422


def test_a_saved_proposal_can_be_edited_and_deleted(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    synagogue = _create_synagogue(client, admin_token, "North")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", synagogue["id"])
    lead_token = _login(client, "lead@shoul.test", USER_PASSWORD)
    project = _create_project(client, lead_token, synagogue["id"], "Main hall")
    dedication = _add_dedication(client, lead_token, project["id"])
    created = _propose(client, lead_token, project["id"], dedication["id"], "120.00", 36, 10)
    assert created.status_code == 200
    proposal_id = created.json()["id"]
    updated = client.patch(
        f"/api/proposals/{proposal_id}",
        headers=_headers(lead_token),
        json=_simulation(dedication["id"], "90.00", 24, 11),
    )
    assert updated.status_code == 200
    assert updated.json()["months"] == 24
    deleted = client.delete(f"/api/proposals/{proposal_id}", headers=_headers(lead_token))
    assert deleted.status_code == 204
    listed = client.get(f"/api/projects/{project['id']}/proposals", headers=_headers(lead_token))
    assert listed.json() == []


def test_another_synagogue_cannot_preview(client: TestClient) -> None:
    admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    north = _create_synagogue(client, admin_token, "North")
    south = _create_synagogue(client, admin_token, "South")
    _create_user(client, admin_token, "lead@shoul.test", "lead_projector", north["id"])
    project = _create_project(client, admin_token, south["id"], "Other hall")
    response = client.get(
        f"/api/projects/{project['id']}/calculator-settings",
        headers=_headers(_login(client, "lead@shoul.test", USER_PASSWORD)),
    )
    assert response.status_code == 403


def _bounds(max_months: int) -> dict[str, object]:
    return {
        "min_monthly": "60.00",
        "max_monthly": "200.00",
        "max_months": max_months,
        "min_per_donor": "7000.00",
        "max_per_donor": "150000.00",
        "min_donors": 10,
    }


def _preview(client: TestClient, token: str, project_id: str, dedication_id: str, monthly: str, months: int, donors: int):
    response = client.post(
        f"/api/projects/{project_id}/calculator/preview",
        headers=_headers(token),
        json=_simulation(dedication_id, monthly, months, donors),
    )
    assert response.status_code == 200
    return response.json()


def _propose(client: TestClient, token: str, project_id: str, dedication_id: str, monthly: str, months: int, donors: int):
    return client.post(
        f"/api/projects/{project_id}/proposals",
        headers=_headers(token),
        json=_simulation(dedication_id, monthly, months, donors),
    )


def _simulation(dedication_id: str, monthly: str, months: int, donors: int) -> dict[str, object]:
    return {
        "dedication_id": dedication_id,
        "monthly_amount": monthly,
        "months": months,
        "donor_count": donors,
    }


def _add_dedication(client: TestClient, token: str, project_id: str) -> dict[str, str]:
    response = client.post(
        f"/api/projects/{project_id}/dedications",
        headers=_headers(token),
        json={"name": "Aron", "price": "700000.00"},
    )
    assert response.status_code == 200
    return response.json()


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

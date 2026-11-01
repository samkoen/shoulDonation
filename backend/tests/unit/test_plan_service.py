"""Building-plan rules on an in-memory store."""

import base64
from uuid import uuid4

import pytest

from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.plan_service import PlanService
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
PASSWORD = "user-pass-1"


def test_the_lead_stores_a_plan_the_sub_projector_can_read() -> None:
    store, lead, sub, project = _project_with_team()
    plans = PlanService(store)
    saved = plans.replace_plan(lead, project.id, "image/png", PNG)
    assert saved.content_type == "image/png"
    assert plans.get_plan(sub, project.id).content == PNG


def test_replacing_the_plan_keeps_one_image() -> None:
    store, lead, _, project = _project_with_team()
    plans = PlanService(store)
    plans.replace_plan(lead, project.id, "image/png", PNG)
    plans.replace_plan(lead, project.id, "image/png", PNG + b"next")
    assert plans.get_plan(lead, project.id).content == PNG + b"next"
    assert len(store.plans_by_project) == 1


def test_a_sub_projector_cannot_replace_the_plan() -> None:
    store, _, sub, project = _project_with_team()
    with pytest.raises(ForbiddenError):
        PlanService(store).replace_plan(sub, project.id, "image/png", PNG)


def test_a_file_that_is_not_an_image_is_rejected() -> None:
    store, lead, _, project = _project_with_team()
    with pytest.raises(ValidationError):
        PlanService(store).replace_plan(lead, project.id, "image/jpeg", PNG)


def test_a_missing_plan_is_not_found() -> None:
    store, lead, _, project = _project_with_team()
    with pytest.raises(NotFoundError):
        PlanService(store).get_plan(lead, project.id)


def _project_with_team():
    store = MemoryUnitOfWork()
    identity = IdentityService(store, PasswordHasher(1_000))
    projects = ProjectService(store)
    admin = Actor(user_id=uuid4(), role=Role.PLATFORM_ADMIN, synagogue_id=None)
    synagogue = identity.create_synagogue(admin, "North")
    lead_user = identity.register_user(admin, "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    sub_user = identity.register_user(admin, "sub@shoul.test", PASSWORD, Role.SUB_PROJECTOR, synagogue.id)
    lead = Actor(user_id=lead_user.id, role=Role.LEAD_PROJECTOR, synagogue_id=synagogue.id)
    project = projects.create_project(lead, synagogue.id, "Main hall")
    projects.assign_sub_projector(lead, project.id, sub_user.id)
    sub = Actor(user_id=sub_user.id, role=Role.SUB_PROJECTOR, synagogue_id=synagogue.id)
    return store, lead, sub, project

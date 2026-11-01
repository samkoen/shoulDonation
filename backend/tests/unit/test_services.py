"""Identity and project rules on an in-memory store."""

from uuid import uuid4

import pytest

from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import AuthenticationError, ConflictError, ForbiddenError
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def _admin() -> Actor:
    return Actor(user_id=uuid4(), role=Role.PLATFORM_ADMIN, synagogue_id=None)


def _services() -> tuple[MemoryUnitOfWork, IdentityService, ProjectService]:
    store = MemoryUnitOfWork()
    identity = IdentityService(store, PasswordHasher(1_000))
    return store, identity, ProjectService(store)


def test_unknown_password_is_rejected() -> None:
    _, identity, _ = _services()
    synagogue = identity.create_synagogue(_admin(), "North")
    identity.register_user(_admin(), "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    with pytest.raises(AuthenticationError):
        identity.authenticate("lead@shoul.test", "wrong-pass-1")


def test_duplicate_email_is_rejected() -> None:
    _, identity, _ = _services()
    synagogue = identity.create_synagogue(_admin(), "North")
    identity.register_user(_admin(), "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    with pytest.raises(ConflictError):
        identity.register_user(_admin(), "lead@shoul.test", PASSWORD, Role.SUB_PROJECTOR, synagogue.id)


def test_sub_projector_sees_only_assigned_projects() -> None:
    _, identity, projects = _services()
    admin = _admin()
    synagogue = identity.create_synagogue(admin, "North")
    lead = identity.register_user(admin, "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    sub = identity.register_user(admin, "sub@shoul.test", PASSWORD, Role.SUB_PROJECTOR, synagogue.id)
    lead_actor = Actor(user_id=lead.id, role=Role.LEAD_PROJECTOR, synagogue_id=synagogue.id)
    assigned = projects.create_project(lead_actor, synagogue.id, "Main hall")
    projects.create_project(admin, synagogue.id, "Office")
    projects.assign_sub_projector(lead_actor, assigned.id, sub.id)
    visible = projects.list_projects(Actor(user_id=sub.id, role=Role.SUB_PROJECTOR, synagogue_id=synagogue.id))
    assert [item.name for item in visible] == ["Main hall"]


def test_lead_projector_cannot_open_a_project_in_another_synagogue() -> None:
    _, identity, projects = _services()
    admin = _admin()
    home = identity.create_synagogue(admin, "North")
    other = identity.create_synagogue(admin, "South")
    lead = identity.register_user(admin, "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, home.id)
    lead_actor = Actor(user_id=lead.id, role=Role.LEAD_PROJECTOR, synagogue_id=home.id)
    with pytest.raises(ForbiddenError):
        projects.create_project(lead_actor, other.id, "Other hall")

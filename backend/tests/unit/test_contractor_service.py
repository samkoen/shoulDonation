"""Contractor rules on an in-memory store."""

from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.contractor_service import ContractorService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.errors import ForbiddenError, ValidationError
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def test_a_realized_dedication_can_keep_a_contractor() -> None:
    store, lead, _, dedication = _realized_dedication()
    saved = ContractorService(store).save(lead, dedication.id, "Amos", "0501112233", Decimal("180000.00"))
    assert saved.name == "Amos"
    assert ContractorService(store).get(lead, dedication.id).amount == Decimal("180000.00")


def test_an_open_dedication_cannot_have_a_contractor() -> None:
    store, _, lead, _, project = _project_with_team()
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("100.00"))
    with pytest.raises(ValidationError):
        ContractorService(store).save(lead, dedication.id, "Amos", "0501112233", Decimal("100.00"))


def test_a_sub_projector_cannot_attach_a_contractor() -> None:
    store, _, sub, dedication = _realized_dedication()
    with pytest.raises(ForbiddenError):
        ContractorService(store).save(sub, dedication.id, "Amos", "0501112233", Decimal("100.00"))


def _realized_dedication():
    store, _, lead, sub, project = _project_with_team()
    budget = BudgetService(store)
    dedication = budget.add_dedication(lead, project.id, "Aron", Decimal("100.00"))
    updated = budget.update_dedication(lead, dedication.id, None, DedicationStatus.REALIZED)
    return store, lead, sub, updated


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
    return store, admin, lead, sub, project

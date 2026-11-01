"""Budget rules on an in-memory store."""

from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.errors import ConflictError, ForbiddenError
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def test_gap_follows_the_prices_set_by_the_lead_projector() -> None:
    store, admin, lead, sub, project = _project_with_team()
    budget = BudgetService(store)
    summary = budget.set_budget(lead, project.id, Decimal("1000.00"), Decimal("120"))
    first = budget.add_dedication(lead, project.id, "Aron", Decimal("700.00"))
    budget.add_dedication(lead, project.id, "Bimah", Decimal("300.00"))
    summary = budget.get_summary(admin, project.id)
    budget.update_dedication(sub, first.id, None, DedicationStatus.FUNDRAISING)
    assert summary.target_amount == Decimal("1200.00")
    assert summary.gap == Decimal("200.00")
    assert budget.list_dedications(sub, project.id)[0].status is DedicationStatus.FUNDRAISING


def test_sub_projector_cannot_set_a_price() -> None:
    store, _, _, sub, project = _project_with_team()
    budget = BudgetService(store)
    with pytest.raises(ForbiddenError):
        budget.add_dedication(sub, project.id, "Aron", Decimal("100.00"))


def test_duplicate_dedication_name_is_rejected() -> None:
    store, _, lead, _, project = _project_with_team()
    budget = BudgetService(store)
    budget.add_dedication(lead, project.id, "Aron", Decimal("100.00"))
    with pytest.raises(ConflictError):
        budget.add_dedication(lead, project.id, "Aron", Decimal("200.00"))


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

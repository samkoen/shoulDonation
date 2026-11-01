"""Calculator bounds and proposals on an in-memory store."""

from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.calculator_service import CalculatorService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.calculator import SettingsBounds, SimulationDraft
from shoul_donation.domain.errors import ForbiddenError, ValidationError
from shoul_donation.domain.proposal_status import ProposalStatus
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def test_a_new_project_uses_the_default_bounds() -> None:
    store, _, _, _, project = _project_with_team()
    settings = CalculatorService(store).get_settings(_lead(store), project.id)
    assert settings.min_monthly == Decimal("60.00")
    assert settings.max_monthly == Decimal("200.00")
    assert settings.max_months == 96
    assert settings.min_per_donor == Decimal("7000.00")
    assert settings.max_per_donor == Decimal("150000.00")
    assert settings.min_donors == 10


def test_sub_projector_cannot_change_the_bounds() -> None:
    store, _, _, sub, project = _project_with_team()
    with pytest.raises(ForbiddenError):
        CalculatorService(store).save_settings(sub, project.id, _bounds())


def test_preview_stays_inside_the_defaults_without_a_financed_total() -> None:
    store, _, lead, sub, project = _project_with_team()
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("700000.00"))
    view = CalculatorService(store).preview(sub, project.id, _draft(dedication.id, "120.00", 36, 10))
    assert view.monthly_within_range is True
    assert view.term_within_limit is True
    assert view.donors_meet_minimum is True
    assert view.financed_total is None
    assert view.status is ProposalStatus.AWAITING_RATE_TABLE


def test_a_proposal_is_refused_when_a_bound_fails() -> None:
    store, _, lead, sub, project = _project_with_team()
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("700000.00"))
    calculator = CalculatorService(store)
    view = calculator.preview(sub, project.id, _draft(dedication.id, "50.00", 36, 9))
    assert view.monthly_within_range is False
    assert view.donors_meet_minimum is False
    with pytest.raises(ValidationError):
        calculator.create_proposal(sub, project.id, _draft(dedication.id, "50.00", 36, 9))


def test_an_accepted_preview_becomes_a_proposal_without_a_total() -> None:
    store, _, lead, sub, project = _project_with_team()
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("700000.00"))
    calculator = CalculatorService(store)
    draft = _draft(dedication.id, "120.00", 24, 10)
    proposal = calculator.create_proposal(sub, project.id, draft)
    assert proposal.financed_total is None
    assert proposal.status is ProposalStatus.AWAITING_RATE_TABLE
    assert calculator.list_proposals(lead, project.id)[0].id == proposal.id


def test_a_proposal_can_be_revised_and_removed() -> None:
    store, _, lead, sub, project = _project_with_team()
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("700000.00"))
    calculator = CalculatorService(store)
    proposal = calculator.create_proposal(sub, project.id, _draft(dedication.id, "120.00", 24, 10))
    revised = calculator.update_proposal(sub, proposal.id, _draft(dedication.id, "80.00", 48, 12))
    assert revised.id == proposal.id
    assert revised.monthly_amount == Decimal("80.00")
    assert revised.donor_count == 12
    with pytest.raises(ValidationError):
        calculator.update_proposal(sub, proposal.id, _draft(dedication.id, "10.00", 24, 10))
    calculator.delete_proposal(lead, proposal.id)
    assert calculator.list_proposals(lead, project.id) == []


def _bounds() -> SettingsBounds:
    return SettingsBounds(
        min_monthly=Decimal("60.00"),
        max_monthly=Decimal("200.00"),
        max_months=48,
        min_per_donor=Decimal("7000.00"),
        max_per_donor=Decimal("150000.00"),
        min_donors=10,
    )


def _draft(dedication_id, monthly: str, months: int, donors: int) -> SimulationDraft:
    return SimulationDraft(dedication_id, Decimal(monthly), months, donors)


def _lead(store: MemoryUnitOfWork) -> Actor:
    synagogue_id = next(iter(store.synagogues_by_id))
    user = store.users_by_email["lead@shoul.test"]
    return Actor(user_id=user.id, role=Role.LEAD_PROJECTOR, synagogue_id=synagogue_id)


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

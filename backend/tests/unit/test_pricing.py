"""Price suggestion and plan marker rules."""

from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.pricing_service import PricingService
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.plan_marker import require_marker
from shoul_donation.domain.pricing import PriceWeight, split_by_weight
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def test_split_keeps_every_cent() -> None:
    ids = [uuid4(), uuid4(), uuid4()]
    weights = [PriceWeight(ids[0], Decimal(1)), PriceWeight(ids[1], Decimal(1)), PriceWeight(ids[2], Decimal(1))]
    shares = split_by_weight(Decimal("100.00"), weights)
    assert sum(shares.values()) == Decimal("100.00")
    assert sorted(shares.values()) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_preview_splits_the_remaining_target_without_writing() -> None:
    store, lead, _, project = _project_with_team()
    budget = BudgetService(store)
    budget.set_budget(lead, project.id, Decimal("1000.00"), Decimal("100"))
    kept = budget.add_dedication(lead, project.id, "Aron", Decimal("400.00"))
    first = budget.add_dedication(lead, project.id, "Bimah", Decimal("1.00"))
    second = budget.add_dedication(lead, project.id, "Door", Decimal("1.00"))
    preview = PricingService(store).preview(
        lead, project.id, [PriceWeight(first.id, Decimal(2)), PriceWeight(second.id, Decimal(1))]
    )
    assert preview.amount_to_split == Decimal("600.00")
    assert [item.suggested_price for item in preview.items] == [Decimal("400.00"), Decimal("200.00")]
    assert store.dedications_by_id[first.id].price == Decimal("1.00")
    assert store.dedications_by_id[kept.id].price == Decimal("400.00")


def test_apply_writes_the_suggested_prices() -> None:
    store, lead, _, project = _project_with_team()
    budget = BudgetService(store)
    budget.set_budget(lead, project.id, Decimal("900.00"), Decimal("100"))
    first = budget.add_dedication(lead, project.id, "Bimah", Decimal("1.00"))
    second = budget.add_dedication(lead, project.id, "Door", Decimal("1.00"))
    PricingService(store).apply(lead, project.id, [PriceWeight(first.id, Decimal(1)), PriceWeight(second.id, Decimal(2))])
    assert store.dedications_by_id[first.id].price == Decimal("300.00")
    assert store.dedications_by_id[second.id].price == Decimal("600.00")


def test_pricing_refuses_sub_projectors_and_missing_budget() -> None:
    store, lead, sub, project = _project_with_team()
    first = BudgetService(store).add_dedication(lead, project.id, "Bimah", Decimal("1.00"))
    pricing = PricingService(store)
    with pytest.raises(ForbiddenError):
        pricing.preview(sub, project.id, [PriceWeight(first.id, Decimal(1))])
    with pytest.raises(NotFoundError):
        pricing.preview(lead, project.id, [PriceWeight(first.id, Decimal(1))])


def test_weights_must_be_positive_and_belong_to_the_project() -> None:
    store, lead, _, project = _project_with_team()
    budget = BudgetService(store)
    budget.set_budget(lead, project.id, Decimal("100.00"), Decimal("100"))
    first = budget.add_dedication(lead, project.id, "Bimah", Decimal("1.00"))
    pricing = PricingService(store)
    with pytest.raises(ValidationError):
        pricing.preview(lead, project.id, [PriceWeight(first.id, Decimal(0))])
    with pytest.raises(NotFoundError):
        pricing.preview(lead, project.id, [PriceWeight(uuid4(), Decimal(1))])


def test_the_owner_places_and_removes_a_marker() -> None:
    store, lead, sub, project = _project_with_team()
    budget = BudgetService(store)
    dedication = budget.add_dedication(lead, project.id, "Aron", Decimal("100.00"))
    placed = budget.set_marker(lead, dedication.id, require_marker(Decimal("12.346"), Decimal("80")))
    assert placed.marker is not None
    assert (placed.marker.x, placed.marker.y) == (Decimal("12.35"), Decimal("80.00"))
    assert budget.set_marker(lead, dedication.id, None).marker is None
    with pytest.raises(ForbiddenError):
        budget.set_marker(sub, dedication.id, require_marker(Decimal(1), Decimal(1)))
    with pytest.raises(ValidationError):
        require_marker(Decimal(101), Decimal(1))


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

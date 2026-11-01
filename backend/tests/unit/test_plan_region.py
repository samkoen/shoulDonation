"""Manual brush strokes on the building plan."""

from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import ValidationError
from shoul_donation.domain.plan_marker import require_marker
from shoul_donation.domain.plan_region import require_brush
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"


def test_a_brush_needs_at_least_one_stroke() -> None:
    with pytest.raises(ValidationError, match="one stroke"):
        require_brush([], Decimal("3.50"))


def test_brush_width_is_bounded() -> None:
    stroke = [(Decimal("10"), Decimal("10")), (Decimal("20"), Decimal("12"))]
    with pytest.raises(ValidationError, match="Brush width"):
        require_brush([stroke], Decimal("20"))


def test_painting_stores_the_strokes_and_an_anchor() -> None:
    store, lead, project = _project_with_team()
    budget = BudgetService(store)
    dedication = budget.add_dedication(lead, project.id, "Hall", Decimal("100.00"))
    region = require_brush([[(Decimal("40"), Decimal("30")), (Decimal("42"), Decimal("33"))]], Decimal("3.50"))
    painted = budget.set_region(lead, dedication.id, region)
    assert painted.region is not None
    assert painted.region.kind == "brush"
    assert len(painted.region.strokes[0]) == 2
    assert painted.marker is not None
    assert (painted.marker.x, painted.marker.y) == (Decimal("40.00"), Decimal("30.00"))
    assert budget.set_marker(lead, dedication.id, None).region is None


def test_a_marker_alone_does_not_invent_a_region() -> None:
    store, lead, project = _project_with_team()
    budget = BudgetService(store)
    dedication = budget.add_dedication(lead, project.id, "Aron", Decimal("100.00"))
    placed = budget.set_marker(lead, dedication.id, require_marker(Decimal("12.34"), Decimal("80")))
    assert placed.marker is not None
    assert placed.region is None


def _project_with_team():
    store = MemoryUnitOfWork()
    identity = IdentityService(store, PasswordHasher(1_000))
    projects = ProjectService(store)
    admin = Actor(user_id=uuid4(), role=Role.PLATFORM_ADMIN, synagogue_id=None)
    synagogue = identity.create_synagogue(admin, "North")
    lead_user = identity.register_user(admin, "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    lead = Actor(user_id=lead_user.id, role=Role.LEAD_PROJECTOR, synagogue_id=synagogue.id)
    project = projects.create_project(lead, synagogue.id, "Main hall")
    return store, lead, project

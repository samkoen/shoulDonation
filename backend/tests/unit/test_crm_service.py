"""CRM rules on an in-memory store."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.crm_service import CrmService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.lead_status import LeadStatus
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PASSWORD = "user-pass-1"
WHEN = datetime(2026, 11, 2, 18, 0, tzinfo=UTC)


def test_a_sub_projector_sees_only_assigned_donor_leads() -> None:
    store, _, lead, sub, project = _project_with_team()
    crm = CrmService(store)
    hidden = crm.add_donor_lead(lead, project.id, "David", "0501234567", None, None)
    visible = crm.add_donor_lead(sub, project.id, "Sarah", "0507654321", None, None)
    assert visible.assignee_id == sub.user_id
    assert [item.id for item in crm.list_donor_leads(sub, project.id)] == [visible.id]
    assert hidden.id in {item.id for item in crm.list_donor_leads(lead, project.id)}
    with pytest.raises(ForbiddenError):
        crm.add_meeting(sub, hidden.id, WHEN, "first call")


def test_assigning_a_lead_lets_the_sub_projector_close_it() -> None:
    store, _, lead, sub, project = _project_with_team()
    crm = CrmService(store)
    created = crm.add_donor_lead(lead, project.id, "David", "0501234567", None, sub.user_id)
    meeting = crm.add_meeting(sub, created.id, WHEN, "at the synagogue", Decimal("70"))
    closed = crm.update_lead(sub, created.id, LeadStatus.WON, None)
    assert closed.status is LeadStatus.WON
    stored = crm.list_meetings(lead, created.id)[0]
    assert stored.id == meeting.id
    assert stored.close_chance == Decimal("70")


def test_an_assignee_must_already_be_on_the_project() -> None:
    store, admin, lead, _, project = _project_with_team()
    outsider = IdentityService(store, PasswordHasher(1_000)).register_user(
        admin, "other@shoul.test", PASSWORD, Role.SUB_PROJECTOR, project.synagogue_id
    )
    with pytest.raises(ValidationError):
        CrmService(store).add_donor_lead(lead, project.id, "David", "0501234567", None, outsider.id)


def test_customer_leads_stay_out_of_the_project_pipeline() -> None:
    store, admin, lead, _, project = _project_with_team()
    crm = CrmService(store)
    customer = crm.add_customer_lead(admin, "Yael", "0521112233", "Beit El")
    assert customer.kind is LeadKind.SYNAGOGUE_CUSTOMER
    assert customer.project_id is None
    assert crm.list_donor_leads(lead, project.id) == []
    with pytest.raises(ForbiddenError):
        crm.list_customer_leads(lead)
    with pytest.raises(ValidationError):
        crm.update_lead(admin, customer.id, None, lead.user_id)


def test_a_dedication_from_another_project_is_rejected() -> None:
    store, admin, lead, _, project = _project_with_team()
    other = ProjectService(store).create_project(admin, project.synagogue_id, "Side hall")
    dedication = BudgetService(store).add_dedication(lead, other.id, "Aron", Decimal("100.00"))
    with pytest.raises(NotFoundError):
        CrmService(store).add_donor_lead(lead, project.id, "David", "0501234567", dedication.id, None)


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

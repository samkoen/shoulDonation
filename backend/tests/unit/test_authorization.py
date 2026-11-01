"""Authorization rules, without a database."""

from uuid import uuid4

import pytest

from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import (
    assert_assignee_is_sub_projector,
    assert_can_assign,
    assert_can_create_project,
    assert_can_register_user,
    assert_platform_admin,
)
from shoul_donation.domain.entities import Membership
from shoul_donation.domain.errors import ForbiddenError, ValidationError
from shoul_donation.domain.role import Role


def _actor(role: Role, synagogue_id=None) -> Actor:
    return Actor(user_id=uuid4(), role=role, synagogue_id=synagogue_id)


def test_only_platform_admin_opens_a_synagogue() -> None:
    assert_platform_admin(_actor(Role.PLATFORM_ADMIN))
    with pytest.raises(ForbiddenError):
        assert_platform_admin(_actor(Role.LEAD_PROJECTOR, uuid4()))


def test_lead_projector_creates_only_a_sub_projector_in_the_same_synagogue() -> None:
    synagogue_id = uuid4()
    lead = _actor(Role.LEAD_PROJECTOR, synagogue_id)
    assert_can_register_user(lead, Role.SUB_PROJECTOR, synagogue_id)
    with pytest.raises(ForbiddenError):
        assert_can_register_user(lead, Role.LEAD_PROJECTOR, synagogue_id)
    with pytest.raises(ForbiddenError):
        assert_can_register_user(lead, Role.SUB_PROJECTOR, uuid4())


def test_platform_admin_is_not_attached_to_a_synagogue() -> None:
    admin = _actor(Role.PLATFORM_ADMIN)
    with pytest.raises(ValidationError):
        assert_can_register_user(admin, Role.PLATFORM_ADMIN, uuid4())


def test_sub_projector_cannot_create_a_project() -> None:
    synagogue_id = uuid4()
    with pytest.raises(ForbiddenError):
        assert_can_create_project(_actor(Role.SUB_PROJECTOR, synagogue_id), synagogue_id)


def test_assignee_must_be_a_sub_projector_of_the_project_synagogue() -> None:
    synagogue_id = uuid4()
    lead = _actor(Role.LEAD_PROJECTOR, synagogue_id)
    assert_can_assign(lead, synagogue_id)
    membership = Membership(id=uuid4(), user_id=uuid4(), synagogue_id=uuid4(), role=Role.SUB_PROJECTOR)
    with pytest.raises(ValidationError):
        assert_assignee_is_sub_projector(membership, synagogue_id)

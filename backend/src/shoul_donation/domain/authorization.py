"""Permission checks. Each function decides one action and raises when it is refused."""

from uuid import UUID

from shoul_donation.domain.actor import Actor
from shoul_donation.domain.entities import Membership
from shoul_donation.domain.errors import ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.role import Role


def assert_platform_admin(actor: Actor) -> None:
    if actor.role is not Role.PLATFORM_ADMIN:
        raise ForbiddenError("Only a platform admin can perform this action")


def assert_can_register_user(actor: Actor, role: Role, synagogue_id: UUID | None) -> None:
    if role is Role.PLATFORM_ADMIN:
        _assert_platform_admin_creation(actor, synagogue_id)
        return
    _assert_synagogue_role_creation(actor, role, synagogue_id)


def assert_can_create_project(actor: Actor, synagogue_id: UUID) -> None:
    if actor.role is Role.PLATFORM_ADMIN:
        return
    if actor.role is Role.LEAD_PROJECTOR and actor.synagogue_id == synagogue_id:
        return
    raise ForbiddenError("You cannot create a project for this synagogue")


def assert_can_assign(actor: Actor, synagogue_id: UUID) -> None:
    if actor.role is Role.PLATFORM_ADMIN:
        return
    if actor.role is Role.LEAD_PROJECTOR and actor.synagogue_id == synagogue_id:
        return
    raise ForbiddenError("You cannot assign a sub-projector on this project")


def assert_assignee_is_sub_projector(membership: Membership | None, synagogue_id: UUID) -> None:
    if membership is None:
        raise NotFoundError("User was not found")
    if membership.role is not Role.SUB_PROJECTOR or membership.synagogue_id != synagogue_id:
        raise ValidationError("The assignee must be a sub-projector of this synagogue")


def _assert_platform_admin_creation(actor: Actor, synagogue_id: UUID | None) -> None:
    assert_platform_admin(actor)
    if synagogue_id is not None:
        raise ValidationError("A platform admin is not attached to a synagogue")


def _assert_synagogue_role_creation(
    actor: Actor,
    role: Role,
    synagogue_id: UUID | None,
) -> None:
    if synagogue_id is None:
        raise ValidationError("This role requires a synagogue")
    if actor.role is Role.PLATFORM_ADMIN:
        return
    if _lead_creates_sub_projector(actor, role, synagogue_id):
        return
    raise ForbiddenError("You cannot create this user")


def assert_can_view_project(actor: Actor, synagogue_id: UUID, is_assigned: bool) -> None:
    if actor.role is Role.PLATFORM_ADMIN:
        return
    if actor.role is Role.LEAD_PROJECTOR and actor.synagogue_id == synagogue_id:
        return
    if actor.role is Role.SUB_PROJECTOR and is_assigned:
        return
    raise ForbiddenError("You cannot view this project")


def assert_can_set_project_prices(actor: Actor, synagogue_id: UUID) -> None:
    if actor.role is Role.PLATFORM_ADMIN:
        return
    if actor.role is Role.LEAD_PROJECTOR and actor.synagogue_id == synagogue_id:
        return
    raise ForbiddenError("Only the project owner can set this price")


def _lead_creates_sub_projector(actor: Actor, role: Role, synagogue_id: UUID) -> bool:
    return (
        actor.role is Role.LEAD_PROJECTOR
        and role is Role.SUB_PROJECTOR
        and actor.synagogue_id == synagogue_id
    )

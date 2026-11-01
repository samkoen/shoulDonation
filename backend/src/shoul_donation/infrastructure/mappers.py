"""Row to domain conversions."""

from uuid import UUID

from shoul_donation.domain.entities import Membership, Project, ProjectAssignment, Synagogue, UserAccount
from shoul_donation.domain.role import Role
from shoul_donation.infrastructure.orm import AssignmentRow, MembershipRow, ProjectRow, SynagogueRow, UserRow


def synagogue_from_row(row: SynagogueRow) -> Synagogue:
    return Synagogue(id=UUID(row.id), name=row.name)


def user_from_row(row: UserRow) -> UserAccount:
    return UserAccount(id=UUID(row.id), email=row.email, password_hash=row.password_hash)


def membership_from_row(row: MembershipRow) -> Membership:
    synagogue_id = None if row.synagogue_id is None else UUID(row.synagogue_id)
    return Membership(
        id=UUID(row.id),
        user_id=UUID(row.user_id),
        synagogue_id=synagogue_id,
        role=Role(row.role),
    )


def project_from_row(row: ProjectRow) -> Project:
    return Project(id=UUID(row.id), synagogue_id=UUID(row.synagogue_id), name=row.name)


def assignment_from_row(row: AssignmentRow) -> ProjectAssignment:
    return ProjectAssignment(
        id=UUID(row.id),
        synagogue_id=UUID(row.synagogue_id),
        project_id=UUID(row.project_id),
        user_id=UUID(row.user_id),
    )

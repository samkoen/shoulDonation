"""SQLAlchemy repositories. They translate rows and hide the session from the services."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.entities import Membership, Project, ProjectAssignment, Synagogue, UserAccount
from shoul_donation.domain.role import Role
from shoul_donation.infrastructure.mappers import (
    membership_from_row,
    project_from_row,
    synagogue_from_row,
    user_from_row,
)
from shoul_donation.infrastructure.orm import AssignmentRow, MembershipRow, ProjectRow, SynagogueRow, UserRow


class SqlAlchemySynagogueRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, synagogue: Synagogue) -> None:
        self._session.add(SynagogueRow(id=str(synagogue.id), name=synagogue.name))

    def get(self, synagogue_id: UUID) -> Synagogue | None:
        row = self._session.get(SynagogueRow, str(synagogue_id))
        return None if row is None else synagogue_from_row(row)

    def get_by_name(self, name: str) -> Synagogue | None:
        row = self._session.scalar(select(SynagogueRow).where(SynagogueRow.name == name))
        return None if row is None else synagogue_from_row(row)

    def list_all(self) -> list[Synagogue]:
        rows = self._session.scalars(select(SynagogueRow).order_by(SynagogueRow.name))
        return [synagogue_from_row(row) for row in rows]


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: UserAccount) -> None:
        self._session.add(UserRow(id=str(user.id), email=user.email, password_hash=user.password_hash))

    def get(self, user_id: UUID) -> UserAccount | None:
        row = self._session.get(UserRow, str(user_id))
        return None if row is None else user_from_row(row)

    def get_by_email(self, email: str) -> UserAccount | None:
        row = self._session.scalar(select(UserRow).where(UserRow.email == email))
        return None if row is None else user_from_row(row)


class SqlAlchemyMembershipRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, membership: Membership) -> None:
        self._session.add(self._row(membership))

    def get_for_user(self, user_id: UUID) -> Membership | None:
        statement = select(MembershipRow).where(MembershipRow.user_id == str(user_id))
        row = self._session.scalar(statement)
        return None if row is None else membership_from_row(row)

    def _row(self, membership: Membership) -> MembershipRow:
        synagogue_id = None if membership.synagogue_id is None else str(membership.synagogue_id)
        return MembershipRow(
            id=str(membership.id),
            user_id=str(membership.user_id),
            synagogue_id=synagogue_id,
            role=membership.role.value if isinstance(membership.role, Role) else membership.role,
        )


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        self._session.add(
            ProjectRow(id=str(project.id), synagogue_id=str(project.synagogue_id), name=project.name)
        )

    def get(self, project_id: UUID) -> Project | None:
        row = self._session.get(ProjectRow, str(project_id))
        return None if row is None else project_from_row(row)

    def get_by_name(self, synagogue_id: UUID, name: str) -> Project | None:
        statement = select(ProjectRow).where(
            ProjectRow.synagogue_id == str(synagogue_id),
            ProjectRow.name == name,
        )
        row = self._session.scalar(statement)
        return None if row is None else project_from_row(row)

    def list_all(self) -> list[Project]:
        rows = self._session.scalars(select(ProjectRow).order_by(ProjectRow.name))
        return [project_from_row(row) for row in rows]

    def list_for_synagogue(self, synagogue_id: UUID) -> list[Project]:
        statement = select(ProjectRow).where(ProjectRow.synagogue_id == str(synagogue_id)).order_by(ProjectRow.name)
        return [project_from_row(row) for row in self._session.scalars(statement)]

    def list_assigned_to(self, user_id: UUID) -> list[Project]:
        statement = (
            select(ProjectRow)
            .join(AssignmentRow, AssignmentRow.project_id == ProjectRow.id)
            .where(AssignmentRow.user_id == str(user_id))
            .order_by(ProjectRow.name)
        )
        return [project_from_row(row) for row in self._session.scalars(statement)]


class SqlAlchemyAssignmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, assignment: ProjectAssignment) -> None:
        self._session.add(
            AssignmentRow(
                id=str(assignment.id),
                synagogue_id=str(assignment.synagogue_id),
                project_id=str(assignment.project_id),
                user_id=str(assignment.user_id),
            )
        )

    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        statement = select(AssignmentRow.id).where(
            AssignmentRow.project_id == str(project_id),
            AssignmentRow.user_id == str(user_id),
        )
        return self._session.scalar(statement) is not None

    def list_for_project(self, project_id: UUID) -> list[ProjectAssignment]:
        statement = select(AssignmentRow).where(AssignmentRow.project_id == str(project_id))
        return [self._assignment(row) for row in self._session.scalars(statement)]

    def _assignment(self, row: AssignmentRow) -> ProjectAssignment:
        return ProjectAssignment(
            id=UUID(row.id),
            synagogue_id=UUID(row.synagogue_id),
            project_id=UUID(row.project_id),
            user_id=UUID(row.user_id),
        )

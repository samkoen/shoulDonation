"""Projects and the assignment of a sub-projector to one project."""

from uuid import UUID, uuid4

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import (
    assert_assignee_is_sub_projector,
    assert_can_assign,
    assert_can_create_project,
    assert_can_view_project,
)
from shoul_donation.domain.entities import Project, ProjectAssignment, ProjectMember
from shoul_donation.domain.errors import ConflictError, ForbiddenError, NotFoundError
from shoul_donation.domain.role import Role
from shoul_donation.domain.validation import require_name


class ProjectService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def create_project(self, actor: Actor, synagogue_id: UUID, name: str) -> Project:
        assert_can_create_project(actor, synagogue_id)
        self._require_synagogue(synagogue_id)
        cleaned = require_name(name, "Project name")
        self._reject_duplicate_name(synagogue_id, cleaned)
        project = Project(id=uuid4(), synagogue_id=synagogue_id, name=cleaned)
        self._unit_of_work.projects.add(project)
        self._unit_of_work.commit()
        return project

    def list_projects(self, actor: Actor) -> list[Project]:
        if actor.role is Role.PLATFORM_ADMIN:
            return self._unit_of_work.projects.list_all()
        if actor.role is Role.LEAD_PROJECTOR:
            return self._list_for_lead(actor)
        return self._unit_of_work.projects.list_assigned_to(actor.user_id)

    def list_project_members(self, actor: Actor, project_id: UUID) -> list[ProjectMember]:
        project = self._require_project(project_id)
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return self._members(project_id)

    def assign_sub_projector(self, actor: Actor, project_id: UUID, user_id: UUID) -> ProjectAssignment:
        project = self._require_project(project_id)
        assert_can_assign(actor, project.synagogue_id)
        membership = self._unit_of_work.memberships.get_for_user(user_id)
        assert_assignee_is_sub_projector(membership, project.synagogue_id)
        self._reject_existing_assignment(project_id, user_id)
        return self._store_assignment(project, user_id)

    def _members(self, project_id: UUID) -> list[ProjectMember]:
        members: list[ProjectMember] = []
        for assignment in self._unit_of_work.assignments.list_for_project(project_id):
            user = self._unit_of_work.users.get(assignment.user_id)
            if user is not None:
                members.append(ProjectMember(user_id=user.id, email=user.email))
        return sorted(members, key=lambda item: item.email)

    def _list_for_lead(self, actor: Actor) -> list[Project]:
        if actor.synagogue_id is None:
            raise ForbiddenError("A lead projector must belong to a synagogue")
        return self._unit_of_work.projects.list_for_synagogue(actor.synagogue_id)

    def _store_assignment(self, project: Project, user_id: UUID) -> ProjectAssignment:
        assignment = ProjectAssignment(
            id=uuid4(),
            synagogue_id=project.synagogue_id,
            project_id=project.id,
            user_id=user_id,
        )
        self._unit_of_work.assignments.add(assignment)
        self._unit_of_work.commit()
        return assignment

    def _require_synagogue(self, synagogue_id: UUID) -> None:
        if self._unit_of_work.synagogues.get(synagogue_id) is None:
            raise NotFoundError("Synagogue was not found")

    def _require_project(self, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        return project

    def _reject_duplicate_name(self, synagogue_id: UUID, name: str) -> None:
        if self._unit_of_work.projects.get_by_name(synagogue_id, name) is not None:
            raise ConflictError("A project with this name already exists in the synagogue")

    def _reject_existing_assignment(self, project_id: UUID, user_id: UUID) -> None:
        if self._unit_of_work.assignments.exists(project_id, user_id):
            raise ConflictError("This user is already assigned to the project")

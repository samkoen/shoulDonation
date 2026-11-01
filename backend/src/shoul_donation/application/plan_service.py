"""Store and read the building plan of a project."""

from uuid import UUID

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.entities import Project
from shoul_donation.domain.errors import NotFoundError
from shoul_donation.domain.plan import ProjectPlan, require_plan_image


class PlanService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def replace_plan(self, actor: Actor, project_id: UUID, content_type: str, content: bytes) -> ProjectPlan:
        project = self._visible_project(actor, project_id)
        assert_can_set_project_prices(actor, project.synagogue_id)
        plan = ProjectPlan(project.id, project.synagogue_id, require_plan_image(content_type, content), content)
        self._unit_of_work.plans.save(plan)
        self._unit_of_work.commit()
        return plan

    def get_plan(self, actor: Actor, project_id: UUID) -> ProjectPlan:
        project = self._visible_project(actor, project_id)
        plan = self._unit_of_work.plans.get(project.id)
        if plan is None:
            raise NotFoundError("Project plan was not found")
        return plan

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

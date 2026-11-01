"""Attach a contractor to a realized dedication."""

from decimal import Decimal
from uuid import UUID

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.contractor import Contractor, require_contractor
from shoul_donation.domain.entities import Dedication, Project
from shoul_donation.domain.errors import NotFoundError


class ContractorService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def get(self, actor: Actor, dedication_id: UUID) -> Contractor:
        dedication = self._visible_dedication(actor, dedication_id)
        contractor = self._unit_of_work.contractors.get(dedication.id)
        if contractor is None:
            raise NotFoundError("Contractor was not found")
        return contractor

    def save(
        self,
        actor: Actor,
        dedication_id: UUID,
        name: str,
        phone: str,
        amount: Decimal,
    ) -> Contractor:
        dedication = self._visible_dedication(actor, dedication_id)
        assert_can_set_project_prices(actor, dedication.synagogue_id)
        contractor = require_contractor(
            dedication.id,
            dedication.synagogue_id,
            dedication.project_id,
            dedication.status,
            name,
            phone,
            amount,
        )
        self._unit_of_work.contractors.save(contractor)
        self._unit_of_work.commit()
        return contractor

    def _visible_dedication(self, actor: Actor, dedication_id: UUID) -> Dedication:
        dedication = self._unit_of_work.dedications.get(dedication_id)
        if dedication is None:
            raise NotFoundError("Dedication was not found")
        self._visible_project(actor, dedication.project_id)
        return dedication

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

"""Construction budget and the dedication catalog of one project."""

from dataclasses import replace
from decimal import Decimal
from uuid import UUID, uuid4

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.entities import BudgetSummary, ConstructionBudget, Dedication, Project
from shoul_donation.domain.errors import ConflictError, NotFoundError, ValidationError
from shoul_donation.domain.money import budget_gap, require_money, require_percent, target_amount
from shoul_donation.domain.plan_marker import PlanMarker
from shoul_donation.domain.plan_region import PlanRegion, region_anchor
from shoul_donation.domain.validation import require_name

_CURRENCY = "ILS"


class BudgetService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def set_budget(
        self,
        actor: Actor,
        project_id: UUID,
        construction_cost: Decimal,
        target_percent: Decimal,
    ) -> BudgetSummary:
        project = self._visible_project(actor, project_id)
        assert_can_set_project_prices(actor, project.synagogue_id)
        budget = self._budget(project, construction_cost, target_percent)
        self._unit_of_work.budgets.save(budget)
        self._unit_of_work.commit()
        return self._summary(budget)

    def get_summary(self, actor: Actor, project_id: UUID) -> BudgetSummary:
        project = self._visible_project(actor, project_id)
        budget = self._unit_of_work.budgets.get(project.id)
        if budget is None:
            raise NotFoundError("Budget was not found")
        return self._summary(budget)

    def add_dedication(self, actor: Actor, project_id: UUID, name: str, price: Decimal) -> Dedication:
        project = self._visible_project(actor, project_id)
        assert_can_set_project_prices(actor, project.synagogue_id)
        cleaned_name = require_name(name, "Dedication name")
        self._reject_duplicate_name(project.id, cleaned_name)
        dedication = self._new_dedication(project, cleaned_name, price)
        self._unit_of_work.dedications.add(dedication)
        self._unit_of_work.commit()
        return dedication

    def list_dedications(self, actor: Actor, project_id: UUID) -> list[Dedication]:
        project = self._visible_project(actor, project_id)
        return self._unit_of_work.dedications.list_for_project(project.id)

    def update_dedication(
        self,
        actor: Actor,
        dedication_id: UUID,
        price: Decimal | None,
        status: DedicationStatus | None,
    ) -> Dedication:
        dedication = self._require_dedication(dedication_id)
        self._visible_project(actor, dedication.project_id)
        updated = self._apply_changes(actor, dedication, price, status)
        self._unit_of_work.dedications.save(updated)
        self._unit_of_work.commit()
        return updated

    def _budget(self, project: Project, construction_cost: Decimal, target_percent: Decimal) -> ConstructionBudget:
        return ConstructionBudget(
            project_id=project.id,
            synagogue_id=project.synagogue_id,
            construction_cost=require_money(construction_cost, "Construction cost"),
            target_percent=require_percent(target_percent),
            currency=_CURRENCY,
        )

    def _new_dedication(self, project: Project, name: str, price: Decimal) -> Dedication:
        return Dedication(
            id=uuid4(),
            project_id=project.id,
            synagogue_id=project.synagogue_id,
            name=name,
            price=require_money(price, "Dedication price"),
            status=DedicationStatus.OPEN,
        )

    def set_marker(self, actor: Actor, dedication_id: UUID, marker: PlanMarker | None) -> Dedication:
        dedication = self._owned_dedication(actor, dedication_id)
        updated = replace(dedication, marker=None, region=None) if marker is None else replace(dedication, marker=marker)
        self._unit_of_work.dedications.save(updated)
        self._unit_of_work.commit()
        return updated

    def set_region(self, actor: Actor, dedication_id: UUID, region: PlanRegion) -> Dedication:
        dedication = self._owned_dedication(actor, dedication_id)
        updated = replace(dedication, marker=region_anchor(region), region=region)
        self._unit_of_work.dedications.save(updated)
        self._unit_of_work.commit()
        return updated

    def _owned_dedication(self, actor: Actor, dedication_id: UUID) -> Dedication:
        dedication = self._require_dedication(dedication_id)
        self._visible_project(actor, dedication.project_id)
        assert_can_set_project_prices(actor, dedication.synagogue_id)
        return dedication

    def _apply_changes(
        self,
        actor: Actor,
        dedication: Dedication,
        price: Decimal | None,
        status: DedicationStatus | None,
    ) -> Dedication:
        if price is None and status is None:
            raise ValidationError("Nothing to update")
        updated = dedication
        if price is not None:
            assert_can_set_project_prices(actor, dedication.synagogue_id)
            updated = replace(updated, price=require_money(price, "Dedication price"))
        if status is not None:
            updated = replace(updated, status=status)
        return updated

    def _summary(self, budget: ConstructionBudget) -> BudgetSummary:
        dedications = self._unit_of_work.dedications.list_for_project(budget.project_id)
        total = sum((item.price for item in dedications), Decimal("0.00"))
        target = target_amount(budget.construction_cost, budget.target_percent)
        return BudgetSummary(
            budget=budget,
            target_amount=target,
            dedications_total=total.quantize(Decimal("0.01")),
            gap=budget_gap(target, total),
        )

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

    def _require_dedication(self, dedication_id: UUID) -> Dedication:
        dedication = self._unit_of_work.dedications.get(dedication_id)
        if dedication is None:
            raise NotFoundError("Dedication was not found")
        return dedication

    def _reject_duplicate_name(self, project_id: UUID, name: str) -> None:
        if self._unit_of_work.dedications.get_by_name(project_id, name) is not None:
            raise ConflictError("A dedication with this name already exists in the project")

"""Suggest and apply dedication prices from the fundraising target."""

from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import UUID

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.entities import Dedication, Project
from shoul_donation.domain.errors import NotFoundError
from shoul_donation.domain.money import target_amount
from shoul_donation.domain.pricing import PriceSuggestion, PriceWeight, require_weights, split_by_weight


@dataclass(frozen=True, slots=True)
class PricingPreview:
    target_amount: Decimal
    amount_to_split: Decimal
    items: list[PriceSuggestion]


class PricingService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def preview(self, actor: Actor, project_id: UUID, weights: list[PriceWeight]) -> PricingPreview:
        project = self._owned_project(actor, project_id)
        chosen = require_weights(weights)
        dedications = self._dedications_by_id(project.id)
        target = self._target(project.id)
        to_split = self._amount_to_split(target, dedications, chosen)
        shares = split_by_weight(to_split, chosen)
        items = [self._suggestion(dedications, item.dedication_id, shares) for item in chosen]
        return PricingPreview(target_amount=target, amount_to_split=to_split, items=items)

    def apply(self, actor: Actor, project_id: UUID, weights: list[PriceWeight]) -> list[Dedication]:
        preview = self.preview(actor, project_id, weights)
        dedications = self._dedications_by_id(project_id)
        updated = [
            replace(dedications[item.dedication_id], price=item.suggested_price)
            for item in preview.items
        ]
        for dedication in updated:
            self._unit_of_work.dedications.save(dedication)
        self._unit_of_work.commit()
        return updated

    def _owned_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        assert_can_set_project_prices(actor, project.synagogue_id)
        return project

    def _dedications_by_id(self, project_id: UUID) -> dict[UUID, Dedication]:
        return {item.id: item for item in self._unit_of_work.dedications.list_for_project(project_id)}

    def _target(self, project_id: UUID) -> Decimal:
        budget = self._unit_of_work.budgets.get(project_id)
        if budget is None:
            raise NotFoundError("Set the construction budget before suggesting prices")
        return target_amount(budget.construction_cost, budget.target_percent)

    def _amount_to_split(
        self,
        target: Decimal,
        dedications: dict[UUID, Dedication],
        chosen: list[PriceWeight],
    ) -> Decimal:
        chosen_ids = {item.dedication_id for item in chosen}
        for dedication_id in chosen_ids:
            if dedication_id not in dedications:
                raise NotFoundError("Dedication was not found in this project")
        kept = sum((item.price for item in dedications.values() if item.id not in chosen_ids), Decimal(0))
        return (target - kept).quantize(Decimal("0.01"))

    def _suggestion(
        self,
        dedications: dict[UUID, Dedication],
        dedication_id: UUID,
        shares: dict[UUID, Decimal],
    ) -> PriceSuggestion:
        dedication = dedications[dedication_id]
        return PriceSuggestion(
            dedication_id=dedication.id,
            name=dedication.name,
            current_price=dedication.price,
            suggested_price=shares[dedication_id],
        )

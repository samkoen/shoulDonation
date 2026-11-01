"""Budget and dedication persistence."""

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.entities import ConstructionBudget, Dedication
from shoul_donation.domain.plan_marker import PlanMarker
from shoul_donation.domain.plan_region import PlanRegion, PlanVertex, require_brush
from shoul_donation.infrastructure.orm import ConstructionBudgetRow, DedicationRow


def _amount(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


class SqlAlchemyBudgetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: UUID) -> ConstructionBudget | None:
        row = self._session.get(ConstructionBudgetRow, str(project_id))
        return None if row is None else self._budget(row)

    def save(self, budget: ConstructionBudget) -> None:
        row = self._session.get(ConstructionBudgetRow, str(budget.project_id))
        if row is None:
            self._session.add(self._new_row(budget))
            return
        row.construction_cost = budget.construction_cost
        row.target_percent = budget.target_percent
        row.currency = budget.currency

    def _new_row(self, budget: ConstructionBudget) -> ConstructionBudgetRow:
        return ConstructionBudgetRow(
            project_id=str(budget.project_id),
            synagogue_id=str(budget.synagogue_id),
            construction_cost=budget.construction_cost,
            target_percent=budget.target_percent,
            currency=budget.currency,
        )

    def _budget(self, row: ConstructionBudgetRow) -> ConstructionBudget:
        return ConstructionBudget(
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            construction_cost=_amount(row.construction_cost),
            target_percent=_amount(row.target_percent),
            currency=row.currency,
        )


class SqlAlchemyDedicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, dedication: Dedication) -> None:
        self._session.add(self._new_row(dedication))

    def save(self, dedication: Dedication) -> None:
        row = self._session.get(DedicationRow, str(dedication.id))
        if row is None:
            self.add(dedication)
            return
        row.price = dedication.price
        row.status = dedication.status.value
        row.name = dedication.name
        row.plan_x = None if dedication.marker is None else dedication.marker.x
        row.plan_y = None if dedication.marker is None else dedication.marker.y
        row.plan_region = _region_json(dedication.region)

    def get(self, dedication_id: UUID) -> Dedication | None:
        row = self._session.get(DedicationRow, str(dedication_id))
        return None if row is None else self._dedication(row)

    def get_by_name(self, project_id: UUID, name: str) -> Dedication | None:
        statement = select(DedicationRow).where(
            DedicationRow.project_id == str(project_id),
            DedicationRow.name == name,
        )
        row = self._session.scalar(statement)
        return None if row is None else self._dedication(row)

    def list_for_project(self, project_id: UUID) -> list[Dedication]:
        statement = select(DedicationRow).where(DedicationRow.project_id == str(project_id)).order_by(DedicationRow.name)
        return [self._dedication(row) for row in self._session.scalars(statement)]

    def _new_row(self, dedication: Dedication) -> DedicationRow:
        return DedicationRow(
            id=str(dedication.id),
            project_id=str(dedication.project_id),
            synagogue_id=str(dedication.synagogue_id),
            name=dedication.name,
            price=dedication.price,
            status=dedication.status.value,
            plan_x=None if dedication.marker is None else dedication.marker.x,
            plan_y=None if dedication.marker is None else dedication.marker.y,
            plan_region=_region_json(dedication.region),
        )

    def _dedication(self, row: DedicationRow) -> Dedication:
        return Dedication(
            id=UUID(row.id),
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            name=row.name,
            price=_amount(row.price),
            status=DedicationStatus(row.status),
            marker=_marker(row),
            region=_region(row.plan_region),
        )


def _marker(row: DedicationRow) -> PlanMarker | None:
    if row.plan_x is None or row.plan_y is None:
        return None
    return PlanMarker(x=Decimal(str(row.plan_x)), y=Decimal(str(row.plan_y)))


def _region_json(region: PlanRegion | None) -> str | None:
    if region is None:
        return None
    return json.dumps(
        {
            "kind": region.kind,
            "width": f"{region.brush_width:.2f}",
            "strokes": [[_point(vertex) for vertex in stroke] for stroke in region.strokes],
        }
    )


def _point(vertex: PlanVertex) -> dict[str, str]:
    return {"x": f"{vertex.x:.2f}", "y": f"{vertex.y:.2f}"}


def _region(raw: str | None) -> PlanRegion | None:
    if raw is None or raw == "":
        return None
    payload = json.loads(raw)
    if isinstance(payload, list):
        return None
    strokes = [[(Decimal(str(point["x"])), Decimal(str(point["y"]))) for point in stroke] for stroke in payload["strokes"]]
    return require_brush(strokes, Decimal(str(payload.get("width", "3.50"))))

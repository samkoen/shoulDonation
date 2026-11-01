"""HTTP routes for the construction budget and the dedication catalog."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.entities import BudgetSummary, Dedication
from shoul_donation.domain.plan_marker import require_marker
from shoul_donation.domain.plan_region import PlanRegion, require_brush
from shoul_donation.infrastructure.api.dependencies import get_actor, get_budget_service
from shoul_donation.infrastructure.api.schemas import (
    BudgetRequest,
    BudgetResponse,
    DedicationRequest,
    DedicationResponse,
    DedicationUpdateRequest,
    MarkerRequest,
    PlanRegionRequest,
)

router = APIRouter()


@router.put("/projects/{project_id}/budget", response_model=BudgetResponse)
def set_budget(
    project_id: UUID,
    body: BudgetRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetResponse:
    summary = service.set_budget(actor, project_id, body.construction_cost, body.target_percent)
    return _budget_response(summary)


@router.get("/projects/{project_id}/budget", response_model=BudgetResponse)
def get_budget(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> BudgetResponse:
    return _budget_response(service.get_summary(actor, project_id))


@router.post("/projects/{project_id}/dedications", response_model=DedicationResponse)
def add_dedication(
    project_id: UUID,
    body: DedicationRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> DedicationResponse:
    return dedication_response(service.add_dedication(actor, project_id, body.name, body.price))


@router.get("/projects/{project_id}/dedications", response_model=list[DedicationResponse])
def list_dedications(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> list[DedicationResponse]:
    return [dedication_response(item) for item in service.list_dedications(actor, project_id)]


@router.patch("/dedications/{dedication_id}", response_model=DedicationResponse)
def update_dedication(
    dedication_id: UUID,
    body: DedicationUpdateRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> DedicationResponse:
    updated = service.update_dedication(actor, dedication_id, body.price, body.status)
    return dedication_response(updated)


def _budget_response(summary: BudgetSummary) -> BudgetResponse:
    budget = summary.budget
    return BudgetResponse(
        project_id=budget.project_id,
        construction_cost=money(budget.construction_cost),
        target_percent=money(budget.target_percent),
        currency=budget.currency,
        target_amount=money(summary.target_amount),
        dedications_total=money(summary.dedications_total),
        gap=money(summary.gap),
    )


@router.put("/dedications/{dedication_id}/marker", response_model=DedicationResponse)
def place_marker(
    dedication_id: UUID,
    body: MarkerRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> DedicationResponse:
    updated = service.set_marker(actor, dedication_id, require_marker(body.x, body.y))
    return dedication_response(updated)


@router.delete("/dedications/{dedication_id}/marker", response_model=DedicationResponse)
def remove_marker(
    dedication_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> DedicationResponse:
    return dedication_response(service.set_marker(actor, dedication_id, None))


@router.put("/dedications/{dedication_id}/region", response_model=DedicationResponse)
def paint_region(
    dedication_id: UUID,
    body: PlanRegionRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> DedicationResponse:
    strokes = [[(point.x, point.y) for point in stroke] for stroke in body.strokes]
    return dedication_response(service.set_region(actor, dedication_id, require_brush(strokes, body.width)))


def dedication_response(dedication: Dedication) -> DedicationResponse:
    return DedicationResponse(
        id=dedication.id,
        project_id=dedication.project_id,
        name=dedication.name,
        price=money(dedication.price),
        status=dedication.status,
        plan_x=None if dedication.marker is None else money(dedication.marker.x),
        plan_y=None if dedication.marker is None else money(dedication.marker.y),
        plan_region=_region_payload(dedication.region),
    )


def _region_payload(region: PlanRegion | None) -> dict[str, object] | None:
    if region is None:
        return None
    return {
        "kind": region.kind,
        "width": money(region.brush_width),
        "strokes": [[{"x": money(vertex.x), "y": money(vertex.y)} for vertex in stroke] for stroke in region.strokes],
    }


def money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"

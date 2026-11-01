"""HTTP routes for the calculator simulation and its digital proposal."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from shoul_donation.application.calculator_service import CalculatorService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.calculator import (
    CalculatorSettings,
    Proposal,
    SettingsBounds,
    SimulationDraft,
    SimulationView,
)
from shoul_donation.infrastructure.api.dependencies import get_actor, get_calculator_service
from shoul_donation.infrastructure.api.schemas import (
    CalculatorSettingsRequest,
    CalculatorSettingsResponse,
    ProposalResponse,
    SimulationRequest,
    SimulationResponse,
)

router = APIRouter()


@router.get("/projects/{project_id}/calculator-settings", response_model=CalculatorSettingsResponse)
def get_settings(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> CalculatorSettingsResponse:
    return _settings_response(service.get_settings(actor, project_id))


@router.put("/projects/{project_id}/calculator-settings", response_model=CalculatorSettingsResponse)
def save_settings(
    project_id: UUID,
    body: CalculatorSettingsRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> CalculatorSettingsResponse:
    return _settings_response(service.save_settings(actor, project_id, _bounds(body)))


@router.post("/projects/{project_id}/calculator/preview", response_model=SimulationResponse)
def preview(
    project_id: UUID,
    body: SimulationRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> SimulationResponse:
    return _simulation_response(service.preview(actor, project_id, _draft(body)))


@router.post("/projects/{project_id}/proposals", response_model=ProposalResponse)
def create_proposal(
    project_id: UUID,
    body: SimulationRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> ProposalResponse:
    return _proposal_response(service.create_proposal(actor, project_id, _draft(body)))


@router.patch("/proposals/{proposal_id}", response_model=ProposalResponse)
def update_proposal(
    proposal_id: UUID,
    body: SimulationRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> ProposalResponse:
    return _proposal_response(service.update_proposal(actor, proposal_id, _draft(body)))


@router.delete("/proposals/{proposal_id}", status_code=204)
def delete_proposal(
    proposal_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> Response:
    service.delete_proposal(actor, proposal_id)
    return Response(status_code=204)


@router.get("/projects/{project_id}/proposals", response_model=list[ProposalResponse])
def list_proposals(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CalculatorService, Depends(get_calculator_service)],
) -> list[ProposalResponse]:
    return [_proposal_response(item) for item in service.list_proposals(actor, project_id)]


def _bounds(body: CalculatorSettingsRequest) -> SettingsBounds:
    return SettingsBounds(
        min_monthly=body.min_monthly,
        max_monthly=body.max_monthly,
        max_months=body.max_months,
        min_per_donor=body.min_per_donor,
        max_per_donor=body.max_per_donor,
        min_donors=body.min_donors,
    )


def _draft(body: SimulationRequest) -> SimulationDraft:
    return SimulationDraft(
        dedication_id=body.dedication_id,
        monthly_amount=body.monthly_amount,
        months=body.months,
        donor_count=body.donor_count,
    )


def _settings_response(settings: CalculatorSettings) -> CalculatorSettingsResponse:
    return CalculatorSettingsResponse(
        project_id=settings.project_id,
        min_monthly=_money(settings.min_monthly),
        max_monthly=_money(settings.max_monthly),
        max_months=settings.max_months,
        min_per_donor=_money(settings.min_per_donor),
        max_per_donor=_money(settings.max_per_donor),
        min_donors=settings.min_donors,
        currency=settings.currency,
    )


def _simulation_response(view: SimulationView) -> SimulationResponse:
    simulation = view.simulation
    return SimulationResponse(
        dedication_id=simulation.dedication_id,
        monthly_amount=_money(simulation.monthly_amount),
        months=simulation.months,
        donor_count=simulation.donor_count,
        monthly_within_range=view.monthly_within_range,
        term_within_limit=view.term_within_limit,
        donors_meet_minimum=view.donors_meet_minimum,
        financed_total=_optional_money(view.financed_total),
        status=view.status,
    )


def _proposal_response(proposal: Proposal) -> ProposalResponse:
    return ProposalResponse(
        id=proposal.id,
        dedication_id=proposal.dedication_id,
        monthly_amount=_money(proposal.monthly_amount),
        months=proposal.months,
        donor_count=proposal.donor_count,
        currency=proposal.currency,
        financed_total=_optional_money(proposal.financed_total),
        status=proposal.status,
        created_at=proposal.created_at,
    )


def _optional_money(value: Decimal | None) -> str | None:
    return None if value is None else _money(value)


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"

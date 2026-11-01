"""HTTP routes for the contractor of a realized dedication."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from shoul_donation.application.contractor_service import ContractorService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.contractor import Contractor
from shoul_donation.infrastructure.api.dependencies import get_actor, get_contractor_service
from shoul_donation.infrastructure.api.routes_budget import money
from shoul_donation.infrastructure.api.schemas import ContractorRequest, ContractorResponse

router = APIRouter()


@router.get("/dedications/{dedication_id}/contractor", response_model=ContractorResponse)
def get_contractor(
    dedication_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ContractorService, Depends(get_contractor_service)],
) -> ContractorResponse:
    return _response(service.get(actor, dedication_id))


@router.put("/dedications/{dedication_id}/contractor", response_model=ContractorResponse)
def save_contractor(
    dedication_id: UUID,
    body: ContractorRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ContractorService, Depends(get_contractor_service)],
) -> ContractorResponse:
    return _response(service.save(actor, dedication_id, body.name, body.phone, body.amount))


def _response(contractor: Contractor) -> ContractorResponse:
    return ContractorResponse(
        dedication_id=contractor.dedication_id,
        name=contractor.name,
        phone=contractor.phone,
        amount=money(contractor.amount),
    )

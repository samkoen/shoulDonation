"""HTTP routes for price suggestions. Nothing is written until the owner applies."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from shoul_donation.application.pricing_service import PricingPreview, PricingService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.pricing import PriceWeight
from shoul_donation.infrastructure.api.dependencies import get_actor, get_pricing_service
from shoul_donation.infrastructure.api.routes_budget import dedication_response, money
from shoul_donation.infrastructure.api.schemas import (
    DedicationResponse,
    PriceSuggestionResponse,
    PricingPreviewResponse,
    PricingRequest,
)

router = APIRouter()


@router.post("/projects/{project_id}/pricing/preview", response_model=PricingPreviewResponse)
def preview_prices(
    project_id: UUID,
    body: PricingRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PricingService, Depends(get_pricing_service)],
) -> PricingPreviewResponse:
    return _preview_response(service.preview(actor, project_id, _weights(body)))


@router.post("/projects/{project_id}/pricing/apply", response_model=list[DedicationResponse])
def apply_prices(
    project_id: UUID,
    body: PricingRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PricingService, Depends(get_pricing_service)],
) -> list[DedicationResponse]:
    return [dedication_response(item) for item in service.apply(actor, project_id, _weights(body))]


def _weights(body: PricingRequest) -> list[PriceWeight]:
    return [PriceWeight(dedication_id=item.dedication_id, weight=item.weight) for item in body.items]


def _preview_response(preview: PricingPreview) -> PricingPreviewResponse:
    return PricingPreviewResponse(
        target_amount=money(preview.target_amount),
        amount_to_split=money(preview.amount_to_split),
        items=[
            PriceSuggestionResponse(
                dedication_id=item.dedication_id,
                name=item.name,
                current_price=money(item.current_price),
                suggested_price=money(item.suggested_price),
            )
            for item in preview.items
        ],
    )

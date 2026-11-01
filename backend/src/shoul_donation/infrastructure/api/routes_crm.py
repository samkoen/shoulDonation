"""HTTP routes for donor leads, synagogue inquiries, and meetings."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from shoul_donation.application.crm_service import CrmService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.crm import Lead, Meeting
from shoul_donation.infrastructure.api.dependencies import get_actor, get_crm_service
from shoul_donation.infrastructure.api.schemas import (
    CustomerLeadRequest,
    DonorLeadRequest,
    LeadResponse,
    LeadUpdateRequest,
    MeetingRequest,
    MeetingResponse,
)

router = APIRouter()


@router.post("/projects/{project_id}/leads", response_model=LeadResponse)
def add_donor_lead(
    project_id: UUID,
    body: DonorLeadRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> LeadResponse:
    lead = service.add_donor_lead(actor, project_id, body.name, body.phone, body.dedication_id, body.assignee_id)
    return _lead_response(lead)


@router.get("/projects/{project_id}/leads", response_model=list[LeadResponse])
def list_donor_leads(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> list[LeadResponse]:
    return [_lead_response(lead) for lead in service.list_donor_leads(actor, project_id)]


@router.post("/customer-leads", response_model=LeadResponse)
def add_customer_lead(
    body: CustomerLeadRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> LeadResponse:
    lead = service.add_customer_lead(actor, body.name, body.phone, body.requested_synagogue_name)
    return _lead_response(lead)


@router.get("/customer-leads", response_model=list[LeadResponse])
def list_customer_leads(
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> list[LeadResponse]:
    return [_lead_response(lead) for lead in service.list_customer_leads(actor)]


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: UUID,
    body: LeadUpdateRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> LeadResponse:
    return _lead_response(service.update_lead(actor, lead_id, body.status, body.assignee_id))


@router.post("/leads/{lead_id}/meetings", response_model=MeetingResponse)
def add_meeting(
    lead_id: UUID,
    body: MeetingRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> MeetingResponse:
    return _meeting_response(service.add_meeting(actor, lead_id, body.scheduled_at, body.note, body.close_chance))


@router.get("/leads/{lead_id}/meetings", response_model=list[MeetingResponse])
def list_meetings(
    lead_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> list[MeetingResponse]:
    return [_meeting_response(meeting) for meeting in service.list_meetings(actor, lead_id)]


def _lead_response(lead: Lead) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        kind=lead.kind,
        name=lead.name,
        phone=lead.phone,
        status=lead.status,
        project_id=lead.project_id,
        dedication_id=lead.dedication_id,
        assignee_id=lead.assignee_id,
        requested_synagogue_name=lead.requested_synagogue_name,
    )


def _meeting_response(meeting: Meeting) -> MeetingResponse:
    return MeetingResponse(
        id=meeting.id,
        lead_id=meeting.lead_id,
        scheduled_at=meeting.scheduled_at,
        note=meeting.note,
        close_chance=None if meeting.close_chance is None else f"{meeting.close_chance:.0f}",
    )

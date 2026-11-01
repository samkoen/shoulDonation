"""HTTP routes for the building plan of a project."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from shoul_donation.application.plan_service import PlanService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.plan import MAX_PLAN_BYTES
from shoul_donation.infrastructure.api.dependencies import get_actor, get_plan_service

router = APIRouter()


@router.put("/projects/{project_id}/plan", status_code=204)
async def replace_plan(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PlanService, Depends(get_plan_service)],
    file: Annotated[UploadFile, File()],
) -> Response:
    content = await file.read(MAX_PLAN_BYTES + 1)
    service.replace_plan(actor, project_id, file.content_type or "", content)
    return Response(status_code=204)


@router.get("/projects/{project_id}/plan")
def get_plan(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> Response:
    plan = service.get_plan(actor, project_id)
    return Response(content=plan.content, media_type=plan.content_type)

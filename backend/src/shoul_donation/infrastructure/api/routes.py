"""HTTP routes for identity and projects. Each route performs one action."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.project_service import ProjectService
from shoul_donation.domain.actor import Actor
from shoul_donation.infrastructure.api.dependencies import get_actor, get_identity_service, get_project_service
from shoul_donation.infrastructure.api.schemas import (
    AssignmentRequest,
    AssignmentResponse,
    AssigneeResponse,
    LoginRequest,
    LoginResponse,
    ProjectRequest,
    ProjectResponse,
    SynagogueRequest,
    SynagogueResponse,
    UserRequest,
    UserResponse,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    http_request: Request,
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> LoginResponse:
    actor = service.authenticate(body.email, body.password)
    token = http_request.app.state.token_issuer.issue(actor)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=actor.user_id,
        role=actor.role,
        synagogue_id=actor.synagogue_id,
    )


@router.post("/synagogues", response_model=SynagogueResponse)
def create_synagogue(
    body: SynagogueRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> SynagogueResponse:
    synagogue = service.create_synagogue(actor, body.name)
    return SynagogueResponse(id=synagogue.id, name=synagogue.name)


@router.get("/synagogues", response_model=list[SynagogueResponse])
def list_synagogues(
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> list[SynagogueResponse]:
    return [SynagogueResponse(id=item.id, name=item.name) for item in service.list_synagogues(actor)]


@router.post("/users", response_model=UserResponse)
def register_user(
    body: UserRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> UserResponse:
    user = service.register_user(actor, body.email, body.password, body.role, body.synagogue_id)
    return UserResponse(id=user.id, email=user.email, role=body.role, synagogue_id=body.synagogue_id)


@router.post("/projects", response_model=ProjectResponse)
def create_project(
    body: ProjectRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = service.create_project(actor, body.synagogue_id, body.name)
    return ProjectResponse(id=project.id, synagogue_id=project.synagogue_id, name=project.name)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectResponse]:
    projects = service.list_projects(actor)
    return [
        ProjectResponse(id=project.id, synagogue_id=project.synagogue_id, name=project.name) for project in projects
    ]


@router.post("/projects/{project_id}/assignments", response_model=AssignmentResponse)
def assign_sub_projector(
    project_id: UUID,
    body: AssignmentRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> AssignmentResponse:
    assignment = service.assign_sub_projector(actor, project_id, body.user_id)
    return AssignmentResponse(
        id=assignment.id,
        synagogue_id=assignment.synagogue_id,
        project_id=assignment.project_id,
        user_id=assignment.user_id,
    )


@router.get("/projects/{project_id}/assignees", response_model=list[AssigneeResponse])
def list_assignees(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[AssigneeResponse]:
    members = service.list_project_members(actor, project_id)
    return [AssigneeResponse(user_id=member.user_id, email=member.email) for member in members]

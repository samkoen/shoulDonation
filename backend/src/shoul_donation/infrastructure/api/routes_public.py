"""HTTP routes for the public page: owner settings behind login, visitor routes without it."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from shoul_donation.application.public_page_service import PublicPageService
from shoul_donation.application.public_site_service import PublicProjectView, PublicSiteService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.entities import Dedication
from shoul_donation.domain.plan import MAX_PLAN_BYTES
from shoul_donation.domain.public_page import PublicPage
from shoul_donation.infrastructure.api.dependencies import get_actor, get_public_page_service, get_public_site_service
from shoul_donation.infrastructure.api.routes_budget import _region_payload, money
from shoul_donation.infrastructure.api.schemas import (
    GalleryImageResponse,
    PublicContactRequest,
    PublicDedicationResponse,
    PublicPageRequest,
    PublicPageResponse,
    PublicProjectResponse,
)

router = APIRouter()


@router.get("/projects/{project_id}/public-page", response_model=PublicPageResponse)
def get_public_page(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
) -> PublicPageResponse | Response:
    page = service.get_settings(actor, project_id)
    if page is None:
        return Response(status_code=404)
    return _page_response(page)


@router.put("/projects/{project_id}/public-page", response_model=PublicPageResponse)
def save_public_page(
    project_id: UUID,
    body: PublicPageRequest,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
) -> PublicPageResponse:
    return _page_response(service.save_settings(actor, project_id, body.slug, body.vision, body.enabled))


@router.get("/projects/{project_id}/gallery", response_model=list[GalleryImageResponse])
def list_gallery(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
) -> list[GalleryImageResponse]:
    return [GalleryImageResponse(id=image_id) for image_id in service.list_gallery(actor, project_id)]


@router.post("/projects/{project_id}/gallery", response_model=GalleryImageResponse)
async def add_gallery_image(
    project_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
    file: Annotated[UploadFile, File()],
) -> GalleryImageResponse:
    content = await file.read(MAX_PLAN_BYTES + 1)
    image = service.add_gallery_image(actor, project_id, file.content_type or "", content)
    return GalleryImageResponse(id=image.id)


@router.get("/gallery/{image_id}")
def get_gallery_image(
    image_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
) -> Response:
    image = service.get_gallery_image(actor, image_id)
    return Response(content=image.content, media_type=image.content_type)


@router.delete("/gallery/{image_id}", status_code=204)
def remove_gallery_image(
    image_id: UUID,
    actor: Annotated[Actor, Depends(get_actor)],
    service: Annotated[PublicPageService, Depends(get_public_page_service)],
) -> Response:
    service.remove_gallery_image(actor, image_id)
    return Response(status_code=204)


@router.get("/public/{slug}", response_model=PublicProjectResponse)
def view_public_project(
    slug: str,
    service: Annotated[PublicSiteService, Depends(get_public_site_service)],
) -> PublicProjectResponse:
    return _public_response(service.view(slug))


@router.get("/public/{slug}/plan")
def public_plan(slug: str, service: Annotated[PublicSiteService, Depends(get_public_site_service)]) -> Response:
    plan = service.plan(slug)
    return Response(content=plan.content, media_type=plan.content_type)


@router.get("/public/{slug}/gallery/{image_id}")
def public_gallery_image(
    slug: str,
    image_id: UUID,
    service: Annotated[PublicSiteService, Depends(get_public_site_service)],
) -> Response:
    image = service.gallery_image(slug, image_id)
    return Response(content=image.content, media_type=image.content_type)


@router.post("/public/{slug}/contact", status_code=204)
def submit_public_contact(
    slug: str,
    body: PublicContactRequest,
    service: Annotated[PublicSiteService, Depends(get_public_site_service)],
) -> Response:
    service.submit_contact(slug, body.name, body.phone, body.synagogue_name)
    return Response(status_code=204)


def _page_response(page: PublicPage) -> PublicPageResponse:
    return PublicPageResponse(project_id=page.project_id, slug=page.slug, vision=page.vision, enabled=page.enabled)


def _public_response(view: PublicProjectView) -> PublicProjectResponse:
    return PublicProjectResponse(
        slug=view.slug,
        project_name=view.project_name,
        synagogue_name=view.synagogue_name,
        vision=view.vision,
        currency=view.currency,
        has_plan=view.has_plan,
        gallery_image_ids=view.gallery_image_ids,
        dedications=[_public_dedication(item) for item in view.dedications],
    )


def _public_dedication(dedication: Dedication) -> PublicDedicationResponse:
    marker = dedication.marker
    return PublicDedicationResponse(
        id=dedication.id,
        name=dedication.name,
        price=money(dedication.price),
        status=dedication.status,
        plan_x=None if marker is None else money(marker.x),
        plan_y=None if marker is None else money(marker.y),
        plan_region=_region_payload(dedication.region),
    )

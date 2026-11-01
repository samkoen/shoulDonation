"""Owner-side settings of the public page: address, vision, gallery."""

from uuid import UUID, uuid4

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.entities import Project
from shoul_donation.domain.errors import ConflictError, NotFoundError, ValidationError
from shoul_donation.domain.plan import require_plan_image
from shoul_donation.domain.public_page import (
    MAX_GALLERY_IMAGES,
    GalleryImage,
    PublicPage,
    require_slug,
    require_vision,
)


class PublicPageService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def get_settings(self, actor: Actor, project_id: UUID) -> PublicPage | None:
        project = self._visible_project(actor, project_id)
        return self._unit_of_work.public_pages.get(project.id)

    def save_settings(self, actor: Actor, project_id: UUID, slug: str, vision: str, enabled: bool) -> PublicPage:
        project = self._owned_project(actor, project_id)
        page = PublicPage(project.id, project.synagogue_id, require_slug(slug), require_vision(vision), enabled)
        self._assert_slug_is_free(page)
        self._unit_of_work.public_pages.save(page)
        self._unit_of_work.commit()
        return page

    def list_gallery(self, actor: Actor, project_id: UUID) -> list[UUID]:
        project = self._visible_project(actor, project_id)
        return self._unit_of_work.gallery.list_ids_for_project(project.id)

    def get_gallery_image(self, actor: Actor, image_id: UUID) -> GalleryImage:
        image = self._unit_of_work.gallery.get(image_id)
        if image is None:
            raise NotFoundError("Gallery image was not found")
        self._visible_project(actor, image.project_id)
        return image

    def add_gallery_image(self, actor: Actor, project_id: UUID, content_type: str, content: bytes) -> GalleryImage:
        project = self._owned_project(actor, project_id)
        existing = self._unit_of_work.gallery.list_ids_for_project(project.id)
        if len(existing) >= MAX_GALLERY_IMAGES:
            raise ValidationError(f"The gallery holds at most {MAX_GALLERY_IMAGES} images")
        image = self._new_image(project, require_plan_image(content_type, content), content, len(existing))
        self._unit_of_work.gallery.add(image)
        self._unit_of_work.commit()
        return image

    def remove_gallery_image(self, actor: Actor, image_id: UUID) -> None:
        image = self._unit_of_work.gallery.get(image_id)
        if image is None:
            raise NotFoundError("Gallery image was not found")
        self._owned_project(actor, image.project_id)
        self._unit_of_work.gallery.delete(image.id)
        self._unit_of_work.commit()

    def _new_image(self, project: Project, content_type: str, content: bytes, position: int) -> GalleryImage:
        return GalleryImage(
            id=uuid4(),
            project_id=project.id,
            synagogue_id=project.synagogue_id,
            content_type=content_type,
            content=content,
            position=position,
        )

    def _assert_slug_is_free(self, page: PublicPage) -> None:
        other = self._unit_of_work.public_pages.get_by_slug(page.slug)
        if other is not None and other.project_id != page.project_id:
            raise ConflictError("This public address is already used by another project")

    def _owned_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._visible_project(actor, project_id)
        assert_can_set_project_prices(actor, project.synagogue_id)
        return project

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

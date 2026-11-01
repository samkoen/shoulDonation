"""What an anonymous visitor sees on an enabled public page, and what they can send back."""

from dataclasses import dataclass
from uuid import UUID

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.crm import Lead, new_customer_lead
from shoul_donation.domain.entities import Dedication
from shoul_donation.domain.errors import NotFoundError
from shoul_donation.domain.plan import ProjectPlan
from shoul_donation.domain.public_page import GalleryImage, PublicPage

DEFAULT_CURRENCY = "ILS"


@dataclass(frozen=True, slots=True)
class PublicProjectView:
    slug: str
    project_name: str
    synagogue_name: str
    vision: str
    currency: str
    has_plan: bool
    gallery_image_ids: list[UUID]
    dedications: list[Dedication]


class PublicSiteService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def view(self, slug: str) -> PublicProjectView:
        page = self._enabled_page(slug)
        project = self._unit_of_work.projects.get(page.project_id)
        synagogue = self._unit_of_work.synagogues.get(page.synagogue_id)
        if project is None or synagogue is None:
            raise NotFoundError("Public page was not found")
        return PublicProjectView(
            slug=page.slug,
            project_name=project.name,
            synagogue_name=synagogue.name,
            vision=page.vision,
            currency=self._currency(page.project_id),
            has_plan=self._unit_of_work.plans.exists(page.project_id),
            gallery_image_ids=self._unit_of_work.gallery.list_ids_for_project(page.project_id),
            dedications=self._unit_of_work.dedications.list_for_project(page.project_id),
        )

    def plan(self, slug: str) -> ProjectPlan:
        page = self._enabled_page(slug)
        plan = self._unit_of_work.plans.get(page.project_id)
        if plan is None:
            raise NotFoundError("Project plan was not found")
        return plan

    def gallery_image(self, slug: str, image_id: UUID) -> GalleryImage:
        page = self._enabled_page(slug)
        image = self._unit_of_work.gallery.get(image_id)
        if image is None or image.project_id != page.project_id:
            raise NotFoundError("Gallery image was not found")
        return image

    def submit_contact(self, slug: str, name: str, phone: str, synagogue_name: str) -> Lead:
        self._enabled_page(slug)
        lead = new_customer_lead(name, phone, synagogue_name)
        self._unit_of_work.leads.add(lead)
        self._unit_of_work.commit()
        return lead

    def _enabled_page(self, slug: str) -> PublicPage:
        page = self._unit_of_work.public_pages.get_by_slug(slug.strip().lower())
        if page is None or not page.enabled:
            raise NotFoundError("Public page was not found")
        return page

    def _currency(self, project_id: UUID) -> str:
        budget = self._unit_of_work.budgets.get(project_id)
        return DEFAULT_CURRENCY if budget is None else budget.currency

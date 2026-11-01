"""Public page rules on an in-memory store."""

import base64
from decimal import Decimal
from uuid import uuid4

import pytest

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.plan_service import PlanService
from shoul_donation.application.project_service import ProjectService
from shoul_donation.application.public_page_service import PublicPageService
from shoul_donation.application.public_site_service import PublicSiteService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.plan_marker import require_marker
from shoul_donation.domain.public_page import MAX_GALLERY_IMAGES, require_slug
from shoul_donation.domain.role import Role
from tests.support.memory_unit_of_work import MemoryUnitOfWork

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
PASSWORD = "user-pass-1"


def test_a_disabled_page_is_invisible_to_visitors() -> None:
    store, lead, _, project = _project_with_team()
    PublicPageService(store).save_settings(lead, project.id, "tiferet-tzvi", "Our vision", enabled=False)
    with pytest.raises(NotFoundError):
        PublicSiteService(store).view("tiferet-tzvi")


def test_an_enabled_page_shows_dedications_plan_and_gallery() -> None:
    store, lead, _, project = _project_with_team()
    pages = PublicPageService(store)
    dedication = BudgetService(store).add_dedication(lead, project.id, "Aron", Decimal("1000"))
    BudgetService(store).set_marker(lead, dedication.id, require_marker(Decimal("10"), Decimal("20")))
    PlanService(store).replace_plan(lead, project.id, "image/png", PNG)
    image = pages.add_gallery_image(lead, project.id, "image/png", PNG)
    pages.save_settings(lead, project.id, "Tiferet-Tzvi", "Our vision", enabled=True)
    view = PublicSiteService(store).view("tiferet-tzvi")
    assert view.project_name == "Main hall"
    assert view.synagogue_name == "North"
    assert view.vision == "Our vision"
    assert view.has_plan is True
    assert view.gallery_image_ids == [image.id]
    assert [item.name for item in view.dedications] == ["Aron"]
    assert view.dedications[0].marker is not None
    assert PublicSiteService(store).plan("tiferet-tzvi").content == PNG
    assert PublicSiteService(store).gallery_image("tiferet-tzvi", image.id).content == PNG


def test_a_visitor_contact_becomes_a_customer_lead_for_the_admin() -> None:
    store, lead, _, project = _project_with_team()
    PublicPageService(store).save_settings(lead, project.id, "tiferet-tzvi", "", enabled=True)
    created = PublicSiteService(store).submit_contact("tiferet-tzvi", "Moshe", "0501234567", "Beit Yaakov")
    assert created.kind is LeadKind.SYNAGOGUE_CUSTOMER
    assert created.requested_synagogue_name == "Beit Yaakov"
    assert created.synagogue_id is None
    assert store.leads_by_id[created.id] == created


def test_the_slug_is_unique_across_projects() -> None:
    store, lead, _, project = _project_with_team()
    other = ProjectService(store).create_project(lead, project.synagogue_id, "Second hall")
    pages = PublicPageService(store)
    pages.save_settings(lead, project.id, "tiferet-tzvi", "", enabled=True)
    with pytest.raises(ConflictError):
        pages.save_settings(lead, other.id, "tiferet-tzvi", "", enabled=True)
    pages.save_settings(lead, project.id, "tiferet-tzvi", "Updated", enabled=True)
    assert store.public_pages_by_project[project.id].vision == "Updated"


def test_a_sub_projector_reads_settings_but_cannot_change_them() -> None:
    store, lead, sub, project = _project_with_team()
    pages = PublicPageService(store)
    pages.save_settings(lead, project.id, "tiferet-tzvi", "", enabled=True)
    assert pages.get_settings(sub, project.id) is not None
    with pytest.raises(ForbiddenError):
        pages.save_settings(sub, project.id, "other", "", enabled=True)
    with pytest.raises(ForbiddenError):
        pages.add_gallery_image(sub, project.id, "image/png", PNG)


def test_the_gallery_is_capped_and_images_can_be_removed() -> None:
    store, lead, _, project = _project_with_team()
    pages = PublicPageService(store)
    images = [pages.add_gallery_image(lead, project.id, "image/png", PNG) for _ in range(MAX_GALLERY_IMAGES)]
    with pytest.raises(ValidationError):
        pages.add_gallery_image(lead, project.id, "image/png", PNG)
    pages.remove_gallery_image(lead, images[0].id)
    assert len(pages.list_gallery(lead, project.id)) == MAX_GALLERY_IMAGES - 1


def test_a_visitor_cannot_read_another_project_image_through_the_slug() -> None:
    store, lead, _, project = _project_with_team()
    other = ProjectService(store).create_project(lead, project.synagogue_id, "Second hall")
    pages = PublicPageService(store)
    foreign = pages.add_gallery_image(lead, other.id, "image/png", PNG)
    pages.save_settings(lead, project.id, "tiferet-tzvi", "", enabled=True)
    with pytest.raises(NotFoundError):
        PublicSiteService(store).gallery_image("tiferet-tzvi", foreign.id)


@pytest.mark.parametrize("value", ["ab", "Has Space", "עברית", "-lead", "trail-", "a" * 61])
def test_invalid_slugs_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        require_slug(value)


def test_slugs_are_normalised() -> None:
    assert require_slug("  Tiferet-Tzvi-2026 ") == "tiferet-tzvi-2026"


def _project_with_team():
    store = MemoryUnitOfWork()
    identity = IdentityService(store, PasswordHasher(1_000))
    projects = ProjectService(store)
    admin = Actor(user_id=uuid4(), role=Role.PLATFORM_ADMIN, synagogue_id=None)
    synagogue = identity.create_synagogue(admin, "North")
    lead_user = identity.register_user(admin, "lead@shoul.test", PASSWORD, Role.LEAD_PROJECTOR, synagogue.id)
    sub_user = identity.register_user(admin, "sub@shoul.test", PASSWORD, Role.SUB_PROJECTOR, synagogue.id)
    lead = Actor(user_id=lead_user.id, role=Role.LEAD_PROJECTOR, synagogue_id=synagogue.id)
    project = projects.create_project(lead, synagogue.id, "Main hall")
    projects.assign_sub_projector(lead, project.id, sub_user.id)
    sub = Actor(user_id=sub_user.id, role=Role.SUB_PROJECTOR, synagogue_id=synagogue.id)
    return store, lead, sub, project

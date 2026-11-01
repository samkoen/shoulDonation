"""Public page settings and gallery persistence. Image bytes stay in the database."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.public_page import GalleryImage, PublicPage
from shoul_donation.infrastructure.orm import GalleryImageRow, PublicPageRow


class SqlAlchemyPublicPageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: UUID) -> PublicPage | None:
        row = self._session.get(PublicPageRow, str(project_id))
        return None if row is None else self._page(row)

    def get_by_slug(self, slug: str) -> PublicPage | None:
        row = self._session.scalar(select(PublicPageRow).where(PublicPageRow.slug == slug))
        return None if row is None else self._page(row)

    def save(self, page: PublicPage) -> None:
        row = self._session.get(PublicPageRow, str(page.project_id))
        if row is None:
            self._session.add(self._new_row(page))
            return
        row.slug = page.slug
        row.vision = page.vision
        row.enabled = page.enabled

    def _new_row(self, page: PublicPage) -> PublicPageRow:
        return PublicPageRow(
            project_id=str(page.project_id),
            synagogue_id=str(page.synagogue_id),
            slug=page.slug,
            vision=page.vision,
            enabled=page.enabled,
        )

    def _page(self, row: PublicPageRow) -> PublicPage:
        return PublicPage(
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            slug=row.slug,
            vision=row.vision,
            enabled=row.enabled,
        )


class SqlAlchemyGalleryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, image: GalleryImage) -> None:
        self._session.add(
            GalleryImageRow(
                id=str(image.id),
                project_id=str(image.project_id),
                synagogue_id=str(image.synagogue_id),
                content_type=image.content_type,
                content=image.content,
                position=image.position,
            )
        )

    def get(self, image_id: UUID) -> GalleryImage | None:
        row = self._session.get(GalleryImageRow, str(image_id))
        return None if row is None else self._image(row)

    def list_ids_for_project(self, project_id: UUID) -> list[UUID]:
        statement = (
            select(GalleryImageRow.id)
            .where(GalleryImageRow.project_id == str(project_id))
            .order_by(GalleryImageRow.position, GalleryImageRow.id)
        )
        return [UUID(value) for value in self._session.scalars(statement)]

    def delete(self, image_id: UUID) -> None:
        row = self._session.get(GalleryImageRow, str(image_id))
        if row is not None:
            self._session.delete(row)

    def _image(self, row: GalleryImageRow) -> GalleryImage:
        return GalleryImage(
            id=UUID(row.id),
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            content_type=row.content_type,
            content=bytes(row.content),
            position=row.position,
        )

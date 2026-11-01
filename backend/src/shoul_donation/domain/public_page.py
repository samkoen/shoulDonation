"""Public showcase of a project: address, vision text, and gallery images."""

import re
from dataclasses import dataclass
from uuid import UUID

from shoul_donation.domain.errors import ValidationError

MAX_VISION_CHARS = 2000
MAX_GALLERY_IMAGES = 12
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_MIN = 3
_SLUG_MAX = 60


@dataclass(frozen=True, slots=True)
class PublicPage:
    project_id: UUID
    synagogue_id: UUID
    slug: str
    vision: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class GalleryImage:
    id: UUID
    project_id: UUID
    synagogue_id: UUID
    content_type: str
    content: bytes
    position: int


def require_slug(value: str) -> str:
    slug = value.strip().lower()
    if not _SLUG_MIN <= len(slug) <= _SLUG_MAX or not _SLUG.match(slug):
        raise ValidationError("The public address must use 3 to 60 latin letters, digits, or hyphens")
    return slug


def require_vision(value: str) -> str:
    vision = value.strip()
    if len(vision) > MAX_VISION_CHARS:
        raise ValidationError(f"The vision text must stay under {MAX_VISION_CHARS} characters")
    return vision

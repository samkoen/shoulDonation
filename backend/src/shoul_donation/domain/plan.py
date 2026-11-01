"""The building plan of one project. The bytes live in the database, not on the server disk."""

from dataclasses import dataclass
from uuid import UUID

from shoul_donation.domain.errors import ValidationError

MAX_PLAN_BYTES = 8_000_000

_SIGNATURES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}


@dataclass(frozen=True, slots=True)
class ProjectPlan:
    project_id: UUID
    synagogue_id: UUID
    content_type: str
    content: bytes


def require_plan_image(content_type: str, content: bytes) -> str:
    media = _declared_type(content_type, content)
    _require_size(content)
    if not _matches(media, content):
        raise ValidationError("The plan file does not match its image type")
    return media


def _declared_type(content_type: str, content: bytes) -> str:
    media = content_type.split(";", 1)[0].strip().lower()
    if media in ("", "application/octet-stream"):
        return _detect(content)
    if media not in _SIGNATURES and media != "image/webp":
        raise ValidationError("The plan must be a PNG, JPEG, or WebP image")
    return media


def _detect(content: bytes) -> str:
    if content.startswith(_SIGNATURES["image/png"]):
        return "image/png"
    if content.startswith(_SIGNATURES["image/jpeg"]):
        return "image/jpeg"
    if _matches("image/webp", content):
        return "image/webp"
    raise ValidationError("The plan must be a PNG, JPEG, or WebP image")


def _require_size(content: bytes) -> None:
    if len(content) == 0 or len(content) > MAX_PLAN_BYTES:
        raise ValidationError("The plan image must be between 1 byte and 8 MB")


def _matches(media: str, content: bytes) -> bool:
    if media == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return content.startswith(_SIGNATURES[media])

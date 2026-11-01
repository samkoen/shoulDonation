"""Input checks shared by the application services."""

from shoul_donation.domain.errors import ValidationError


def normalize_email(email: str) -> str:
    cleaned = email.strip().lower()
    if not _is_email(cleaned):
        raise ValidationError("Email is invalid")
    return cleaned


def require_name(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 200:
        raise ValidationError(f"{field_name} must be between 1 and 200 characters")
    return cleaned


def require_password(password: str) -> str:
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters")
    return password


def require_phone(value: str) -> str:
    cleaned = "".join(value.split())
    if not _is_phone(cleaned):
        raise ValidationError("Phone must contain 7 to 20 digits")
    return cleaned


def require_note(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) > 500:
        raise ValidationError("Note must be at most 500 characters")
    return cleaned


def _is_phone(value: str) -> bool:
    return 7 <= len(value) <= 20 and all(char in "+0123456789-" for char in value)


def _is_email(value: str) -> bool:
    local, separator, domain = value.partition("@")
    return bool(separator and local and domain and "." in domain and " " not in value)

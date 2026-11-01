"""Input validation."""

import pytest

from shoul_donation.domain.errors import ValidationError
from shoul_donation.domain.validation import normalize_email, require_name, require_password


def test_email_is_trimmed_and_lowered() -> None:
    assert normalize_email("  Ada@Shoul.Test ") == "ada@shoul.test"


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValidationError):
        normalize_email("ada-at-shoul")


def test_blank_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        require_name("   ", "Project name")


def test_short_password_is_rejected() -> None:
    with pytest.raises(ValidationError):
        require_password("short")

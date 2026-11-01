"""Donor leads inside a project, and new-synagogue inquiries."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.lead_status import LeadStatus
from shoul_donation.domain.validation import require_name, require_phone


@dataclass(frozen=True, slots=True)
class Lead:
    id: UUID
    kind: LeadKind
    name: str
    phone: str
    status: LeadStatus
    synagogue_id: UUID | None
    project_id: UUID | None
    dedication_id: UUID | None
    assignee_id: UUID | None
    requested_synagogue_name: str | None


@dataclass(frozen=True, slots=True)
class Meeting:
    id: UUID
    lead_id: UUID
    scheduled_at: datetime
    note: str
    close_chance: Decimal | None


def new_customer_lead(name: str, phone: str, requested_synagogue_name: str) -> Lead:
    """A synagogue asking to join the platform. Nobody owns it until the admin picks it up."""
    return Lead(
        id=uuid4(),
        kind=LeadKind.SYNAGOGUE_CUSTOMER,
        name=require_name(name, "Lead name"),
        phone=require_phone(phone),
        status=LeadStatus.NEW,
        synagogue_id=None,
        project_id=None,
        dedication_id=None,
        assignee_id=None,
        requested_synagogue_name=require_name(requested_synagogue_name, "Synagogue name"),
    )


def require_meeting_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value

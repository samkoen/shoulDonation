"""A contractor attached when a dedication is fully funded."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.errors import ValidationError
from shoul_donation.domain.money import require_money
from shoul_donation.domain.validation import require_name, require_phone


@dataclass(frozen=True, slots=True)
class Contractor:
    dedication_id: UUID
    synagogue_id: UUID
    project_id: UUID
    name: str
    phone: str
    amount: Decimal


def require_contractor(
    dedication_id: UUID,
    synagogue_id: UUID,
    project_id: UUID,
    status: DedicationStatus,
    name: str,
    phone: str,
    amount: Decimal,
) -> Contractor:
    if status is not DedicationStatus.REALIZED:
        raise ValidationError("A contractor can be attached only after the dedication is realized")
    return Contractor(
        dedication_id=dedication_id,
        synagogue_id=synagogue_id,
        project_id=project_id,
        name=require_name(name, "Contractor name"),
        phone=require_phone(phone),
        amount=require_money(amount, "Contractor amount"),
    )

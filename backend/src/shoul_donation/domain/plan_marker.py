"""Where a dedication sits on the building plan, as percentages of the image size."""

from dataclasses import dataclass
from decimal import Decimal

from shoul_donation.domain.errors import ValidationError

_STEP = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PlanMarker:
    x: Decimal
    y: Decimal


def require_marker(x: Decimal, y: Decimal) -> PlanMarker:
    return PlanMarker(require_percent_axis(x, "x"), require_percent_axis(y, "y"))


def require_percent_axis(value: Decimal, axis: str) -> Decimal:
    position = value.quantize(_STEP)
    if position < 0 or position > 100:
        raise ValidationError(f"Marker {axis} must be between 0 and 100 percent")
    return position

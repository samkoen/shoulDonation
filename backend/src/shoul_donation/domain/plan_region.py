"""A painted patch on the building plan, stored as percent strokes."""

from dataclasses import dataclass
from decimal import Decimal

from shoul_donation.domain.errors import ValidationError
from shoul_donation.domain.plan_marker import PlanMarker, require_percent_axis

_MIN_STROKES = 1
_MAX_STROKES = 12
_MAX_POINTS = 40
_MIN_WIDTH = Decimal("1.00")
_MAX_WIDTH = Decimal("8.00")


@dataclass(frozen=True, slots=True)
class PlanVertex:
    x: Decimal
    y: Decimal


@dataclass(frozen=True, slots=True)
class PlanRegion:
    kind: str
    strokes: tuple[tuple[PlanVertex, ...], ...]
    brush_width: Decimal


def require_brush(strokes: list[list[tuple[Decimal, Decimal]]], width: Decimal) -> PlanRegion:
    cleaned = tuple(_stroke(item) for item in strokes if item)
    if len(cleaned) < _MIN_STROKES:
        raise ValidationError("Paint at least one stroke")
    if len(cleaned) > _MAX_STROKES:
        raise ValidationError("Too many painted strokes")
    return PlanRegion("brush", cleaned, _require_width(width))


def region_anchor(region: PlanRegion) -> PlanMarker:
    first = region.strokes[0][0]
    return PlanMarker(first.x, first.y)


def _stroke(points: list[tuple[Decimal, Decimal]]) -> tuple[PlanVertex, ...]:
    sampled = points if len(points) <= _MAX_POINTS else points[:: max(1, len(points) // _MAX_POINTS)][:_MAX_POINTS]
    return tuple(_vertex(x, y) for x, y in sampled)


def _vertex(x: Decimal, y: Decimal) -> PlanVertex:
    return PlanVertex(require_percent_axis(x, "x"), require_percent_axis(y, "y"))


def _require_width(width: Decimal) -> Decimal:
    value = width.quantize(Decimal("0.01"))
    if value < _MIN_WIDTH or value > _MAX_WIDTH:
        raise ValidationError("Brush width must be between 1 and 8 percent")
    return value

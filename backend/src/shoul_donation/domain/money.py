"""Money rules. Amounts stay in Decimal and never pass through float."""

from decimal import Decimal

from shoul_donation.domain.errors import ValidationError

_CENT = Decimal("0.01")


def require_money(value: Decimal, field_name: str) -> Decimal:
    amount = _cents(value)
    if amount <= 0:
        raise ValidationError(f"{field_name} must be greater than zero")
    return amount


def require_close_chance(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    chance = value.quantize(Decimal("1"))
    if chance < 0 or chance > 100:
        raise ValidationError("Close chance must be between 0 and 100")
    return chance


def require_percent(value: Decimal) -> Decimal:
    percent = _cents(value)
    if percent <= 0:
        raise ValidationError("Target percent must be greater than zero")
    return percent


def target_amount(construction_cost: Decimal, target_percent: Decimal) -> Decimal:
    return (construction_cost * target_percent / Decimal(100)).quantize(_CENT)


def budget_gap(target: Decimal, dedications_total: Decimal) -> Decimal:
    return (target - dedications_total).quantize(_CENT)


def _cents(value: Decimal) -> Decimal:
    return value.quantize(_CENT)

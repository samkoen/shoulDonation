"""Price suggestions. The owner decides; this only splits an amount by weight."""

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from uuid import UUID

from shoul_donation.domain.errors import ValidationError

_CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PriceWeight:
    dedication_id: UUID
    weight: Decimal


@dataclass(frozen=True, slots=True)
class PriceSuggestion:
    dedication_id: UUID
    name: str
    current_price: Decimal
    suggested_price: Decimal


def require_weights(weights: list[PriceWeight]) -> list[PriceWeight]:
    if not weights:
        raise ValidationError("Choose at least one dedication to price")
    if len({item.dedication_id for item in weights}) != len(weights):
        raise ValidationError("A dedication appears twice")
    for item in weights:
        if item.weight <= 0:
            raise ValidationError("Each weight must be greater than zero")
    return weights


def split_by_weight(amount: Decimal, weights: list[PriceWeight]) -> dict[UUID, Decimal]:
    if amount <= 0:
        raise ValidationError("There is nothing left to split across these dedications")
    total_weight = sum((item.weight for item in weights), Decimal(0))
    shares = {item.dedication_id: _share(amount, item.weight, total_weight) for item in weights}
    return _spread_remainder(shares, amount, weights)


def _share(amount: Decimal, weight: Decimal, total_weight: Decimal) -> Decimal:
    return (amount * weight / total_weight).quantize(_CENT, rounding=ROUND_DOWN)


def _spread_remainder(shares: dict[UUID, Decimal], amount: Decimal, weights: list[PriceWeight]) -> dict[UUID, Decimal]:
    """Hand the leftover cents one by one to the heaviest items so no row stands out."""
    cents_left = int((amount - sum(shares.values(), Decimal(0))) / _CENT)
    by_weight = sorted(weights, key=lambda item: item.weight, reverse=True)
    for index in range(cents_left):
        target = by_weight[index % len(by_weight)].dedication_id
        shares[target] = (shares[target] + _CENT).quantize(_CENT)
    return shares

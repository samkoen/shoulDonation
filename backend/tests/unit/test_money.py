"""Budget arithmetic."""

from decimal import Decimal

from shoul_donation.domain.money import budget_gap, require_percent, target_amount


def test_target_can_exceed_the_construction_cost() -> None:
    target = target_amount(Decimal("1000000.00"), require_percent(Decimal("120")))
    assert target == Decimal("1200000.00")


def test_gap_is_what_remains_after_dedication_prices() -> None:
    assert budget_gap(Decimal("1200.00"), Decimal("1000.00")) == Decimal("200.00")

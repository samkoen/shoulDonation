"""Financing total. The formula stays closed until a rate table is supplied."""

from decimal import Decimal
from typing import Protocol


class FinancingCalculator(Protocol):
    def total_for(self, monthly_amount: Decimal, months: int) -> Decimal | None:
        """Return the financed total, or None while the rate table is missing."""


class PendingRateTable:
    """Placeholder. It never invents a heter iska or interest formula."""

    def total_for(self, monthly_amount: Decimal, months: int) -> Decimal | None:
        del monthly_amount, months
        return None

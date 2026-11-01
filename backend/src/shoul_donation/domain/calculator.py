"""Per-project calculator bounds and the checks that do not need a rate table."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from shoul_donation.domain.entities import Project
from shoul_donation.domain.errors import ValidationError
from shoul_donation.domain.money import require_money
from shoul_donation.domain.proposal_status import ProposalStatus

_CURRENCY = "ILS"


@dataclass(frozen=True, slots=True)
class CalculatorSettings:
    project_id: UUID
    synagogue_id: UUID
    min_monthly: Decimal
    max_monthly: Decimal
    max_months: int
    min_per_donor: Decimal
    max_per_donor: Decimal
    min_donors: int
    currency: str


@dataclass(frozen=True, slots=True)
class SettingsBounds:
    min_monthly: Decimal
    max_monthly: Decimal
    max_months: int
    min_per_donor: Decimal
    max_per_donor: Decimal
    min_donors: int


@dataclass(frozen=True, slots=True)
class SimulationDraft:
    dedication_id: UUID
    monthly_amount: Decimal
    months: int
    donor_count: int


@dataclass(frozen=True, slots=True)
class PreparedSimulation:
    dedication_id: UUID
    monthly_amount: Decimal
    months: int
    donor_count: int


@dataclass(frozen=True, slots=True)
class SimulationView:
    simulation: PreparedSimulation
    monthly_within_range: bool
    term_within_limit: bool
    donors_meet_minimum: bool
    financed_total: Decimal | None
    status: ProposalStatus


@dataclass(frozen=True, slots=True)
class RangeCheck:
    monthly_within_range: bool
    term_within_limit: bool
    donors_meet_minimum: bool

    @property
    def accepted(self) -> bool:
        return self.monthly_within_range and self.term_within_limit and self.donors_meet_minimum


@dataclass(frozen=True, slots=True)
class Proposal:
    id: UUID
    project_id: UUID
    synagogue_id: UUID
    dedication_id: UUID
    author_id: UUID
    monthly_amount: Decimal
    months: int
    donor_count: int
    currency: str
    status: ProposalStatus
    financed_total: Decimal | None
    created_at: datetime


def default_settings(project: Project) -> CalculatorSettings:
    return CalculatorSettings(
        project_id=project.id,
        synagogue_id=project.synagogue_id,
        min_monthly=Decimal("60.00"),
        max_monthly=Decimal("200.00"),
        max_months=96,
        min_per_donor=Decimal("7000.00"),
        max_per_donor=Decimal("150000.00"),
        min_donors=10,
        currency=_CURRENCY,
    )


def require_settings(project: Project, bounds: SettingsBounds) -> CalculatorSettings:
    monthly = _ordered_money(bounds.min_monthly, bounds.max_monthly, "monthly amount")
    per_donor = _ordered_money(bounds.min_per_donor, bounds.max_per_donor, "amount per donor")
    return CalculatorSettings(
        project_id=project.id,
        synagogue_id=project.synagogue_id,
        min_monthly=monthly[0],
        max_monthly=monthly[1],
        max_months=_require_count(bounds.max_months, "Maximum term"),
        min_per_donor=per_donor[0],
        max_per_donor=per_donor[1],
        min_donors=_require_count(bounds.min_donors, "Minimum donor count"),
        currency=_CURRENCY,
    )


def prepare_simulation(draft: SimulationDraft) -> PreparedSimulation:
    return PreparedSimulation(
        dedication_id=draft.dedication_id,
        monthly_amount=require_money(draft.monthly_amount, "Monthly amount"),
        months=_require_count(draft.months, "Term"),
        donor_count=_require_count(draft.donor_count, "Donor count"),
    )


def evaluate(settings: CalculatorSettings, simulation: PreparedSimulation) -> RangeCheck:
    return RangeCheck(
        monthly_within_range=_between(simulation.monthly_amount, settings.min_monthly, settings.max_monthly),
        term_within_limit=simulation.months <= settings.max_months,
        donors_meet_minimum=simulation.donor_count >= settings.min_donors,
    )


def _ordered_money(low: Decimal, high: Decimal, label: str) -> tuple[Decimal, Decimal]:
    minimum = require_money(low, f"Minimum {label}")
    maximum = require_money(high, f"Maximum {label}")
    if maximum < minimum:
        raise ValidationError(f"Maximum {label} must be at least the minimum")
    return minimum, maximum


def _require_count(value: int, field_name: str) -> int:
    if value < 1:
        raise ValidationError(f"{field_name} must be at least one")
    return value


def _between(value: Decimal, low: Decimal, high: Decimal) -> bool:
    return low <= value <= high

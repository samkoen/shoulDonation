"""Domain records. Persistence details stay outside this module."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.plan_marker import PlanMarker
from shoul_donation.domain.plan_region import PlanRegion
from shoul_donation.domain.role import Role


@dataclass(frozen=True, slots=True)
class Synagogue:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class UserAccount:
    id: UUID
    email: str
    password_hash: str


@dataclass(frozen=True, slots=True)
class Membership:
    id: UUID
    user_id: UUID
    synagogue_id: UUID | None
    role: Role


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    synagogue_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ProjectAssignment:
    id: UUID
    synagogue_id: UUID
    project_id: UUID
    user_id: UUID


@dataclass(frozen=True, slots=True)
class ConstructionBudget:
    project_id: UUID
    synagogue_id: UUID
    construction_cost: Decimal
    target_percent: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class BudgetSummary:
    budget: ConstructionBudget
    target_amount: Decimal
    dedications_total: Decimal
    gap: Decimal


@dataclass(frozen=True, slots=True)
class ProjectMember:
    user_id: UUID
    email: str


@dataclass(frozen=True, slots=True)
class Dedication:
    id: UUID
    project_id: UUID
    synagogue_id: UUID
    name: str
    price: Decimal
    status: DedicationStatus
    marker: PlanMarker | None = None
    region: PlanRegion | None = None

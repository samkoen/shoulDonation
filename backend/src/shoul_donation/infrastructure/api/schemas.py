"""HTTP contracts. These shapes are the only data the frontend receives."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from shoul_donation.domain.dedication_status import DedicationStatus
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.lead_status import LeadStatus
from shoul_donation.domain.proposal_status import ProposalStatus
from shoul_donation.domain.role import Role


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID
    role: Role
    synagogue_id: UUID | None


class SynagogueRequest(BaseModel):
    name: str


class SynagogueResponse(BaseModel):
    id: UUID
    name: str


class UserRequest(BaseModel):
    email: str
    password: str
    role: Role
    synagogue_id: UUID | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: Role
    synagogue_id: UUID | None


class ProjectRequest(BaseModel):
    synagogue_id: UUID
    name: str


class ProjectResponse(BaseModel):
    id: UUID
    synagogue_id: UUID
    name: str


class AssignmentRequest(BaseModel):
    user_id: UUID


class AssignmentResponse(BaseModel):
    id: UUID
    synagogue_id: UUID
    project_id: UUID
    user_id: UUID


class BudgetRequest(BaseModel):
    construction_cost: Decimal
    target_percent: Decimal


class BudgetResponse(BaseModel):
    project_id: UUID
    construction_cost: str
    target_percent: str
    currency: str
    target_amount: str
    dedications_total: str
    gap: str


class DedicationRequest(BaseModel):
    name: str
    price: Decimal


class DedicationUpdateRequest(BaseModel):
    price: Decimal | None = None
    status: DedicationStatus | None = None


class PlanVertexResponse(BaseModel):
    x: str
    y: str


class PlanRegionResponse(BaseModel):
    kind: str
    width: str
    strokes: list[list[PlanVertexResponse]]


class PlanVertexRequest(BaseModel):
    x: Decimal
    y: Decimal


class PlanRegionRequest(BaseModel):
    kind: str = "brush"
    width: Decimal
    strokes: list[list[PlanVertexRequest]]


class DedicationResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    price: str
    status: DedicationStatus
    plan_x: str | None
    plan_y: str | None
    plan_region: PlanRegionResponse | None


class MarkerRequest(BaseModel):
    x: Decimal
    y: Decimal


class PriceWeightRequest(BaseModel):
    dedication_id: UUID
    weight: Decimal


class PricingRequest(BaseModel):
    items: list[PriceWeightRequest]


class PriceSuggestionResponse(BaseModel):
    dedication_id: UUID
    name: str
    current_price: str
    suggested_price: str


class PricingPreviewResponse(BaseModel):
    target_amount: str
    amount_to_split: str
    items: list[PriceSuggestionResponse]


class CalculatorSettingsRequest(BaseModel):
    min_monthly: Decimal
    max_monthly: Decimal
    max_months: int
    min_per_donor: Decimal
    max_per_donor: Decimal
    min_donors: int


class CalculatorSettingsResponse(BaseModel):
    project_id: UUID
    min_monthly: str
    max_monthly: str
    max_months: int
    min_per_donor: str
    max_per_donor: str
    min_donors: int
    currency: str


class SimulationRequest(BaseModel):
    dedication_id: UUID
    monthly_amount: Decimal
    months: int
    donor_count: int


class SimulationResponse(BaseModel):
    dedication_id: UUID
    monthly_amount: str
    months: int
    donor_count: int
    monthly_within_range: bool
    term_within_limit: bool
    donors_meet_minimum: bool
    financed_total: str | None
    status: ProposalStatus


class ProposalResponse(BaseModel):
    id: UUID
    dedication_id: UUID
    monthly_amount: str
    months: int
    donor_count: int
    currency: str
    financed_total: str | None
    status: ProposalStatus
    created_at: datetime


class AssigneeResponse(BaseModel):
    user_id: UUID
    email: str


class DonorLeadRequest(BaseModel):
    name: str
    phone: str
    dedication_id: UUID | None = None
    assignee_id: UUID | None = None


class CustomerLeadRequest(BaseModel):
    name: str
    phone: str
    requested_synagogue_name: str


class LeadUpdateRequest(BaseModel):
    status: LeadStatus | None = None
    assignee_id: UUID | None = None


class LeadResponse(BaseModel):
    id: UUID
    kind: LeadKind
    name: str
    phone: str
    status: LeadStatus
    project_id: UUID | None
    dedication_id: UUID | None
    assignee_id: UUID | None
    requested_synagogue_name: str | None


class PublicPageRequest(BaseModel):
    slug: str
    vision: str = ""
    enabled: bool = False


class PublicPageResponse(BaseModel):
    project_id: UUID
    slug: str
    vision: str
    enabled: bool


class GalleryImageResponse(BaseModel):
    id: UUID


class PublicDedicationResponse(BaseModel):
    id: UUID
    name: str
    price: str
    status: DedicationStatus
    plan_x: str | None
    plan_y: str | None
    plan_region: PlanRegionResponse | None


class PublicProjectResponse(BaseModel):
    slug: str
    project_name: str
    synagogue_name: str
    vision: str
    currency: str
    has_plan: bool
    gallery_image_ids: list[UUID]
    dedications: list[PublicDedicationResponse]


class PublicContactRequest(BaseModel):
    name: str
    phone: str
    synagogue_name: str


class MeetingRequest(BaseModel):
    scheduled_at: datetime
    note: str = ""
    close_chance: Decimal | None = None


class MeetingResponse(BaseModel):
    id: UUID
    lead_id: UUID
    scheduled_at: datetime
    note: str
    close_chance: str | None


class ContractorRequest(BaseModel):
    name: str
    phone: str
    amount: Decimal


class ContractorResponse(BaseModel):
    dedication_id: UUID
    name: str
    phone: str
    amount: str

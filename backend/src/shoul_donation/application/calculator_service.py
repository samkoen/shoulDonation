"""Calculator settings, range checks, and a digital proposal without a charge."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from shoul_donation.application.financing import FinancingCalculator, PendingRateTable
from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_set_project_prices, assert_can_view_project
from shoul_donation.domain.calculator import (
    CalculatorSettings,
    PreparedSimulation,
    Proposal,
    RangeCheck,
    SettingsBounds,
    SimulationDraft,
    SimulationView,
    default_settings,
    evaluate,
    prepare_simulation,
    require_settings,
)
from shoul_donation.domain.entities import Project
from shoul_donation.domain.errors import NotFoundError, ValidationError
from shoul_donation.domain.proposal_status import ProposalStatus


class CalculatorService:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        financing: FinancingCalculator | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._financing = financing if financing is not None else PendingRateTable()

    def get_settings(self, actor: Actor, project_id: UUID) -> CalculatorSettings:
        return self._settings(self._visible_project(actor, project_id))

    def save_settings(self, actor: Actor, project_id: UUID, bounds: SettingsBounds) -> CalculatorSettings:
        project = self._visible_project(actor, project_id)
        assert_can_set_project_prices(actor, project.synagogue_id)
        settings = require_settings(project, bounds)
        self._unit_of_work.calculator_settings.save(settings)
        self._unit_of_work.commit()
        return settings

    def preview(self, actor: Actor, project_id: UUID, draft: SimulationDraft) -> SimulationView:
        _project, prepared, check = self._checked(actor, project_id, draft)
        return self._view(prepared, check)

    def create_proposal(self, actor: Actor, project_id: UUID, draft: SimulationDraft) -> Proposal:
        project, prepared, check = self._checked(actor, project_id, draft)
        if not check.accepted:
            raise ValidationError("The simulation is outside the project limits")
        proposal = self._proposal(project, actor, prepared)
        self._unit_of_work.proposals.add(proposal)
        self._unit_of_work.commit()
        return proposal

    def list_proposals(self, actor: Actor, project_id: UUID) -> list[Proposal]:
        project = self._visible_project(actor, project_id)
        return self._unit_of_work.proposals.list_for_project(project.id)

    def update_proposal(self, actor: Actor, proposal_id: UUID, draft: SimulationDraft) -> Proposal:
        current = self._visible_proposal(actor, proposal_id)
        _project, prepared, check = self._checked(actor, current.project_id, draft)
        if not check.accepted:
            raise ValidationError("The simulation is outside the project limits")
        updated = self._revised(current, prepared)
        self._unit_of_work.proposals.save(updated)
        self._unit_of_work.commit()
        return updated

    def delete_proposal(self, actor: Actor, proposal_id: UUID) -> None:
        current = self._visible_proposal(actor, proposal_id)
        self._unit_of_work.proposals.delete(current.id)
        self._unit_of_work.commit()

    def _checked(
        self,
        actor: Actor,
        project_id: UUID,
        draft: SimulationDraft,
    ) -> tuple[Project, PreparedSimulation, RangeCheck]:
        project = self._visible_project(actor, project_id)
        prepared = self._for_project(project, draft)
        return project, prepared, evaluate(self._settings(project), prepared)

    def _view(self, prepared: PreparedSimulation, check: RangeCheck) -> SimulationView:
        return SimulationView(
            simulation=prepared,
            monthly_within_range=check.monthly_within_range,
            term_within_limit=check.term_within_limit,
            donors_meet_minimum=check.donors_meet_minimum,
            financed_total=self._financed_total(prepared),
            status=ProposalStatus.AWAITING_RATE_TABLE,
        )

    def _settings(self, project: Project) -> CalculatorSettings:
        stored = self._unit_of_work.calculator_settings.get(project.id)
        return stored if stored is not None else default_settings(project)

    def _for_project(self, project: Project, draft: SimulationDraft) -> PreparedSimulation:
        prepared = prepare_simulation(draft)
        dedication = self._unit_of_work.dedications.get(prepared.dedication_id)
        if dedication is None or dedication.project_id != project.id:
            raise NotFoundError("Dedication was not found")
        return prepared

    def _proposal(self, project: Project, actor: Actor, prepared: PreparedSimulation) -> Proposal:
        return Proposal(
            id=uuid4(),
            project_id=project.id,
            synagogue_id=project.synagogue_id,
            dedication_id=prepared.dedication_id,
            author_id=actor.user_id,
            monthly_amount=prepared.monthly_amount,
            months=prepared.months,
            donor_count=prepared.donor_count,
            currency=self._settings(project).currency,
            status=ProposalStatus.AWAITING_RATE_TABLE,
            financed_total=self._financed_total(prepared),
            created_at=datetime.now(UTC),
        )

    def _revised(self, current: Proposal, prepared: PreparedSimulation) -> Proposal:
        return replace(
            current,
            dedication_id=prepared.dedication_id,
            monthly_amount=prepared.monthly_amount,
            months=prepared.months,
            donor_count=prepared.donor_count,
            financed_total=self._financed_total(prepared),
        )

    def _visible_proposal(self, actor: Actor, proposal_id: UUID) -> Proposal:
        proposal = self._unit_of_work.proposals.get(proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal was not found")
        self._visible_project(actor, proposal.project_id)
        return proposal

    def _financed_total(self, prepared: PreparedSimulation) -> Decimal | None:
        return self._financing.total_for(prepared.monthly_amount, prepared.months)

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

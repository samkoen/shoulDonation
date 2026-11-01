"""Calculator settings and proposal persistence."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.calculator import CalculatorSettings, Proposal
from shoul_donation.domain.proposal_status import ProposalStatus
from shoul_donation.infrastructure.orm import CalculatorSettingsRow, ProposalRow


def _amount(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


class SqlAlchemyCalculatorSettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: UUID) -> CalculatorSettings | None:
        row = self._session.get(CalculatorSettingsRow, str(project_id))
        return None if row is None else self._settings(row)

    def save(self, settings: CalculatorSettings) -> None:
        row = self._session.get(CalculatorSettingsRow, str(settings.project_id))
        if row is None:
            self._session.add(self._new_row(settings))
            return
        self._copy(row, settings)

    def _new_row(self, settings: CalculatorSettings) -> CalculatorSettingsRow:
        return CalculatorSettingsRow(
            project_id=str(settings.project_id),
            synagogue_id=str(settings.synagogue_id),
            min_monthly=settings.min_monthly,
            max_monthly=settings.max_monthly,
            max_months=settings.max_months,
            min_per_donor=settings.min_per_donor,
            max_per_donor=settings.max_per_donor,
            min_donors=settings.min_donors,
            currency=settings.currency,
        )

    def _copy(self, row: CalculatorSettingsRow, settings: CalculatorSettings) -> None:
        row.min_monthly = settings.min_monthly
        row.max_monthly = settings.max_monthly
        row.max_months = settings.max_months
        row.min_per_donor = settings.min_per_donor
        row.max_per_donor = settings.max_per_donor
        row.min_donors = settings.min_donors
        row.currency = settings.currency

    def _settings(self, row: CalculatorSettingsRow) -> CalculatorSettings:
        return CalculatorSettings(
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            min_monthly=_amount(row.min_monthly),
            max_monthly=_amount(row.max_monthly),
            max_months=row.max_months,
            min_per_donor=_amount(row.min_per_donor),
            max_per_donor=_amount(row.max_per_donor),
            min_donors=row.min_donors,
            currency=row.currency,
        )


class SqlAlchemyProposalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, proposal: Proposal) -> None:
        self._session.add(_proposal_row(proposal))

    def save(self, proposal: Proposal) -> None:
        row = self._session.get(ProposalRow, str(proposal.id))
        if row is None:
            self.add(proposal)
            return
        _copy_proposal(row, proposal)

    def get(self, proposal_id: UUID) -> Proposal | None:
        row = self._session.get(ProposalRow, str(proposal_id))
        return None if row is None else _proposal(row)

    def delete(self, proposal_id: UUID) -> None:
        row = self._session.get(ProposalRow, str(proposal_id))
        if row is not None:
            self._session.delete(row)

    def list_for_project(self, project_id: UUID) -> list[Proposal]:
        statement = (
            select(ProposalRow)
            .where(ProposalRow.project_id == str(project_id))
            .order_by(ProposalRow.created_at.desc())
        )
        return [_proposal(row) for row in self._session.scalars(statement)]


def _copy_proposal(row: ProposalRow, proposal: Proposal) -> None:
    row.dedication_id = str(proposal.dedication_id)
    row.monthly_amount = proposal.monthly_amount
    row.months = proposal.months
    row.donor_count = proposal.donor_count
    row.financed_total = proposal.financed_total


def _proposal_row(proposal: Proposal) -> ProposalRow:
    return ProposalRow(
        id=str(proposal.id),
        project_id=str(proposal.project_id),
        synagogue_id=str(proposal.synagogue_id),
        dedication_id=str(proposal.dedication_id),
        author_id=str(proposal.author_id),
        monthly_amount=proposal.monthly_amount,
        months=proposal.months,
        donor_count=proposal.donor_count,
        currency=proposal.currency,
        status=proposal.status.value,
        financed_total=proposal.financed_total,
        created_at=proposal.created_at,
    )


def _proposal(row: ProposalRow) -> Proposal:
    return Proposal(
        id=UUID(row.id),
        project_id=UUID(row.project_id),
        synagogue_id=UUID(row.synagogue_id),
        dedication_id=UUID(row.dedication_id),
        author_id=UUID(row.author_id),
        monthly_amount=_amount(row.monthly_amount),
        months=row.months,
        donor_count=row.donor_count,
        currency=row.currency,
        status=ProposalStatus(row.status),
        financed_total=None if row.financed_total is None else _amount(row.financed_total),
        created_at=_aware(row.created_at),
    )


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        from datetime import UTC

        return value.replace(tzinfo=UTC)
    return value

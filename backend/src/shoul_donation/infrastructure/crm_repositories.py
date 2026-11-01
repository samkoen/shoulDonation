"""Lead and meeting persistence."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.crm import Lead, Meeting
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.lead_status import LeadStatus
from shoul_donation.infrastructure.orm import LeadRow, MeetingRow


class SqlAlchemyLeadRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, lead: Lead) -> None:
        self._session.add(_lead_row(lead))

    def save(self, lead: Lead) -> None:
        row = self._session.get(LeadRow, str(lead.id))
        if row is None:
            self.add(lead)
            return
        row.status = lead.status.value
        row.assignee_id = None if lead.assignee_id is None else str(lead.assignee_id)
        row.name = lead.name
        row.phone = lead.phone

    def get(self, lead_id: UUID) -> Lead | None:
        row = self._session.get(LeadRow, str(lead_id))
        return None if row is None else _lead(row)

    def list_for_project(self, project_id: UUID) -> list[Lead]:
        statement = select(LeadRow).where(LeadRow.project_id == str(project_id)).order_by(LeadRow.name)
        return [_lead(row) for row in self._session.scalars(statement)]

    def list_by_kind(self, kind: LeadKind) -> list[Lead]:
        statement = select(LeadRow).where(LeadRow.kind == kind.value).order_by(LeadRow.name)
        return [_lead(row) for row in self._session.scalars(statement)]


class SqlAlchemyMeetingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, meeting: Meeting) -> None:
        self._session.add(_meeting_row(meeting))

    def list_for_lead(self, lead_id: UUID) -> list[Meeting]:
        statement = (
            select(MeetingRow)
            .where(MeetingRow.lead_id == str(lead_id))
            .order_by(MeetingRow.scheduled_at.desc())
        )
        return [_meeting(row) for row in self._session.scalars(statement)]


def _lead_row(lead: Lead) -> LeadRow:
    return LeadRow(
        id=str(lead.id),
        kind=lead.kind.value,
        name=lead.name,
        phone=lead.phone,
        status=lead.status.value,
        synagogue_id=None if lead.synagogue_id is None else str(lead.synagogue_id),
        project_id=None if lead.project_id is None else str(lead.project_id),
        dedication_id=None if lead.dedication_id is None else str(lead.dedication_id),
        assignee_id=None if lead.assignee_id is None else str(lead.assignee_id),
        requested_synagogue_name=lead.requested_synagogue_name,
    )


def _lead(row: LeadRow) -> Lead:
    return Lead(
        id=UUID(row.id),
        kind=LeadKind(row.kind),
        name=row.name,
        phone=row.phone,
        status=LeadStatus(row.status),
        synagogue_id=None if row.synagogue_id is None else UUID(row.synagogue_id),
        project_id=None if row.project_id is None else UUID(row.project_id),
        dedication_id=None if row.dedication_id is None else UUID(row.dedication_id),
        assignee_id=None if row.assignee_id is None else UUID(row.assignee_id),
        requested_synagogue_name=row.requested_synagogue_name,
    )


def _meeting_row(meeting: Meeting) -> MeetingRow:
    return MeetingRow(
        id=str(meeting.id),
        lead_id=str(meeting.lead_id),
        scheduled_at=meeting.scheduled_at,
        note=meeting.note,
        close_chance=meeting.close_chance,
    )


def _meeting(row: MeetingRow) -> Meeting:
    return Meeting(
        id=UUID(row.id),
        lead_id=UUID(row.lead_id),
        scheduled_at=_aware(row.scheduled_at),
        note=row.note,
        close_chance=None if row.close_chance is None else Decimal(str(row.close_chance)).quantize(Decimal("1")),
    )


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value

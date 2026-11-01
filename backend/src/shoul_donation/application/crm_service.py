"""Donor leads, new-synagogue inquiries, and their meetings."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import (
    assert_assignee_is_sub_projector,
    assert_can_assign,
    assert_can_view_project,
    assert_platform_admin,
)
from shoul_donation.domain.crm import Lead, Meeting, new_customer_lead, require_meeting_time
from shoul_donation.domain.entities import Project
from shoul_donation.domain.errors import ForbiddenError, NotFoundError, ValidationError
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.lead_status import LeadStatus
from shoul_donation.domain.role import Role
from shoul_donation.domain.money import require_close_chance
from shoul_donation.domain.validation import require_name, require_note, require_phone


class CrmService:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def add_donor_lead(
        self,
        actor: Actor,
        project_id: UUID,
        name: str,
        phone: str,
        dedication_id: UUID | None,
        assignee_id: UUID | None,
    ) -> Lead:
        project = self._visible_project(actor, project_id)
        self._dedication_belongs(project, dedication_id)
        lead = self._donor(actor, project, name, phone, dedication_id, assignee_id)
        self._unit_of_work.leads.add(lead)
        self._unit_of_work.commit()
        return lead

    def list_donor_leads(self, actor: Actor, project_id: UUID) -> list[Lead]:
        project = self._visible_project(actor, project_id)
        leads = self._unit_of_work.leads.list_for_project(project.id)
        if actor.role is Role.SUB_PROJECTOR:
            return [lead for lead in leads if lead.assignee_id == actor.user_id]
        return leads

    def add_customer_lead(self, actor: Actor, name: str, phone: str, requested_synagogue_name: str) -> Lead:
        assert_platform_admin(actor)
        lead = new_customer_lead(name, phone, requested_synagogue_name)
        self._unit_of_work.leads.add(lead)
        self._unit_of_work.commit()
        return lead

    def list_customer_leads(self, actor: Actor) -> list[Lead]:
        assert_platform_admin(actor)
        return self._unit_of_work.leads.list_by_kind(LeadKind.SYNAGOGUE_CUSTOMER)

    def update_lead(
        self,
        actor: Actor,
        lead_id: UUID,
        status: LeadStatus | None,
        assignee_id: UUID | None,
    ) -> Lead:
        lead = self._visible_lead(actor, lead_id)
        updated = self._apply(actor, lead, status, assignee_id)
        self._unit_of_work.leads.save(updated)
        self._unit_of_work.commit()
        return updated

    def add_meeting(
        self,
        actor: Actor,
        lead_id: UUID,
        scheduled_at: datetime,
        note: str,
        close_chance: Decimal | None = None,
    ) -> Meeting:
        lead = self._visible_lead(actor, lead_id)
        meeting = self._meeting(lead.id, scheduled_at, note, close_chance)
        self._unit_of_work.meetings.add(meeting)
        self._unit_of_work.commit()
        return meeting

    def list_meetings(self, actor: Actor, lead_id: UUID) -> list[Meeting]:
        lead = self._visible_lead(actor, lead_id)
        return self._unit_of_work.meetings.list_for_lead(lead.id)

    def _donor(
        self,
        actor: Actor,
        project: Project,
        name: str,
        phone: str,
        dedication_id: UUID | None,
        assignee_id: UUID | None,
    ) -> Lead:
        return Lead(
            id=uuid4(),
            kind=LeadKind.DONOR,
            name=require_name(name, "Lead name"),
            phone=require_phone(phone),
            status=LeadStatus.NEW,
            synagogue_id=project.synagogue_id,
            project_id=project.id,
            dedication_id=dedication_id,
            assignee_id=self._donor_assignee(actor, project, assignee_id),
            requested_synagogue_name=None,
        )

    def _apply(
        self,
        actor: Actor,
        lead: Lead,
        status: LeadStatus | None,
        assignee_id: UUID | None,
    ) -> Lead:
        if status is None and assignee_id is None:
            raise ValidationError("Nothing to update")
        updated = lead
        if assignee_id is not None:
            updated = replace(updated, assignee_id=self._reassign(actor, lead, assignee_id))
        if status is not None:
            updated = replace(updated, status=status)
        return updated

    def _donor_assignee(self, actor: Actor, project: Project, assignee_id: UUID | None) -> UUID | None:
        if actor.role is Role.SUB_PROJECTOR:
            return actor.user_id
        if assignee_id is None:
            return None
        return self._checked_assignee(project, assignee_id)

    def _reassign(self, actor: Actor, lead: Lead, assignee_id: UUID) -> UUID:
        if lead.kind is not LeadKind.DONOR or lead.synagogue_id is None or lead.project_id is None:
            raise ValidationError("Only a donor lead can be assigned")
        assert_can_assign(actor, lead.synagogue_id)
        return self._checked_assignee(self._require_project(lead.project_id), assignee_id)

    def _checked_assignee(self, project: Project, assignee_id: UUID) -> UUID:
        membership = self._unit_of_work.memberships.get_for_user(assignee_id)
        assert_assignee_is_sub_projector(membership, project.synagogue_id)
        if not self._unit_of_work.assignments.exists(project.id, assignee_id):
            raise ValidationError("The assignee must be assigned to this project")
        return assignee_id

    def _meeting(
        self,
        lead_id: UUID,
        scheduled_at: datetime,
        note: str,
        close_chance: Decimal | None,
    ) -> Meeting:
        return Meeting(
            id=uuid4(),
            lead_id=lead_id,
            scheduled_at=require_meeting_time(scheduled_at),
            note=require_note(note),
            close_chance=require_close_chance(close_chance),
        )

    def _dedication_belongs(self, project: Project, dedication_id: UUID | None) -> None:
        if dedication_id is None:
            return
        dedication = self._unit_of_work.dedications.get(dedication_id)
        if dedication is None or dedication.project_id != project.id:
            raise NotFoundError("Dedication was not found")

    def _visible_lead(self, actor: Actor, lead_id: UUID) -> Lead:
        lead = self._require_lead(lead_id)
        if lead.kind is LeadKind.SYNAGOGUE_CUSTOMER:
            assert_platform_admin(actor)
            return lead
        return self._visible_donor(actor, lead)

    def _visible_donor(self, actor: Actor, lead: Lead) -> Lead:
        if lead.project_id is None:
            raise NotFoundError("Lead was not found")
        self._visible_project(actor, lead.project_id)
        if actor.role is Role.SUB_PROJECTOR and lead.assignee_id != actor.user_id:
            raise ForbiddenError("You can only see leads assigned to you")
        return lead

    def _visible_project(self, actor: Actor, project_id: UUID) -> Project:
        project = self._require_project(project_id)
        assigned = self._unit_of_work.assignments.exists(project_id, actor.user_id)
        assert_can_view_project(actor, project.synagogue_id, assigned)
        return project

    def _require_project(self, project_id: UUID) -> Project:
        project = self._unit_of_work.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project was not found")
        return project

    def _require_lead(self, lead_id: UUID) -> Lead:
        lead = self._unit_of_work.leads.get(lead_id)
        if lead is None:
            raise NotFoundError("Lead was not found")
        return lead

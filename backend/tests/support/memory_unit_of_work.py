"""In-memory unit of work for service tests. It implements the same ports as SQLite."""

from uuid import UUID

from shoul_donation.domain.calculator import CalculatorSettings, Proposal
from shoul_donation.domain.contractor import Contractor
from shoul_donation.domain.crm import Lead, Meeting
from shoul_donation.domain.lead_kind import LeadKind
from shoul_donation.domain.plan import ProjectPlan
from shoul_donation.domain.public_page import GalleryImage, PublicPage
from shoul_donation.domain.entities import (
    ConstructionBudget,
    Dedication,
    Membership,
    Project,
    ProjectAssignment,
    Synagogue,
    UserAccount,
)


class MemoryUnitOfWork:
    def __init__(self) -> None:
        self.synagogues_by_id: dict[UUID, Synagogue] = {}
        self.users_by_id: dict[UUID, UserAccount] = {}
        self.users_by_email: dict[str, UserAccount] = {}
        self.memberships_by_user: dict[UUID, Membership] = {}
        self.projects_by_id: dict[UUID, Project] = {}
        self.assignment_rows: list[ProjectAssignment] = []
        self.budgets_by_project: dict[UUID, ConstructionBudget] = {}
        self.dedications_by_id: dict[UUID, Dedication] = {}
        self.settings_by_project: dict[UUID, CalculatorSettings] = {}
        self.proposals_by_id: dict[UUID, Proposal] = {}
        self.leads_by_id: dict[UUID, Lead] = {}
        self.meetings_by_id: dict[UUID, Meeting] = {}
        self.plans_by_project: dict[UUID, ProjectPlan] = {}
        self.public_pages_by_project: dict[UUID, PublicPage] = {}
        self.gallery_by_id: dict[UUID, GalleryImage] = {}
        self.contractors_by_dedication: dict[UUID, Contractor] = {}
        self.synagogues = _SynagogueRepository(self)
        self.users = _UserRepository(self)
        self.memberships = _MembershipRepository(self)
        self.projects = _ProjectRepository(self)
        self.assignments = _AssignmentRepository(self)
        self.budgets = _BudgetRepository(self)
        self.dedications = _DedicationRepository(self)
        self.calculator_settings = _CalculatorSettingsRepository(self)
        self.proposals = _ProposalRepository(self)
        self.leads = _LeadRepository(self)
        self.meetings = _MeetingRepository(self)
        self.plans = _PlanRepository(self)
        self.public_pages = _PublicPageRepository(self)
        self.gallery = _GalleryRepository(self)
        self.contractors = _ContractorRepository(self)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class _SynagogueRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, synagogue: Synagogue) -> None:
        self._store.synagogues_by_id[synagogue.id] = synagogue

    def get(self, synagogue_id: UUID) -> Synagogue | None:
        return self._store.synagogues_by_id.get(synagogue_id)

    def get_by_name(self, name: str) -> Synagogue | None:
        return next((item for item in self._store.synagogues_by_id.values() if item.name == name), None)

    def list_all(self) -> list[Synagogue]:
        return sorted(self._store.synagogues_by_id.values(), key=lambda item: item.name)


class _UserRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, user: UserAccount) -> None:
        self._store.users_by_id[user.id] = user
        self._store.users_by_email[user.email] = user

    def get(self, user_id: UUID) -> UserAccount | None:
        return self._store.users_by_id.get(user_id)

    def get_by_email(self, email: str) -> UserAccount | None:
        return self._store.users_by_email.get(email)


class _MembershipRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, membership: Membership) -> None:
        self._store.memberships_by_user[membership.user_id] = membership

    def get_for_user(self, user_id: UUID) -> Membership | None:
        return self._store.memberships_by_user.get(user_id)


class _ProjectRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, project: Project) -> None:
        self._store.projects_by_id[project.id] = project

    def get(self, project_id: UUID) -> Project | None:
        return self._store.projects_by_id.get(project_id)

    def get_by_name(self, synagogue_id: UUID, name: str) -> Project | None:
        return next(self._matching_name(synagogue_id, name), None)

    def list_all(self) -> list[Project]:
        return sorted(self._store.projects_by_id.values(), key=lambda item: item.name)

    def list_for_synagogue(self, synagogue_id: UUID) -> list[Project]:
        projects = [item for item in self._store.projects_by_id.values() if item.synagogue_id == synagogue_id]
        return sorted(projects, key=lambda item: item.name)

    def list_assigned_to(self, user_id: UUID) -> list[Project]:
        project_ids = {item.project_id for item in self._store.assignment_rows if item.user_id == user_id}
        projects = [self._store.projects_by_id[project_id] for project_id in project_ids]
        return sorted(projects, key=lambda item: item.name)

    def _matching_name(self, synagogue_id: UUID, name: str):
        for project in self._store.projects_by_id.values():
            if project.synagogue_id == synagogue_id and project.name == name:
                yield project


class _AssignmentRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, assignment: ProjectAssignment) -> None:
        self._store.assignment_rows.append(assignment)

    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        return any(
            item.project_id == project_id and item.user_id == user_id for item in self._store.assignment_rows
        )

    def list_for_project(self, project_id: UUID) -> list[ProjectAssignment]:
        return [item for item in self._store.assignment_rows if item.project_id == project_id]


class _BudgetRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def get(self, project_id: UUID) -> ConstructionBudget | None:
        return self._store.budgets_by_project.get(project_id)

    def save(self, budget: ConstructionBudget) -> None:
        self._store.budgets_by_project[budget.project_id] = budget


class _DedicationRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, dedication: Dedication) -> None:
        self._store.dedications_by_id[dedication.id] = dedication

    def save(self, dedication: Dedication) -> None:
        self._store.dedications_by_id[dedication.id] = dedication

    def get(self, dedication_id: UUID) -> Dedication | None:
        return self._store.dedications_by_id.get(dedication_id)

    def get_by_name(self, project_id: UUID, name: str) -> Dedication | None:
        return next(self._named(project_id, name), None)

    def list_for_project(self, project_id: UUID) -> list[Dedication]:
        rows = [item for item in self._store.dedications_by_id.values() if item.project_id == project_id]
        return sorted(rows, key=lambda item: item.name)

    def _named(self, project_id: UUID, name: str):
        for dedication in self._store.dedications_by_id.values():
            if dedication.project_id == project_id and dedication.name == name:
                yield dedication


class _CalculatorSettingsRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def get(self, project_id: UUID) -> CalculatorSettings | None:
        return self._store.settings_by_project.get(project_id)

    def save(self, settings: CalculatorSettings) -> None:
        self._store.settings_by_project[settings.project_id] = settings


class _ProposalRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, proposal: Proposal) -> None:
        self._store.proposals_by_id[proposal.id] = proposal

    def save(self, proposal: Proposal) -> None:
        self._store.proposals_by_id[proposal.id] = proposal

    def get(self, proposal_id: UUID) -> Proposal | None:
        return self._store.proposals_by_id.get(proposal_id)

    def delete(self, proposal_id: UUID) -> None:
        self._store.proposals_by_id.pop(proposal_id, None)

    def list_for_project(self, project_id: UUID) -> list[Proposal]:
        rows = [item for item in self._store.proposals_by_id.values() if item.project_id == project_id]
        return sorted(rows, key=lambda item: item.created_at, reverse=True)


class _LeadRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, lead: Lead) -> None:
        self._store.leads_by_id[lead.id] = lead

    def save(self, lead: Lead) -> None:
        self._store.leads_by_id[lead.id] = lead

    def get(self, lead_id: UUID) -> Lead | None:
        return self._store.leads_by_id.get(lead_id)

    def list_for_project(self, project_id: UUID) -> list[Lead]:
        rows = [item for item in self._store.leads_by_id.values() if item.project_id == project_id]
        return sorted(rows, key=lambda item: item.name)

    def list_by_kind(self, kind: LeadKind) -> list[Lead]:
        rows = [item for item in self._store.leads_by_id.values() if item.kind is kind]
        return sorted(rows, key=lambda item: item.name)


class _MeetingRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, meeting: Meeting) -> None:
        self._store.meetings_by_id[meeting.id] = meeting

    def list_for_lead(self, lead_id: UUID) -> list[Meeting]:
        rows = [item for item in self._store.meetings_by_id.values() if item.lead_id == lead_id]
        return sorted(rows, key=lambda item: item.scheduled_at, reverse=True)


class _PlanRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def get(self, project_id: UUID) -> ProjectPlan | None:
        return self._store.plans_by_project.get(project_id)

    def exists(self, project_id: UUID) -> bool:
        return project_id in self._store.plans_by_project

    def save(self, plan: ProjectPlan) -> None:
        self._store.plans_by_project[plan.project_id] = plan


class _PublicPageRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def get(self, project_id: UUID) -> PublicPage | None:
        return self._store.public_pages_by_project.get(project_id)

    def get_by_slug(self, slug: str) -> PublicPage | None:
        return next((item for item in self._store.public_pages_by_project.values() if item.slug == slug), None)

    def save(self, page: PublicPage) -> None:
        self._store.public_pages_by_project[page.project_id] = page


class _GalleryRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def add(self, image: GalleryImage) -> None:
        self._store.gallery_by_id[image.id] = image

    def get(self, image_id: UUID) -> GalleryImage | None:
        return self._store.gallery_by_id.get(image_id)

    def list_ids_for_project(self, project_id: UUID) -> list[UUID]:
        rows = [item for item in self._store.gallery_by_id.values() if item.project_id == project_id]
        return [item.id for item in sorted(rows, key=lambda item: item.position)]

    def delete(self, image_id: UUID) -> None:
        self._store.gallery_by_id.pop(image_id, None)


class _ContractorRepository:
    def __init__(self, store: MemoryUnitOfWork) -> None:
        self._store = store

    def get(self, dedication_id: UUID) -> Contractor | None:
        return self._store.contractors_by_dedication.get(dedication_id)

    def save(self, contractor: Contractor) -> None:
        self._store.contractors_by_dedication[contractor.dedication_id] = contractor

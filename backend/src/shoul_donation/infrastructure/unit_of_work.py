"""One database transaction for a request."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from shoul_donation.domain.errors import ConflictError
from shoul_donation.infrastructure.budget_repositories import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyDedicationRepository,
)
from shoul_donation.infrastructure.calculator_repositories import (
    SqlAlchemyCalculatorSettingsRepository,
    SqlAlchemyProposalRepository,
)
from shoul_donation.infrastructure.contractor_repositories import SqlAlchemyContractorRepository
from shoul_donation.infrastructure.crm_repositories import SqlAlchemyLeadRepository, SqlAlchemyMeetingRepository
from shoul_donation.infrastructure.plan_repositories import SqlAlchemyPlanRepository
from shoul_donation.infrastructure.public_page_repositories import (
    SqlAlchemyGalleryRepository,
    SqlAlchemyPublicPageRepository,
)
from shoul_donation.infrastructure.repositories import (
    SqlAlchemyAssignmentRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemySynagogueRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def open(self) -> None:
        session = self._session_factory()
        self._session = session
        self.synagogues = SqlAlchemySynagogueRepository(session)
        self.users = SqlAlchemyUserRepository(session)
        self.memberships = SqlAlchemyMembershipRepository(session)
        self.projects = SqlAlchemyProjectRepository(session)
        self.assignments = SqlAlchemyAssignmentRepository(session)
        self.budgets = SqlAlchemyBudgetRepository(session)
        self.dedications = SqlAlchemyDedicationRepository(session)
        self.calculator_settings = SqlAlchemyCalculatorSettingsRepository(session)
        self.proposals = SqlAlchemyProposalRepository(session)
        self.leads = SqlAlchemyLeadRepository(session)
        self.meetings = SqlAlchemyMeetingRepository(session)
        self.plans = SqlAlchemyPlanRepository(session)
        self.public_pages = SqlAlchemyPublicPageRepository(session)
        self.gallery = SqlAlchemyGalleryRepository(session)
        self.contractors = SqlAlchemyContractorRepository(session)

    def commit(self) -> None:
        try:
            self._require_session().commit()
        except IntegrityError as error:
            self._require_session().rollback()
            raise ConflictError("This record already exists") from error

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    def _require_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("The unit of work is not open")
        return self._session

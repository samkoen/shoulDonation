"""Building-plan persistence. The image bytes stay in the database."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shoul_donation.domain.plan import ProjectPlan
from shoul_donation.infrastructure.orm import ProjectPlanRow


class SqlAlchemyPlanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: UUID) -> ProjectPlan | None:
        row = self._session.get(ProjectPlanRow, str(project_id))
        return None if row is None else self._plan(row)

    def exists(self, project_id: UUID) -> bool:
        statement = select(ProjectPlanRow.project_id).where(ProjectPlanRow.project_id == str(project_id))
        return self._session.scalar(statement) is not None

    def save(self, plan: ProjectPlan) -> None:
        row = self._session.get(ProjectPlanRow, str(plan.project_id))
        if row is None:
            self._session.add(self._new_row(plan))
            return
        row.content_type = plan.content_type
        row.content = plan.content

    def _new_row(self, plan: ProjectPlan) -> ProjectPlanRow:
        return ProjectPlanRow(
            project_id=str(plan.project_id),
            synagogue_id=str(plan.synagogue_id),
            content_type=plan.content_type,
            content=plan.content,
        )

    def _plan(self, row: ProjectPlanRow) -> ProjectPlan:
        return ProjectPlan(
            project_id=UUID(row.project_id),
            synagogue_id=UUID(row.synagogue_id),
            content_type=row.content_type,
            content=bytes(row.content),
        )

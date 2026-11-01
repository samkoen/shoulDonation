"""Contractor persistence."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from shoul_donation.domain.contractor import Contractor
from shoul_donation.infrastructure.orm import ContractorRow


class SqlAlchemyContractorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, dedication_id: UUID) -> Contractor | None:
        row = self._session.get(ContractorRow, str(dedication_id))
        return None if row is None else self._contractor(row)

    def save(self, contractor: Contractor) -> None:
        row = self._session.get(ContractorRow, str(contractor.dedication_id))
        if row is None:
            self._session.add(self._new_row(contractor))
            return
        row.name = contractor.name
        row.phone = contractor.phone
        row.amount = contractor.amount

    def _new_row(self, contractor: Contractor) -> ContractorRow:
        return ContractorRow(
            dedication_id=str(contractor.dedication_id),
            synagogue_id=str(contractor.synagogue_id),
            project_id=str(contractor.project_id),
            name=contractor.name,
            phone=contractor.phone,
            amount=contractor.amount,
        )

    def _contractor(self, row: ContractorRow) -> Contractor:
        return Contractor(
            dedication_id=UUID(row.dedication_id),
            synagogue_id=UUID(row.synagogue_id),
            project_id=UUID(row.project_id),
            name=row.name,
            phone=row.phone,
            amount=Decimal(str(row.amount)).quantize(Decimal("0.01")),
        )

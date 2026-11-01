"""Request-scoped dependencies."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, Request

from shoul_donation.application.budget_service import BudgetService
from shoul_donation.application.contractor_service import ContractorService
from shoul_donation.application.calculator_service import CalculatorService
from shoul_donation.application.crm_service import CrmService
from shoul_donation.application.identity_service import IdentityService
from shoul_donation.application.plan_service import PlanService
from shoul_donation.application.pricing_service import PricingService
from shoul_donation.application.project_service import ProjectService
from shoul_donation.application.public_page_service import PublicPageService
from shoul_donation.application.public_site_service import PublicSiteService
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import AuthenticationError
from shoul_donation.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work(request: Request) -> Iterator[SqlAlchemyUnitOfWork]:
    unit_of_work = SqlAlchemyUnitOfWork(request.app.state.session_factory)
    unit_of_work.open()
    try:
        yield unit_of_work
    except Exception:
        unit_of_work.rollback()
        raise
    finally:
        unit_of_work.close()


def get_identity_service(
    request: Request,
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> IdentityService:
    return IdentityService(unit_of_work, request.app.state.password_hasher)


def get_project_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> ProjectService:
    return ProjectService(unit_of_work)


def get_contractor_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> ContractorService:
    return ContractorService(unit_of_work)


def get_budget_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> BudgetService:
    return BudgetService(unit_of_work)


def get_calculator_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> CalculatorService:
    return CalculatorService(unit_of_work)


def get_plan_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> PlanService:
    return PlanService(unit_of_work)


def get_pricing_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> PricingService:
    return PricingService(unit_of_work)


def get_public_page_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> PublicPageService:
    return PublicPageService(unit_of_work)


def get_public_site_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> PublicSiteService:
    return PublicSiteService(unit_of_work)


def get_crm_service(
    unit_of_work: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> CrmService:
    return CrmService(unit_of_work)


def get_actor(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Actor:
    return request.app.state.token_issuer.read(_bearer_token(authorization))


def _bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthenticationError("Authentication is required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Authentication is required")
    return token

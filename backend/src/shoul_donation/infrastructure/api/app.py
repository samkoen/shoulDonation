"""FastAPI application. The domain is reached only through application services."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker

from shoul_donation.application.bootstrap_admin import ensure_platform_admin
from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.config import Settings
from shoul_donation.infrastructure.api.errors import register_error_handlers
from shoul_donation.infrastructure.api.frontend_static import mount_frontend
from shoul_donation.infrastructure.api.routes import router
from shoul_donation.infrastructure.api.routes_budget import router as budget_router
from shoul_donation.infrastructure.api.routes_calculator import router as calculator_router
from shoul_donation.infrastructure.api.routes_contractor import router as contractor_router
from shoul_donation.infrastructure.api.routes_crm import router as crm_router
from shoul_donation.infrastructure.api.routes_plan import router as plan_router
from shoul_donation.infrastructure.api.routes_pricing import router as pricing_router
from shoul_donation.infrastructure.api.routes_public import router as public_router
from shoul_donation.infrastructure.token_issuer import TokenIssuer
from shoul_donation.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def create_app(settings: Settings, session_factory: sessionmaker[Session]) -> FastAPI:
    app = FastAPI(title="shoulDonation", lifespan=_lifespan)
    _attach_state(app, settings, session_factory)
    _allow_local_frontend(app)
    register_error_handlers(app)
    app.include_router(router, prefix="/api")
    app.include_router(budget_router, prefix="/api")
    app.include_router(calculator_router, prefix="/api")
    app.include_router(crm_router, prefix="/api")
    app.include_router(contractor_router, prefix="/api")
    app.include_router(plan_router, prefix="/api")
    app.include_router(pricing_router, prefix="/api")
    app.include_router(public_router, prefix="/api")
    mount_frontend(app)
    return app


def _attach_state(app: FastAPI, settings: Settings, session_factory: sessionmaker[Session]) -> None:
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.password_hasher = PasswordHasher(settings.password_iterations)
    app.state.token_issuer = TokenIssuer(settings.jwt_secret, settings.jwt_ttl_minutes)


def _allow_local_frontend(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    _bootstrap_platform_admin(app)
    yield


def _bootstrap_platform_admin(app: FastAPI) -> None:
    settings: Settings = app.state.settings
    if not settings.platform_admin_email or not settings.platform_admin_password:
        return
    unit_of_work = SqlAlchemyUnitOfWork(app.state.session_factory)
    unit_of_work.open()
    try:
        ensure_platform_admin(
            unit_of_work,
            app.state.password_hasher,
            settings.platform_admin_email,
            settings.platform_admin_password,
        )
    finally:
        unit_of_work.close()

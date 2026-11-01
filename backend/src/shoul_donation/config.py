"""Runtime settings. Secrets come from the environment, never from the client."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def default_database_url() -> str:
    repository_root = Path(__file__).resolve().parents[3]
    database_file = repository_root / "data" / "shoul_donation.db"
    return "sqlite:///" + database_file.as_posix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    database_url: str = ""
    jwt_secret: str = "dev-only-change-me-to-a-long-secret"
    jwt_ttl_minutes: int = 720
    password_iterations: int = 120_000
    platform_admin_email: str | None = None
    platform_admin_password: str | None = None

    def resolved_database_url(self) -> str:
        if self.database_url:
            return _sqlalchemy_url(self.database_url)
        return default_database_url()


def _sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url

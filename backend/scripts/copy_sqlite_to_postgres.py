"""Copy the local SQLite catalog onto the configured Postgres database."""

from sqlalchemy import create_engine, select

from shoul_donation.config import Settings, default_database_url
from shoul_donation.infrastructure.migrations import upgrade_to_head
from shoul_donation.infrastructure.orm import Base


def main() -> None:
    settings = Settings()
    postgres_url = settings.resolved_database_url()
    sqlite_url = default_database_url()
    if not postgres_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL is not a Postgres URL")
    upgrade_to_head(postgres_url)
    copied = _copy(sqlite_url, postgres_url)
    for name, count in copied:
        print(f"{name}: {count}")


def _copy(sqlite_url: str, postgres_url: str) -> list[tuple[str, int]]:
    source = create_engine(sqlite_url)
    destination = create_engine(postgres_url, pool_pre_ping=True)
    copied: list[tuple[str, int]] = []
    with source.connect() as incoming, destination.begin() as outgoing:
        for table in reversed(Base.metadata.sorted_tables):
            outgoing.execute(table.delete())
        for table in Base.metadata.sorted_tables:
            rows = [dict(row) for row in incoming.execute(select(table)).mappings()]
            if rows:
                outgoing.execute(table.insert(), rows)
            copied.append((table.name, len(rows)))
    source.dispose()
    destination.dispose()
    return copied


if __name__ == "__main__":
    main()

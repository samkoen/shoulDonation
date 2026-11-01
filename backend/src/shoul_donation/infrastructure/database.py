"""SQLite engine. Foreign keys are off unless each connection turns them on."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def sqlite_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def ensure_sqlite_parent(url: str) -> None:
    path = _sqlite_file(url)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)


def create_engine_from_url(url: str) -> Engine:
    ensure_sqlite_parent(url)
    return create_engine(url, connect_args=_connect_args(url), pool_pre_ping=True)


def session_factory_for(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def _connect_args(url: str) -> dict[str, bool]:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _sqlite_file(url: str) -> Path | None:
    if not url.startswith("sqlite:///") or url.endswith(":memory:"):
        return None
    return Path(url.removeprefix("sqlite:///"))


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
    if dbapi_connection.__class__.__module__ != "sqlite3":
        return
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

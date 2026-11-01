from shoul_donation.config import _sqlalchemy_url


def test_a_neon_url_uses_the_psycopg_driver() -> None:
    raw = "postgresql://owner:secret@ep-example.neon.tech/neondb?sslmode=require"
    assert _sqlalchemy_url(raw).startswith("postgresql+psycopg://owner:secret@")


def test_a_postgres_scheme_is_normalized() -> None:
    assert _sqlalchemy_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"

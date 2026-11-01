"""Process entry point. Binds every interface so the service can run on Render."""

import os

import uvicorn

from shoul_donation.config import Settings
from shoul_donation.infrastructure.api.app import create_app
from shoul_donation.infrastructure.database import create_engine_from_url, session_factory_for
from shoul_donation.infrastructure.migrations import upgrade_to_head


def main() -> None:
    settings = Settings()
    database_url = settings.resolved_database_url()
    upgrade_to_head(database_url)
    engine = create_engine_from_url(database_url)
    app = create_app(settings, session_factory_for(engine))
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()

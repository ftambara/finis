from collections.abc import Generator

import pytest
from pytest_django.plugin import DjangoDbBlocker

_saved_user: str | None = None
_saved_password: str | None = None


@pytest.fixture(scope="session")
def django_db_modify_db_settings() -> None:
    """
    Override the default connection's credentials to use the admin connection's
    credentials during database setup and migrations.
    """
    global _saved_user, _saved_password
    from django.conf import settings

    _saved_user = settings.DATABASES["default"]["USER"]
    _saved_password = settings.DATABASES["default"].get("PASSWORD")

    default_db = settings.DATABASES["default"]
    admin_db = settings.DATABASES["admin"]

    default_db["USER"] = admin_db["USER"]
    default_db["PASSWORD"] = admin_db.get("PASSWORD")


@pytest.fixture(scope="session", autouse=True)
def _restore_db_credentials(
    django_db_setup: Generator[None],
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None]:
    """
    Restore the default connection's credentials to the normal user after
    database setup and migrations are complete, so tests run with proper RLS.
    Then, swap back to admin credentials for teardown.
    """
    from django.conf import settings
    from django.db import connections

    with django_db_blocker.unblock():
        default_db = settings.DATABASES["default"]
        admin_db = settings.DATABASES["admin"]

        default_db["USER"] = _saved_user
        default_db["PASSWORD"] = _saved_password

        # Close the connection and update settings_dict so the next connection
        # uses the restored credentials.
        conn = connections["default"]
        conn.close()
        conn.settings_dict["USER"] = _saved_user
        conn.settings_dict["PASSWORD"] = _saved_password

        yield

        # Swap back to admin for teardown so pytest can drop the database
        default_db["USER"] = admin_db["USER"]
        default_db["PASSWORD"] = admin_db.get("PASSWORD")
        conn.close()
        conn.settings_dict["USER"] = admin_db["USER"]
        conn.settings_dict["PASSWORD"] = admin_db.get("PASSWORD")

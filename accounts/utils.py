from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.http import HttpRequest

from accounts.models import User


class TransactionRequiredError(Exception):
    pass


def get_auth_user(request: HttpRequest) -> User:
    """
    Returns the authenticated user from the request, or raises a ValueError.
    Use this to safely narrow the type of request.user for mypy.
    """
    user = getattr(request, "user", None)
    if not isinstance(user, User) or isinstance(user, AnonymousUser) or not user.is_authenticated:
        raise ValueError("User must be authenticated")
    return user


def set_tenant(organization_id: int) -> None:
    """
    Set the current database transaction tenant context.
    """
    if not connection.in_atomic_block:
        raise TransactionRequiredError("set_tenant() must be called inside an active transaction.")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true);",
            [str(organization_id)],
        )

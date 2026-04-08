from collections.abc import Callable

from django.db import transaction
from django.http import HttpRequest
from django.http.response import HttpResponseBase

from accounts.models import User
from accounts.utils import set_tenant


def tenant_middleware(
    get_response: Callable[[HttpRequest], HttpResponseBase],
) -> Callable[[HttpRequest], HttpResponseBase]:
    def middleware(request: HttpRequest) -> HttpResponseBase:
        user = getattr(request, "user", None)

        if isinstance(user, User) and user.is_authenticated:
            # We manage the transaction boundary here instead of using Django's ATOMIC_REQUESTS.
            # Django's ATOMIC_REQUESTS only wraps the view function, which means the middleware
            # executes outside of that transaction.
            # Because set_tenant() requires an active transaction (so that PostgreSQL's SET LOCAL
            # is automatically dropped when the request ends), we must wrap both the tenant setup
            # and the downstream view execution in an atomic block ourselves.
            with transaction.atomic():
                set_tenant(user.organization_id)
                return get_response(request)

        # Unauthenticated requests proceed without a tenant context.
        # Any database queries to RLS-protected tables will naturally return 0 rows or fail.
        return get_response(request)

    return middleware

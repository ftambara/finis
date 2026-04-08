from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from accounts.models import User


class AdminDBModelBackend(ModelBackend):
    def get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.using("admin").get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User.objects.using("admin").get(email=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

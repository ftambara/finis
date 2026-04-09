import posthog
from django.apps import AppConfig
from django.conf import settings


class FinisConfig(AppConfig):
    name = "finis"

    def ready(self) -> None:
        posthog.api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST
        super().ready()

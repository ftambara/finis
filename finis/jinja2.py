from typing import Any

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def url(viewname: str, *args: Any, **kwargs: Any) -> str:
    return reverse(viewname, args=args, kwargs=kwargs)


def environment(**options: Any) -> Environment:
    env = Environment(**options)
    env.globals["static"] = static
    env.globals["url"] = url
    env.globals["SCANNING_MODEL"] = settings.SCANNING_MODEL
    env.globals["POSTHOG_API_KEY"] = settings.POSTHOG_API_KEY
    env.globals["POSTHOG_HOST"] = settings.POSTHOG_HOST
    env.globals["POSTHOG_ENABLED"] = settings.POSTHOG_ENABLED
    return env

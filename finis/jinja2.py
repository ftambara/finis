from typing import Any

from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def url(viewname: str, *args: Any, **kwargs: Any) -> str:
    return reverse(viewname, args=args, kwargs=kwargs)


def environment(**options: Any) -> Environment:
    env = Environment(**options)
    env.globals["static"] = static
    env.globals["url"] = url
    return env

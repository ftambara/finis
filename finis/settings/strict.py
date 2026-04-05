# ruff: noqa: F403, F405 - Star import is required to inherit and re-export all default settings.
from .default import *


def check(condition: bool, error: str) -> None:
    """Validate a setting and raise ValueError if the condition is not met."""
    if not condition:
        msg = f"Settings assertion failed: {error}"
        logger.warning(msg)
        raise ValueError(msg)


check(DEBUG or DEFAULT_SECRET_KEY != SECRET_KEY, "Using default secret key")
check(DEBUG or LOCAL_HTTPS, "HTTPS disabled")
check(bool(ALLOWED_HOSTS), "ALLOWED_HOSTS is empty")
check("*" not in ALLOWED_HOSTS, "Wildcard present in ALLOWED_HOSTS")

match SCANNING_LLM_PROVIDER:
    case "grok":
        check(bool(GROK_API_KEY), "GROK_API_KEY is required when SCANNING_LLM_PROVIDER is 'grok'")
    case "gemini":
        check(
            bool(GEMINI_API_KEY),
            "GEMINI_API_KEY is required when SCANNING_LLM_PROVIDER is 'gemini'",
        )
    case _:
        check(False, f"Invalid SCANNING_LLM_PROVIDER: {SCANNING_LLM_PROVIDER}")

# PostHog configuration
check(bool(POSTHOG_API_KEY), "POSTHOG_API key not set")
check(bool(POSTHOG_HOST), "POSTHOG_HOST key not set")

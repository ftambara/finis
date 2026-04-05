import importlib
import os
import sys
from collections.abc import Generator
from unittest.mock import patch

import pytest

CleanSettings = Generator[None]


@pytest.fixture
def clean_settings() -> CleanSettings:
    """
    Fixture to cleanly reload settings for each test by clearing sys.modules
    and resetting environment variables.
    """
    old_env = os.environ.copy()

    # Patch env.read_env to do nothing, so it doesn't read the local .env file
    # and override our test environment manipulations.
    with patch("environs.Env.read_env"):

        def remove_settings_modules() -> None:
            for module in list(sys.modules.keys()):
                if module.startswith("finis.settings"):
                    del sys.modules[module]

        remove_settings_modules()
        yield

        os.environ.clear()
        os.environ.update(old_env)
        remove_settings_modules()


def test_default_settings_no_fail_on_missing_env(clean_settings: CleanSettings) -> None:
    # Ensure missing variables don't crash default settings
    os.environ.clear()

    importlib.import_module("finis.settings.default")


@pytest.mark.parametrize(
    "env_vars, expected_error",
    [
        # Missing PostHog API key
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "",
                "POSTHOG_HOST": "some-host",
                "SCANNING_LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "dummy",
                "ALLOWED_HOSTS": "localhost",
            },
            "POSTHOG_API key not set",
        ),
        # Default secret key in non-debug
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "django-insecure-k_@40wpb#=*-hdd_mi9k9y(5=$u4d&#v3x%he4nwedyb!=34kf",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "dummy",
                "ALLOWED_HOSTS": "localhost",
            },
            "Using default secret key",
        ),
        # Missing Gemini API key
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "gemini",
                "ALLOWED_HOSTS": "localhost",
            },
            "GEMINI_API_KEY is required",
        ),
        # Missing Grok API key
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "grok",
                "ALLOWED_HOSTS": "localhost",
            },
            "GROK_API_KEY is required",
        ),
        # Invalid LLM provider
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "invalid-provider",
                "ALLOWED_HOSTS": "localhost",
            },
            "Invalid SCANNING_LLM_PROVIDER: invalid-provider",
        ),
        # Empty ALLOWED_HOSTS
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "dummy",
                "ALLOWED_HOSTS": "",
            },
            "ALLOWED_HOSTS is empty",
        ),
        # Wildcard in ALLOWED_HOSTS
        (
            {
                "DEBUG": "False",
                "SECRET_KEY": "not-default-anymore",
                "POSTHOG_API_KEY": "key",
                "POSTHOG_HOST": "host",
                "SCANNING_LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "dummy",
                "ALLOWED_HOSTS": "localhost,*",
            },
            "Wildcard present in ALLOWED_HOSTS",
        ),
    ],
)
def test_strict_settings_failures(
    clean_settings: CleanSettings, env_vars: dict[str, str], expected_error: str
) -> None:
    os.environ.clear()
    os.environ.update(env_vars)

    with pytest.raises(ValueError, match=expected_error):
        importlib.import_module("finis.settings.strict")


def test_strict_settings_succeeds_when_valid(clean_settings: CleanSettings) -> None:
    os.environ.clear()
    os.environ.update(
        {
            "DEBUG": "False",
            "SECRET_KEY": "not-default-anymore",
            "POSTHOG_API_KEY": "key",
            "POSTHOG_HOST": "host",
            "SCANNING_LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "gemini-key",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
        }
    )

    # If no exception is raised, the test passes
    importlib.import_module("finis.settings.strict")

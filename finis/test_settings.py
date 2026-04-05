import os
import sys
import pytest
from unittest.mock import patch


@pytest.fixture
def clean_settings():
    """
    Fixture to cleanly reload settings for each test by clearing sys.modules
    and resetting environment variables.
    """
    old_env = os.environ.copy()

    # Patch env.read_env to do nothing, so it doesn't read the local .env file
    # and override our test environment manipulations.
    with patch('environs.Env.read_env'):
        def remove_settings_modules():
            for module in list(sys.modules.keys()):
                if module.startswith("finis.settings"):
                    del sys.modules[module]

        remove_settings_modules()
        yield

        os.environ.clear()
        os.environ.update(old_env)
        remove_settings_modules()


def test_default_settings_no_fail_on_missing_env(clean_settings):
    # Ensure missing variables don't crash default settings
    os.environ.clear()

    # Should import without raising any errors
    import finis.settings.default


def test_strict_settings_fails_default_secret_key(clean_settings):
    os.environ["DEBUG"] = "False"
    # Set it to the default key defined in default.py
    os.environ[
        "SECRET_KEY"] = "django-insecure-k_@40wpb#=*-hdd_mi9k9y(5=$u4d&#v3x%he4nwedyb!=34kf"

    with pytest.raises(ValueError, match="Using default secret key"):
        import finis.settings.strict


def test_strict_settings_fails_missing_gemini_key(clean_settings):
    os.environ["DEBUG"] = "False"
    os.environ["SECRET_KEY"] = "not-default-anymore"

    os.environ["SCANNING_LLM_PROVIDER"] = "gemini"
    os.environ.pop("GEMINI_API_KEY", None)

    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        import finis.settings.strict


def test_strict_settings_succeeds_when_valid(clean_settings):
    os.environ["DEBUG"] = "False"
    os.environ["SECRET_KEY"] = "not-default-anymore"
    os.environ["SCANNING_LLM_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "gemini-key"
    os.environ["ALLOWED_HOSTS"] = "localhost,127.0.0.1"

    # Should import without raising any errors
    import finis.settings.strict

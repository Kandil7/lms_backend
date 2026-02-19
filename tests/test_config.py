import pytest

from app.core.config import Settings


def _production_settings(**overrides) -> Settings:
    payload = {
        "ENVIRONMENT": "production",
        "DEBUG": False,
        "SECRET_KEY": "x" * 64,
        "TASKS_FORCE_INLINE": False,
        "ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED": True,
    }
    payload.update(overrides)
    return Settings(**payload)


def test_api_docs_disabled_in_production_effective_flags() -> None:
    settings = _production_settings(ENABLE_API_DOCS=True, STRICT_ROUTER_IMPORTS=False)
    assert settings.API_DOCS_EFFECTIVE_ENABLED is False
    assert settings.STRICT_ROUTER_IMPORTS_EFFECTIVE is True


def test_api_docs_enabled_in_development_by_default() -> None:
    settings = Settings(ENVIRONMENT="development")
    assert settings.API_DOCS_EFFECTIVE_ENABLED is True
    assert settings.STRICT_ROUTER_IMPORTS_EFFECTIVE is False


def test_metrics_path_normalization() -> None:
    settings = Settings(METRICS_PATH="metrics")
    assert settings.METRICS_PATH == "/metrics"


def test_sentry_environment_effective_defaults_to_runtime_environment() -> None:
    settings = Settings(ENVIRONMENT="staging", SENTRY_ENVIRONMENT="")
    assert settings.SENTRY_ENVIRONMENT_EFFECTIVE == "staging"


def test_sentry_sample_rates_must_be_in_0_1_range() -> None:
    with pytest.raises(Exception):
        Settings(SENTRY_TRACES_SAMPLE_RATE=1.5)

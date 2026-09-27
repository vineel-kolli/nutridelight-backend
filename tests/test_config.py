import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings


def test_settings():
    assert settings.app_name == "Nutri Delight API"
    assert settings.environment == "development"


def test_production_environment_is_valid():
    config = Settings(
        database_url="postgresql://test:test@localhost/test",
        environment="production",
    )

    assert config.environment == "production"


def test_invalid_environment_is_rejected():
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://test:test@localhost/test",
            environment="staging",
        )
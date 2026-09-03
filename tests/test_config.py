from app.core.config import settings


def test_settings():
    assert settings.app_name == "Nutri Delight API"
    assert settings.environment == "development"
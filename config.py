"""
Konfigurationsmodul für die Europapark API.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Anwendungskonfiguration aus Umgebungsvariablen."""

    # Datenbank
    database_url: str = "sqlite:///./data.db"

    # Firebase Konfiguration
    fb_app_id: str
    fb_api_key: str
    fb_project_id: str

    # API Konfiguration
    api_base: str
    auth_url: str

    # Encryption Keys
    enc_key: str
    enc_iv: str

    # API Credentials (Fallback)
    user_key: str
    pass_key: str
    api_username: str
    api_password: str

    # App Version
    app_version: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Gibt die gecachte Settings-Instanz zurück."""
    return Settings()


def refresh_settings() -> Settings:
    """Aktualisiert die Settings."""
    get_settings.cache_clear()
    return get_settings()

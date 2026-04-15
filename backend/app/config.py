"""
Configuration module for managing environment variables.
Loads Firebase credentials and app settings from .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Firebase Configuration
    firebase_type: str = os.getenv("TYPE", "")
    firebase_project_id: str = os.getenv("PROJECT_ID", "")
    firebase_private_key_id: str = os.getenv("PRIVATE_KEY_ID", "")
    firebase_private_key: str = os.getenv("PRIVATE_KEY", "")
    firebase_client_email: str = os.getenv("CLIENT_EMAIL", "")
    firebase_client_id: str = os.getenv("CLIENT_ID", "")
    firebase_auth_uri: str = os.getenv("AUTH_URI", "")
    firebase_token_uri: str = os.getenv("TOKEN_URI", "")
    firebase_auth_provider_x509_cert_url: str = os.getenv(
        "AUTH_PROVIDER_X509_CERT_URL", ""
    )
    firebase_client_x509_cert_url: str = os.getenv("CLIENT_X509_CERT_URL", "")

    # App Configuration
    app_name: str = "Tech Monopoly"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    Returns the same instance on multiple calls.
    """
    return Settings()

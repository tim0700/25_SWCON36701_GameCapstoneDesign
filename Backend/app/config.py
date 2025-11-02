"""Application configuration using Pydantic Settings.

This module provides centralized configuration management with environment variable
support and type validation. All paths use pathlib.Path for Windows compatibility.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    Configuration priority:
    1. Environment variables (highest)
    2. .env file
    3. Default values (lowest)
    """

    # Google Cloud Configuration
    google_cloud_project: str = Field(
        ...,
        description="Google Cloud project ID"
    )
    google_cloud_location: str = Field(
        default="us-central1",
        description="Google Cloud region for Vertex AI"
    )
    google_application_credentials: Optional[str] = Field(
        default=None,
        description="Path to Google Cloud service account JSON key"
    )

    # Model Configuration
    gemini_model: str = Field(
        default="gemini-2.5-pro",
        description="Gemini model to use for generation"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for text generation (0.0-1.0)"
    )
    max_output_tokens: int = Field(
        default=8192,
        gt=0,
        description="Maximum tokens in generated response"
    )

    # Path Configuration (Windows compatible using pathlib.Path)
    templates_dir: Path = Field(
        default=Path("app/templates"),
        description="Directory containing prompt templates"
    )
    output_dir: Path = Field(
        default=Path("data/npcs"),
        description="Directory for generated character sheets"
    )

    # API Configuration
    api_timeout: int = Field(
        default=60,
        gt=0,
        description="API request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for failed API calls"
    )

    # Application Settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        """Initialize settings and ensure output directory exists."""
        super().__init__(**kwargs)
        # Create output directory if it doesn't exist (Windows compatible)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

"""
Configuration module for the NPC Dynamic Memory System.

This module handles all configuration settings using Pydantic Settings,
allowing configuration via environment variables or .env file.
"""
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Memory Configuration
    recent_memory_size: int = Field(
        default=5,
        description="Number of recent memories to keep per NPC (FIFO queue size)"
    )
    long_term_buffer_size: int = Field(
        default=10,
        description="Buffer size before triggering automatic embedding"
    )
    similarity_search_results: int = Field(
        default=3,
        description="Number of similar memories to return from vector search"
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    embedding_device: Literal["auto", "cpu", "cuda", "mps"] = Field(
        default="auto",
        description="Device for embedding model (auto=GPU if available)"
    )
    preload_on_startup: bool = Field(
        default=True,
        description="Preload embedding model at startup (recommended)"
    )
    max_batch_size: int = Field(
        default=50,
        description="Maximum batch size for embedding operations"
    )

    # Storage Configuration
    chroma_persist_dir: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory"
    )
    buffer_dir: str = Field(
        default="./data/buffers",
        description="Directory for buffer JSON files"
    )
    recent_memory_backup: str = Field(
        default="./data/recent_memory.json",
        description="Backup file for recent memory persistence"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8123,
        description="API server port"
    )
    api_title: str = Field(
        default="NPC Dynamic Memory System",
        description="API documentation title"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )

    # Quest Generation Configuration (NEW - Backend2 Integration)
    google_cloud_project: str = Field(
        default="questtest-477417",
        description="Google Cloud Project ID"
    )
    google_cloud_location: str = Field(
        default="global",
        description="Google Cloud region for Vertex AI (use 'global' for newest models like Gemini 3.0)"
    )
    google_application_credentials: str = Field(
        default="my-service-account-key.json",
        description="Path to service account JSON key file"
    )
    gemini_model: str = Field(
        default="gemini-3-pro-preview",
        description="Gemini model for quest generation"
    )
    quest_temperature: float = Field(
        default=0.7,
        description="Temperature for quest generation (0.0-1.0)"
    )
    quest_max_output_tokens: int = Field(
        default=8192,
        description="Maximum output tokens for quest generation"
    )
    quest_generation_enabled: bool = Field(
        default=True,
        description="Enable quest generation functionality"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

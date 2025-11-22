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

    # Google Cloud / Vertex AI Configuration (for Quest Generation)
    vertex_project_id: str = Field(
        default="questtest-477417",
        description="Google Cloud project ID for Vertex AI"
    )
    vertex_location: str = Field(
        default="us-central1",
        description="Vertex AI region"
    )
    vertex_model_name: str = Field(
        default="gemini-2.5-pro",
        description="Gemini model name for quest generation"
    )
    google_application_credentials: str = Field(
        default="",
        description="Path to Google Cloud service account key file"
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

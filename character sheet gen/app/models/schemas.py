"""API request and response schemas.

This module defines Pydantic models for API endpoints, including request
validation and response formatting.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CharacterRequest(BaseModel):
    """Request model for character sheet generation.

    This model validates incoming requests to the character generation endpoint.
    """

    character_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the character",
        examples=["npc_wandering_mage_elara", "npc_village_elder_gareth"]
    )
    seed_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Brief description to seed character generation",
        examples=[
            "A wandering mage seeking forgotten knowledge of the world. "
            "Prickly but warm-hearted. Chasing clues to ancient artifacts.",
            "An elderly village leader who has seen too many winters. "
            "Wise and patient, but harbors a dark secret from his past."
        ]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "npc_wandering_mage_elara",
                    "seed_description": "A wandering mage seeking the world's forgotten knowledge. Prickly but warm-hearted. Chasing clues to ancient artifacts."
                }
            ]
        }
    }


class CharacterResponse(BaseModel):
    """Response model for successful character sheet generation."""

    success: bool = Field(
        default=True,
        description="Indicates successful generation"
    )
    character_id: str = Field(
        ...,
        description="The character ID from the request"
    )
    file_path: str = Field(
        ...,
        description="Path to the generated character sheet JSON file"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when the character was generated"
    )
    message: str = Field(
        default="Character sheet generated successfully",
        description="Success message"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "character_id": "npc_wandering_mage_elara",
                    "file_path": "data/npcs/npc_wandering_mage_elara.json",
                    "generated_at": "2025-11-02T12:34:56.789Z",
                    "message": "Character sheet generated successfully"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    success: bool = Field(
        default=False,
        description="Indicates generation failure"
    )
    error_type: str = Field(
        ...,
        description="Type of error that occurred"
    )
    error_message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details (optional)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error_type": "validation_error",
                    "error_message": "Character must have a long-term goal",
                    "details": {
                        "field": "long_term_goal",
                        "reason": "Field is empty"
                    }
                },
                {
                    "success": False,
                    "error_type": "llm_generation_error",
                    "error_message": "Failed to generate character sheet",
                    "details": {
                        "reason": "API timeout after 60 seconds"
                    }
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(
        default="healthy",
        description="Service health status"
    )
    timestamp: datetime = Field(
        ...,
        description="Current server time"
    )
    version: str = Field(
        default="1.0.0",
        description="API version"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2025-11-02T12:34:56.789Z",
                    "version": "1.0.0"
                }
            ]
        }
    }

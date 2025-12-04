"""
API request models for the NPC Dynamic Memory System.

This module defines Pydantic models for validating incoming API requests.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AddMemoryRequest(BaseModel):
    """
    Request body for adding a new memory to an NPC.

    Used by POST /memory/{npc_id}
    """

    content: str = Field(
        ...,
        description="The memory content/text",
        min_length=1,
        max_length=10000
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for this memory"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Player completed the herb gathering quest and returned with rare mushrooms",
                "metadata": {
                    "quest_id": "herb_001",
                    "quest_status": "completed",
                    "importance": "high"
                }
            }
        }


class SearchMemoryRequest(BaseModel):
    """
    Query parameters for searching memories.

    Used by GET /memory/{npc_id}/search
    """

    query: str = Field(
        ...,
        description="Search query for semantic similarity",
        min_length=1,
        max_length=1000
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of similar memories to return"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "sword quest",
                "top_k": 3
            }
        }


class UpdateMemoryRequest(BaseModel):
    """
    Request body for updating an existing memory.

    Used by PUT /admin/memory/{memory_id}
    """

    content: str = Field(
        ...,
        description="Updated memory content",
        min_length=1,
        max_length=10000
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata (replaces existing)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Player completed the advanced herb gathering quest with rare mushrooms",
                "metadata": {
                    "quest_id": "herb_001",
                    "quest_status": "completed",
                    "importance": "high",
                    "reward_given": True
                }
            }
        }


class BulkImportRequest(BaseModel):
    """
    Request body for bulk importing memories.

    Used by POST /admin/import
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier to import memories for",
        min_length=1
    )
    memories: list[Dict[str, Any]] = Field(
        ...,
        description="List of memory objects to import",
        min_items=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "memories": [
                    {
                        "content": "Player asked about sword repairs",
                        "metadata": {"category": "service_inquiry"}
                    },
                    {
                        "content": "Player brought iron ore for crafting",
                        "metadata": {"category": "material_delivery"}
                    }
                ]
            }
        }

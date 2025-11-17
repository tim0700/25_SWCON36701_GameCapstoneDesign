"""
API response models for the NPC Dynamic Memory System.

This module defines Pydantic models for structuring API responses.
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from models.memory import MemoryEntry, SimilarMemory, NPCMemoryStats


class BaseResponse(BaseModel):
    """Base response model with status and message."""

    status: str = Field(
        ...,
        description="Response status (success, error, etc.)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional message providing additional context"
    )


class AddMemoryResponse(BaseResponse):
    """
    Response after successfully adding a memory.

    Returned by POST /memory/{npc_id}
    """

    memory_id: str = Field(
        ...,
        description="ID of the created memory"
    )
    stored_in: str = Field(
        ...,
        description="Where the memory was stored (recent)"
    )
    evicted_to_buffer: bool = Field(
        default=False,
        description="Whether an older memory was evicted to buffer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Memory added successfully",
                "memory_id": "mem_a1b2c3d4e5f6",
                "stored_in": "recent",
                "evicted_to_buffer": True
            }
        }


class RecentMemoryResponse(BaseResponse):
    """
    Response containing recent memories for an NPC.

    Returned by GET /memory/{npc_id}
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    memories: List[MemoryEntry] = Field(
        default_factory=list,
        description="List of recent memories (up to 5)"
    )
    count: int = Field(
        ...,
        ge=0,
        le=5,
        description="Number of recent memories"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "npc_id": "blacksmith_001",
                "memories": [
                    {
                        "id": "mem_abc123",
                        "npc_id": "blacksmith_001",
                        "content": "Player asked about sword repairs",
                        "timestamp": "2025-11-16T10:00:00"
                    }
                ],
                "count": 1
            }
        }


class SearchMemoryResponse(BaseResponse):
    """
    Response containing semantically similar memories.

    Returned by GET /memory/{npc_id}/search
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    query: str = Field(
        ...,
        description="The search query used"
    )
    results: List[SimilarMemory] = Field(
        default_factory=list,
        description="List of similar memories with scores"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of results returned"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "npc_id": "blacksmith_001",
                "query": "sword quest",
                "results": [
                    {
                        "memory": {
                            "id": "mem_abc123",
                            "npc_id": "blacksmith_001",
                            "content": "Player asked about the legendary sword",
                            "timestamp": "2025-11-16T10:00:00"
                        },
                        "similarity_score": 0.87
                    }
                ],
                "count": 1
            }
        }


class ContextResponse(BaseResponse):
    """
    Response containing combined context (recent + relevant memories).

    Returned by GET /memory/{npc_id}/context
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    recent: List[MemoryEntry] = Field(
        default_factory=list,
        description="Recent memories (FIFO queue)"
    )
    relevant: List[SimilarMemory] = Field(
        default_factory=list,
        description="Semantically relevant memories (if query provided)"
    )
    recent_count: int = Field(
        ...,
        ge=0,
        description="Number of recent memories"
    )
    relevant_count: int = Field(
        ...,
        ge=0,
        description="Number of relevant memories"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "npc_id": "blacksmith_001",
                "recent": [
                    {
                        "id": "mem_recent1",
                        "npc_id": "blacksmith_001",
                        "content": "Player showed me the enchanted hammer",
                        "timestamp": "2025-11-16T14:00:00"
                    }
                ],
                "relevant": [
                    {
                        "memory": {
                            "id": "mem_old1",
                            "npc_id": "blacksmith_001",
                            "content": "Player asked about the legendary sword",
                            "timestamp": "2025-11-16T10:00:00"
                        },
                        "similarity_score": 0.87
                    }
                ],
                "recent_count": 1,
                "relevant_count": 1
            }
        }


class NPCListResponse(BaseResponse):
    """
    Response containing list of all NPCs with statistics.

    Returned by GET /admin/npcs
    """

    npcs: List[NPCMemoryStats] = Field(
        default_factory=list,
        description="List of NPCs with memory statistics"
    )
    total_npcs: int = Field(
        ...,
        ge=0,
        description="Total number of NPCs"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "npcs": [
                    {
                        "npc_id": "blacksmith_001",
                        "recent_count": 5,
                        "buffer_count": 7,
                        "longterm_count": 234,
                        "total_count": 246,
                        "last_memory_at": "2025-11-16T14:30:00"
                    }
                ],
                "total_npcs": 1
            }
        }


class ErrorResponse(BaseResponse):
    """
    Standard error response.

    Returned for all error conditions.
    """

    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    detail: Optional[Any] = Field(
        default=None,
        description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "NPC not found",
                "error_code": "NPC_NOT_FOUND",
                "detail": {
                    "npc_id": "unknown_npc_123"
                }
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response.

    Returned by GET /health and GET /admin/health
    """

    status: str = Field(
        ...,
        description="Overall system health (healthy, degraded, unhealthy)"
    )
    embedding_service: str = Field(
        ...,
        description="Embedding service status"
    )
    chromadb: str = Field(
        ...,
        description="ChromaDB connection status"
    )
    recent_memory: str = Field(
        ...,
        description="Recent memory service status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "embedding_service": "loaded",
                "chromadb": "connected",
                "recent_memory": "operational"
            }
        }

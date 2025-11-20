"""
Admin-specific models for the NPC Dynamic Memory System.

This module defines Pydantic models for administrative operations
such as bulk imports, exports, and memory management.
"""
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from models.memory import MemoryEntry, MemoryWithLocation


class ExportData(BaseModel):
    """
    Format for exporting NPC memories.

    Used by GET /admin/export/{npc_id}
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    exported_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this export was created"
    )
    total_memories: int = Field(
        ...,
        ge=0,
        description="Total number of memories exported"
    )
    memories: List[MemoryWithLocation] = Field(
        default_factory=list,
        description="All memories with location information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "exported_at": "2025-11-16T15:00:00",
                "total_memories": 246,
                "memories": [
                    {
                        "id": "mem_abc123",
                        "npc_id": "blacksmith_001",
                        "content": "Player asked about sword repairs",
                        "timestamp": "2025-11-16T10:00:00",
                        "metadata": {"category": "service"},
                        "location": "longterm",
                        "embedding_id": "emb_xyz789"
                    }
                ]
            }
        }


class ImportResult(BaseModel):
    """
    Result of a bulk import operation.

    Returned by POST /admin/import
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    imported_count: int = Field(
        ...,
        ge=0,
        description="Number of memories successfully imported"
    )
    failed_count: int = Field(
        default=0,
        ge=0,
        description="Number of memories that failed to import"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages for failed imports"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "imported_count": 50,
                "failed_count": 2,
                "errors": [
                    "Memory 5: content field is required",
                    "Memory 12: content exceeds maximum length"
                ]
            }
        }


class EmbedNowResult(BaseModel):
    """
    Result of forcing immediate buffer embedding.

    Returned by POST /admin/npc/{npc_id}/embed-now
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    embedded_count: int = Field(
        ...,
        ge=0,
        description="Number of memories embedded from buffer"
    )
    buffer_was_empty: bool = Field(
        default=False,
        description="Whether the buffer was empty"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "embedded_count": 7,
                "buffer_was_empty": False
            }
        }


class ClearMemoryResult(BaseModel):
    """
    Result of clearing all memories for an NPC.

    Returned by DELETE /admin/npc/{npc_id}/clear
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    deleted_recent: int = Field(
        ...,
        ge=0,
        description="Number of recent memories deleted"
    )
    deleted_buffer: int = Field(
        ...,
        ge=0,
        description="Number of buffer memories deleted"
    )
    deleted_longterm: int = Field(
        ...,
        ge=0,
        description="Number of long-term memories deleted"
    )
    total_deleted: int = Field(
        ...,
        ge=0,
        description="Total memories deleted"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "deleted_recent": 5,
                "deleted_buffer": 7,
                "deleted_longterm": 234,
                "total_deleted": 246
            }
        }


class PaginatedMemories(BaseModel):
    """
    Paginated list of memories for admin viewing.

    Returned by GET /admin/npc/{npc_id}/memories
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Items per page"
    )
    total_memories: int = Field(
        ...,
        ge=0,
        description="Total number of memories available"
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages"
    )
    memories: List[MemoryWithLocation] = Field(
        default_factory=list,
        description="Memories on this page"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "page": 1,
                "limit": 50,
                "total_memories": 246,
                "total_pages": 5,
                "memories": [
                    {
                        "id": "mem_abc123",
                        "npc_id": "blacksmith_001",
                        "content": "Player asked about sword repairs",
                        "timestamp": "2025-11-16T10:00:00",
                        "location": "recent",
                        "embedding_id": None
                    }
                ]
            }
        }


class SystemStats(BaseModel):
    """
    Overall system statistics.

    Used for monitoring and admin dashboards.
    """

    total_npcs: int = Field(
        ...,
        ge=0,
        description="Total number of NPCs with memories"
    )
    total_memories: int = Field(
        ...,
        ge=0,
        description="Total memories across all NPCs"
    )
    total_recent: int = Field(
        ...,
        ge=0,
        description="Total memories in recent storage"
    )
    total_buffer: int = Field(
        ...,
        ge=0,
        description="Total memories in buffers"
    )
    total_longterm: int = Field(
        ...,
        ge=0,
        description="Total memories in long-term storage"
    )
    embedding_model_loaded: bool = Field(
        ...,
        description="Whether embedding model is loaded"
    )
    chromadb_collections: int = Field(
        ...,
        ge=0,
        description="Number of ChromaDB collections"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_npcs": 15,
                "total_memories": 3240,
                "total_recent": 65,
                "total_buffer": 87,
                "total_longterm": 3088,
                "embedding_model_loaded": True,
                "chromadb_collections": 15
            }
        }

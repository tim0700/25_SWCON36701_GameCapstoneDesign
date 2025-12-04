"""
Core memory data models for the NPC Dynamic Memory System.

This module defines the fundamental data structures for representing
memories, metadata, and memory-related information.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class MemoryEntry(BaseModel):
    """
    Represents a single memory entry for an NPC.

    This is the core data structure used across all memory systems
    (recent, buffer, and long-term).
    """

    id: str = Field(
        default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}",
        description="Unique identifier for this memory"
    )
    npc_id: str = Field(
        ...,
        description="Identifier of the NPC this memory belongs to",
        min_length=1
    )
    content: str = Field(
        ...,
        description="The actual memory content/text",
        min_length=1
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this memory was created"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for this memory"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "mem_a1b2c3d4e5f6",
                "npc_id": "blacksmith_001",
                "content": "Player asked about the legendary sword",
                "timestamp": "2025-11-16T10:30:00",
                "metadata": {"quest_related": True, "importance": "high"}
            }
        }


class MemoryLocation(BaseModel):
    """
    Metadata about where a memory is stored in the system.
    """

    location: Literal["recent", "buffer", "longterm"] = Field(
        ...,
        description="Current storage location of the memory"
    )
    embedding_id: Optional[str] = Field(
        default=None,
        description="ChromaDB embedding ID (only for longterm memories)"
    )
    added_to_location_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the memory was added to this location"
    )


class MemoryWithLocation(MemoryEntry):
    """
    Memory entry with location information.

    Used for admin/developer operations where knowing the
    storage location is important.
    """

    location: Literal["recent", "buffer", "longterm"] = Field(
        ...,
        description="Current storage location"
    )
    embedding_id: Optional[str] = Field(
        default=None,
        description="ChromaDB embedding ID if in longterm storage"
    )


class SimilarMemory(BaseModel):
    """
    Represents a memory returned from similarity search.

    Includes the memory entry plus similarity score.
    """

    memory: MemoryEntry = Field(
        ...,
        description="The memory entry"
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0.0 to 1.0)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "memory": {
                    "id": "mem_a1b2c3d4e5f6",
                    "npc_id": "blacksmith_001",
                    "content": "Player asked about the legendary sword",
                    "timestamp": "2025-11-16T10:30:00"
                },
                "similarity_score": 0.87
            }
        }


class NPCMemoryStats(BaseModel):
    """
    Statistics about an NPC's memory usage.

    Used for monitoring and admin operations.
    """

    npc_id: str = Field(
        ...,
        description="NPC identifier"
    )
    recent_count: int = Field(
        ...,
        ge=0,
        le=5,
        description="Number of memories in recent storage (max 5)"
    )
    buffer_count: int = Field(
        ...,
        ge=0,
        description="Number of memories in buffer (pending embedding)"
    )
    longterm_count: int = Field(
        ...,
        ge=0,
        description="Number of memories in long-term vector storage"
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of memories across all storage"
    )
    last_memory_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of most recent memory"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": "blacksmith_001",
                "recent_count": 5,
                "buffer_count": 7,
                "longterm_count": 234,
                "total_count": 246,
                "last_memory_at": "2025-11-16T14:30:00"
            }
        }

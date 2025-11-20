"""
Memory Manager - Orchestration layer for NPC memory system.

This service coordinates Recent Memory and Long-term Memory services,
providing a unified interface for memory operations.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from models.memory import MemoryEntry, NPCMemoryStats
from services.recent_memory import RecentMemoryService
from services.longterm_memory import LongTermMemoryService

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Orchestrates recent and long-term memory services.

    Provides a single interface for all memory operations, handling
    the coordination between FIFO queue and vector storage.
    """

    def __init__(
        self,
        recent_service: RecentMemoryService,
        longterm_service: LongTermMemoryService
    ):
        """
        Initialize the memory manager.

        Args:
            recent_service: Recent memory service instance
            longterm_service: Long-term memory service instance
        """
        self.recent_service = recent_service
        self.longterm_service = longterm_service

        logger.info("MemoryManager initialized")

    def add_memory(
        self,
        npc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a new memory for an NPC.

        This method:
        1. Creates a MemoryEntry
        2. Adds to recent memory (FIFO queue)
        3. If evicted, adds to long-term buffer
        4. Auto-embeds if buffer threshold reached

        Args:
            npc_id: NPC identifier
            content: Memory content text
            metadata: Optional metadata dict

        Returns:
            Status dict with:
            - memory_id: ID of created memory
            - stored_in: Where memory was stored ("recent")
            - evicted_to_buffer: Whether an old memory was evicted
            - buffer_auto_embedded: Whether auto-embed was triggered
        """
        # Create memory entry
        memory = MemoryEntry(
            npc_id=npc_id,
            content=content,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        logger.info(f"Adding memory {memory.id} for NPC {npc_id}")

        # Add to recent memory
        evicted_memory = self.recent_service.add_memory(npc_id, memory)

        result = {
            "memory_id": memory.id,
            "stored_in": "recent",
            "evicted_to_buffer": False,
            "buffer_auto_embedded": False
        }

        # Handle eviction
        if evicted_memory:
            logger.debug(
                f"Memory {evicted_memory.id} evicted from recent, "
                f"adding to long-term buffer"
            )

            # Get buffer count before adding
            buffer_before = self.longterm_service.get_buffer_count(npc_id)

            # Add to buffer
            self.longterm_service.add_to_buffer(npc_id, evicted_memory)

            result["evicted_to_buffer"] = True

            # Check if auto-embed was triggered
            buffer_after = self.longterm_service.get_buffer_count(npc_id)

            if buffer_after == 0 and buffer_before > 0:
                # Buffer was cleared, meaning auto-embed happened
                result["buffer_auto_embedded"] = True
                logger.info(
                    f"Auto-embed triggered for {npc_id}, "
                    f"{buffer_before} memories embedded"
                )

        return result

    def get_context(
        self,
        npc_id: str,
        query: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Get memory context for an NPC.

        Returns recent memories plus semantically relevant memories if query provided.

        Args:
            npc_id: NPC identifier
            query: Optional search query for semantic search
            top_k: Number of relevant memories to return (default: 3)

        Returns:
            Dict with:
            - recent: List of recent memories (up to 5)
            - relevant: List of similar memories with scores (if query provided)
            - recent_count: Number of recent memories
            - relevant_count: Number of relevant memories
        """
        logger.debug(f"Getting context for {npc_id}, query: {query}")

        # Get recent memories
        recent_memories = self.recent_service.get_recent(npc_id)

        context = {
            "recent": recent_memories,
            "relevant": [],
            "recent_count": len(recent_memories),
            "relevant_count": 0
        }

        # Get relevant memories if query provided
        if query:
            relevant_memories = self.longterm_service.search(
                npc_id=npc_id,
                query=query,
                top_k=top_k
            )

            context["relevant"] = relevant_memories
            context["relevant_count"] = len(relevant_memories)

            logger.debug(
                f"Context for {npc_id}: {len(recent_memories)} recent, "
                f"{len(relevant_memories)} relevant"
            )

        return context

    def get_stats(self, npc_id: str) -> NPCMemoryStats:
        """
        Get comprehensive memory statistics for an NPC.

        Args:
            npc_id: NPC identifier

        Returns:
            NPCMemoryStats object with counts from all storage locations
        """
        # Get counts from each service
        recent_count = self.recent_service.get_count(npc_id)
        longterm_stats = self.longterm_service.get_stats(npc_id)

        buffer_count = longterm_stats["buffer_count"]
        longterm_count = longterm_stats["longterm_count"]

        total_count = recent_count + buffer_count + longterm_count

        # Get last memory timestamp from recent
        recent_memories = self.recent_service.get_recent(npc_id)
        last_memory_at = None
        if recent_memories:
            # Recent memories are ordered oldest to newest
            last_memory_at = recent_memories[-1].timestamp

        stats = NPCMemoryStats(
            npc_id=npc_id,
            recent_count=recent_count,
            buffer_count=buffer_count,
            longterm_count=longterm_count,
            total_count=total_count,
            last_memory_at=last_memory_at
        )

        logger.debug(f"Stats for {npc_id}: {stats.model_dump()}")

        return stats

    def clear_npc(self, npc_id: str) -> Dict[str, int]:
        """
        Clear all memories for an NPC (all storage locations).

        Args:
            npc_id: NPC identifier

        Returns:
            Dict with counts of deleted items from each location
        """
        logger.warning(f"Clearing ALL memories for NPC {npc_id}")

        # Clear recent memory
        self.recent_service.clear_npc(npc_id)

        # Clear long-term (buffer + vector DB)
        longterm_counts = self.longterm_service.clear_npc(npc_id)

        result = {
            "recent": self.recent_service.get_count(npc_id),  # Should be 0
            "buffer": longterm_counts["buffer"],
            "longterm": longterm_counts["longterm"],
            "total": longterm_counts["buffer"] + longterm_counts["longterm"]
        }

        logger.info(
            f"Cleared {result['total']} total memories for {npc_id} "
            f"(buffer: {result['buffer']}, longterm: {result['longterm']})"
        )

        return result

    def get_all_npcs(self) -> List[str]:
        """
        Get list of all NPCs with memories.

        Combines NPCs from recent and long-term storage.

        Returns:
            List of unique NPC identifiers
        """
        recent_npcs = set(self.recent_service.get_all_npcs())

        # Get NPCs from long-term storage (buffer files)
        # Note: This could be extended to also check ChromaDB collections

        all_npcs = sorted(list(recent_npcs))

        logger.debug(f"Found {len(all_npcs)} NPCs with memories")

        return all_npcs

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get system-wide statistics across all NPCs.

        Returns:
            Dict with aggregated stats
        """
        npcs = self.get_all_npcs()

        total_stats = {
            "total_npcs": len(npcs),
            "total_memories": 0,
            "total_recent": 0,
            "total_buffer": 0,
            "total_longterm": 0,
            "npc_stats": []
        }

        for npc_id in npcs:
            stats = self.get_stats(npc_id)
            total_stats["total_recent"] += stats.recent_count
            total_stats["total_buffer"] += stats.buffer_count
            total_stats["total_longterm"] += stats.longterm_count
            total_stats["total_memories"] += stats.total_count
            total_stats["npc_stats"].append(stats.model_dump())

        logger.info(
            f"System stats: {total_stats['total_npcs']} NPCs, "
            f"{total_stats['total_memories']} total memories"
        )

        return total_stats

    def force_embed_buffer(self, npc_id: str) -> int:
        """
        Force immediate embedding of buffered memories (admin operation).

        Args:
            npc_id: NPC identifier

        Returns:
            Number of memories embedded
        """
        logger.info(f"Force embedding buffer for {npc_id}")
        return self.longterm_service.force_embed(npc_id)

    def search_longterm(
        self,
        npc_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Any]:
        """
        Direct semantic search in long-term memory.

        Args:
            npc_id: NPC identifier
            query: Search query
            top_k: Number of results

        Returns:
            List of SimilarMemory objects
        """
        return self.longterm_service.search(npc_id, query, top_k)

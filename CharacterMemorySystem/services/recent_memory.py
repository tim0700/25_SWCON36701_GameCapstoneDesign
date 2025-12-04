"""
Recent Memory Service - FIFO queue for NPC working memory.

This service manages a FIFO queue of recent memories for each NPC,
with automatic eviction when capacity (5 items) is reached.
"""
import json
import logging
from collections import deque
from typing import Dict, List, Optional
from pathlib import Path

from models.memory import MemoryEntry

logger = logging.getLogger(__name__)


class RecentMemoryService:
    """
    Manages recent memories for NPCs using FIFO queues.

    Each NPC has a deque with maxlen=5. When full, adding a new item
    automatically evicts the oldest, which is returned for long-term storage.
    """

    def __init__(self, max_size: int = 5):
        """
        Initialize the recent memory service.

        Args:
            max_size: Maximum number of recent memories per NPC (default: 5)
        """
        self.max_size = max_size
        self._storage: Dict[str, deque] = {}
        logger.info(f"RecentMemoryService initialized with max_size={max_size}")

    def add_memory(
        self,
        npc_id: str,
        memory: MemoryEntry
    ) -> Optional[MemoryEntry]:
        """
        Add a memory to an NPC's recent memory queue.

        If the queue is full (5 items), the oldest memory is evicted
        and returned for long-term storage.

        Args:
            npc_id: NPC identifier
            memory: MemoryEntry to add

        Returns:
            Evicted MemoryEntry if queue was full, None otherwise
        """
        # Initialize deque for NPC if not exists
        if npc_id not in self._storage:
            self._storage[npc_id] = deque(maxlen=self.max_size)
            logger.debug(f"Created new memory queue for NPC: {npc_id}")

        queue = self._storage[npc_id]

        # Check if queue is full before adding
        evicted_memory = None
        if len(queue) == self.max_size:
            # deque will auto-evict, but we need to capture it first
            evicted_memory = queue[0]  # Oldest item (will be evicted)
            logger.debug(
                f"Queue full for {npc_id}. Evicting memory: {evicted_memory.id}"
            )

        # Add new memory (deque automatically evicts oldest if full)
        queue.append(memory)
        logger.debug(
            f"Added memory {memory.id} to {npc_id}. "
            f"Queue size: {len(queue)}/{self.max_size}"
        )

        return evicted_memory

    def get_recent(self, npc_id: str) -> List[MemoryEntry]:
        """
        Get all recent memories for an NPC.

        Memories are returned in chronological order (oldest first).

        Args:
            npc_id: NPC identifier

        Returns:
            List of MemoryEntry objects (up to 5), empty list if NPC not found
        """
        if npc_id not in self._storage:
            logger.debug(f"No recent memories found for NPC: {npc_id}")
            return []

        # Convert deque to list (maintains order: oldest to newest)
        memories = list(self._storage[npc_id])
        logger.debug(f"Retrieved {len(memories)} recent memories for {npc_id}")
        return memories

    def get_all_npcs(self) -> List[str]:
        """
        Get list of all NPC IDs that have memories.

        Returns:
            List of NPC identifiers
        """
        npc_list = list(self._storage.keys())
        logger.debug(f"Found {len(npc_list)} NPCs with recent memories")
        return npc_list

    def clear_npc(self, npc_id: str) -> None:
        """
        Clear all recent memories for a specific NPC.

        Args:
            npc_id: NPC identifier
        """
        if npc_id in self._storage:
            count = len(self._storage[npc_id])
            del self._storage[npc_id]
            logger.info(f"Cleared {count} recent memories for NPC: {npc_id}")
        else:
            logger.warning(f"Attempted to clear non-existent NPC: {npc_id}")

    def get_count(self, npc_id: str) -> int:
        """
        Get the number of recent memories for an NPC.

        Args:
            npc_id: NPC identifier

        Returns:
            Count of recent memories (0 if NPC not found)
        """
        if npc_id not in self._storage:
            return 0
        return len(self._storage[npc_id])

    def update_memory(
        self,
        npc_id: str,
        memory_id: str,
        new_content: str,
        new_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update a memory's content and/or metadata by ID.

        Searches for the memory in the NPC's recent queue and updates it
        while preserving the original ID and timestamp.

        Args:
            npc_id: NPC identifier
            memory_id: Memory identifier to update
            new_content: New content for the memory
            new_metadata: Optional new metadata (if None, preserves existing)

        Returns:
            True if memory was found and updated, False if not found
        """
        if npc_id not in self._storage:
            logger.debug(f"NPC {npc_id} not found in recent storage")
            return False

        queue = self._storage[npc_id]

        # Convert deque to list to find and update the item
        memories_list = list(queue)
        updated = False

        for i, memory in enumerate(memories_list):
            if memory.id == memory_id:
                # Update the memory in place
                memory.content = new_content
                if new_metadata is not None:
                    memory.metadata = new_metadata
                updated = True
                logger.info(
                    f"Updated memory {memory_id} in recent storage for {npc_id}"
                )
                break

        if updated:
            # Recreate the deque with updated memories (preserves order)
            self._storage[npc_id] = deque(memories_list, maxlen=self.max_size)
            return True
        else:
            logger.debug(
                f"Memory {memory_id} not found in recent storage for {npc_id}"
            )
            return False

    def delete_memory(self, npc_id: str, memory_id: str) -> bool:
        """
        Delete a memory by ID from the recent queue.

        Searches for the memory in the NPC's recent queue and removes it
        while preserving the order of remaining memories.

        Args:
            npc_id: NPC identifier
            memory_id: Memory identifier to delete

        Returns:
            True if memory was found and deleted, False if not found
        """
        if npc_id not in self._storage:
            logger.debug(f"NPC {npc_id} not found in recent storage")
            return False

        queue = self._storage[npc_id]

        # Convert deque to list to filter out the target memory
        memories_list = list(queue)
        original_count = len(memories_list)

        # Filter out the memory with matching ID
        filtered_memories = [m for m in memories_list if m.id != memory_id]

        if len(filtered_memories) < original_count:
            # Memory was found and removed
            self._storage[npc_id] = deque(filtered_memories, maxlen=self.max_size)
            logger.info(
                f"Deleted memory {memory_id} from recent storage for {npc_id}"
            )
            return True
        else:
            logger.debug(
                f"Memory {memory_id} not found in recent storage for {npc_id}"
            )
            return False

    def save_to_disk(self, filepath: str) -> None:
        """
        Persist all recent memories to disk as JSON.

        This is used for graceful shutdown to restore state on restart.

        Args:
            filepath: Path to JSON file for persistence
        """
        # Convert deques to lists and MemoryEntry objects to dicts
        data = {}
        for npc_id, queue in self._storage.items():
            data[npc_id] = [memory.model_dump() for memory in queue]

        # Ensure parent directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)  # default=str for datetime

        total_memories = sum(len(queue) for queue in self._storage.values())
        logger.info(
            f"Saved {total_memories} recent memories "
            f"for {len(self._storage)} NPCs to {filepath}"
        )

    def load_from_disk(self, filepath: str) -> None:
        """
        Restore recent memories from disk.

        This is used at startup to restore state from previous session.

        Args:
            filepath: Path to JSON file with persisted data
        """
        try:
            if not Path(filepath).exists():
                logger.info(f"No backup file found at {filepath}, starting fresh")
                return

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruct deques with MemoryEntry objects
            for npc_id, memories_data in data.items():
                self._storage[npc_id] = deque(
                    [MemoryEntry(**mem_dict) for mem_dict in memories_data],
                    maxlen=self.max_size
                )

            total_memories = sum(len(queue) for queue in self._storage.values())
            logger.info(
                f"Loaded {total_memories} recent memories "
                f"for {len(self._storage)} NPCs from {filepath}"
            )

        except Exception as e:
            logger.error(f"Failed to load recent memories from {filepath}: {e}")
            # Don't crash - start with empty state
            self._storage = {}

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about recent memory usage.

        Returns:
            Dict with total_npcs and total_memories
        """
        stats = {
            "total_npcs": len(self._storage),
            "total_memories": sum(len(queue) for queue in self._storage.values())
        }
        return stats

"""
Long-term Memory Service - Vector storage with ChromaDB.

This service manages the long-term memory for NPCs using a two-stage approach:
1. Buffer: Temporary storage (JSON files) until threshold reached
2. Vector DB: Embedded memories in ChromaDB for semantic search
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from models.memory import MemoryEntry, SimilarMemory
from utils.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class LongTermMemoryService:
    """
    Manages long-term memory storage with buffering and vector embeddings.

    Each NPC has:
    - A buffer (JSON file) for memories awaiting embedding
    - A ChromaDB collection for embedded memories
    """

    def __init__(
        self,
        chroma_client,
        embedding_service: EmbeddingService,
        buffer_dir: str = "./data/buffers",
        buffer_size: int = 10
    ):
        """
        Initialize the long-term memory service.

        Args:
            chroma_client: ChromaDB client instance
            embedding_service: Embedding service for vector generation
            buffer_dir: Directory for buffer JSON files
            buffer_size: Number of items before auto-embedding
        """
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
        self.buffer_dir = Path(buffer_dir)
        self.buffer_size = buffer_size

        # Ensure buffer directory exists
        self.buffer_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"LongTermMemoryService initialized: "
            f"buffer_dir={buffer_dir}, buffer_size={buffer_size}"
        )

    def _get_buffer_path(self, npc_id: str) -> Path:
        """Get path to buffer file for an NPC."""
        return self.buffer_dir / f"{npc_id}.json"

    def _get_collection_name(self, npc_id: str) -> str:
        """Get ChromaDB collection name for an NPC."""
        return f"npc_{npc_id}_longterm"

    def _load_buffer(self, npc_id: str) -> List[Dict[str, Any]]:
        """
        Load buffer from disk for an NPC.

        Returns:
            List of memory dicts, empty list if file doesn't exist
        """
        buffer_path = self._get_buffer_path(npc_id)

        if not buffer_path.exists():
            return []

        try:
            with open(buffer_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('memories', [])
        except Exception as e:
            logger.error(f"Failed to load buffer for {npc_id}: {e}")
            return []

    def _save_buffer(self, npc_id: str, memories: List[Dict[str, Any]]) -> None:
        """
        Save buffer to disk for an NPC.

        Args:
            npc_id: NPC identifier
            memories: List of memory dicts to save
        """
        buffer_path = self._get_buffer_path(npc_id)

        try:
            data = {
                "memories": memories,
                "count": len(memories),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            with open(buffer_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Saved {len(memories)} memories to buffer for {npc_id}")

        except Exception as e:
            logger.error(f"Failed to save buffer for {npc_id}: {e}")
            raise

    def add_to_buffer(self, npc_id: str, memory: MemoryEntry) -> None:
        """
        Add a memory to the buffer.

        If buffer reaches threshold, automatically triggers embedding.

        Args:
            npc_id: NPC identifier
            memory: Memory to add
        """
        # Load current buffer
        buffer = self._load_buffer(npc_id)

        # Add new memory
        buffer.append(memory.model_dump())

        # Save updated buffer
        self._save_buffer(npc_id, buffer)

        logger.debug(
            f"Added memory {memory.id} to buffer for {npc_id}. "
            f"Buffer: {len(buffer)}/{self.buffer_size}"
        )

        # Check if should auto-embed
        if self._should_embed(npc_id):
            logger.info(f"Buffer threshold reached for {npc_id}, auto-embedding...")
            self._embed_buffer(npc_id)

    def get_buffer_count(self, npc_id: str) -> int:
        """
        Get number of memories in buffer for an NPC.

        Args:
            npc_id: NPC identifier

        Returns:
            Count of buffered memories
        """
        buffer = self._load_buffer(npc_id)
        return len(buffer)

    def _should_embed(self, npc_id: str) -> bool:
        """
        Check if buffer should be embedded.

        Args:
            npc_id: NPC identifier

        Returns:
            True if buffer size >= threshold
        """
        return self.get_buffer_count(npc_id) >= self.buffer_size

    def _embed_buffer(self, npc_id: str) -> int:
        """
        Embed all buffered memories and store in ChromaDB.

        This is triggered automatically when buffer reaches threshold,
        or manually via force_embed().

        Args:
            npc_id: NPC identifier

        Returns:
            Number of memories embedded
        """
        # Load buffer
        buffer = self._load_buffer(npc_id)

        if not buffer:
            logger.debug(f"No memories in buffer for {npc_id}, nothing to embed")
            return 0

        try:
            # Extract content for embedding
            contents = [mem['content'] for mem in buffer]
            memory_ids = [mem['id'] for mem in buffer]

            logger.info(f"Embedding {len(contents)} memories for {npc_id}...")

            # Generate embeddings (batch)
            embeddings = self.embedding_service.embed(contents)

            # Ensure 2D array
            if len(embeddings.shape) == 1:
                embeddings = embeddings.reshape(1, -1)

            # Get or create collection
            collection = self.chroma_client.get_or_create_collection(
                name=self._get_collection_name(npc_id)
            )

            # Prepare metadata
            metadatas = [
                {
                    "npc_id": mem['npc_id'],
                    "memory_id": mem['id'],
                    "timestamp": mem['timestamp'] if isinstance(mem['timestamp'], str) else mem['timestamp'].isoformat(),
                    "content": mem['content']  # Store content in metadata for retrieval
                }
                for mem in buffer
            ]

            # Add to ChromaDB
            collection.add(
                ids=memory_ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=contents  # ChromaDB requires documents
            )

            logger.info(
                f"✓ Embedded {len(buffer)} memories for {npc_id} "
                f"into collection '{self._get_collection_name(npc_id)}'"
            )

            # Clear buffer after successful embedding
            self._save_buffer(npc_id, [])

            return len(buffer)

        except Exception as e:
            logger.error(f"Failed to embed buffer for {npc_id}: {e}")
            raise RuntimeError(f"Embedding failed: {e}")

    def search(
        self,
        npc_id: str,
        query: str,
        top_k: int = 3
    ) -> List[SimilarMemory]:
        """
        Semantic search for similar memories.

        Args:
            npc_id: NPC identifier
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of SimilarMemory objects with similarity scores
        """
        try:
            # Get collection
            collection = self.chroma_client.get_or_create_collection(
                name=self._get_collection_name(npc_id)
            )

            # Check if collection is empty
            if collection.count() == 0:
                logger.debug(f"No memories in long-term storage for {npc_id}")
                return []

            # Generate query embedding
            query_embedding = self.embedding_service.embed(query)

            # Search
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(top_k, collection.count())
            )

            # Convert to SimilarMemory objects
            similar_memories = []

            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]

                    # Convert distance to similarity (ChromaDB uses L2 distance)
                    # For normalized embeddings: similarity = 1 - (distance^2 / 2)
                    similarity = 1.0 - (distance ** 2 / 2.0)
                    similarity = max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

                    # Reconstruct MemoryEntry
                    memory = MemoryEntry(
                        id=metadata['memory_id'],
                        npc_id=metadata['npc_id'],
                        content=metadata['content'],
                        timestamp=datetime.fromisoformat(metadata['timestamp'])
                    )

                    similar_memories.append(
                        SimilarMemory(
                            memory=memory,
                            similarity_score=similarity
                        )
                    )

            logger.debug(
                f"Found {len(similar_memories)} similar memories "
                f"for {npc_id} with query: '{query[:50]}...'"
            )

            return similar_memories

        except Exception as e:
            logger.error(f"Search failed for {npc_id}: {e}")
            return []

    def get_all_memories(self, npc_id: str) -> List[MemoryEntry]:
        """
        Get all long-term memories for an NPC.

        Args:
            npc_id: NPC identifier

        Returns:
            List of all MemoryEntry objects in long-term storage
        """
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=self._get_collection_name(npc_id)
            )

            if collection.count() == 0:
                return []

            # Get all items
            results = collection.get()

            # Convert to MemoryEntry objects
            memories = []
            for i, memory_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]

                memory = MemoryEntry(
                    id=metadata['memory_id'],
                    npc_id=metadata['npc_id'],
                    content=metadata['content'],
                    timestamp=datetime.fromisoformat(metadata['timestamp'])
                )
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"Failed to get all memories for {npc_id}: {e}")
            return []

    def update_memory(self, npc_id: str, memory_id: str, new_content: str) -> bool:
        """
        Update a memory's content and re-embed.

        Args:
            npc_id: NPC identifier
            memory_id: Memory identifier
            new_content: New content text

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=self._get_collection_name(npc_id)
            )

            # Get existing memory
            result = collection.get(ids=[memory_id])

            if not result['ids']:
                logger.warning(f"Memory {memory_id} not found for update")
                return False

            # Generate new embedding
            new_embedding = self.embedding_service.embed(new_content)

            # Update metadata
            metadata = result['metadatas'][0]
            metadata['content'] = new_content
            metadata['timestamp'] = datetime.now(timezone.utc).isoformat()

            # Update in ChromaDB
            collection.update(
                ids=[memory_id],
                embeddings=[new_embedding.tolist()],
                metadatas=[metadata],
                documents=[new_content]
            )

            logger.info(f"Updated memory {memory_id} for {npc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False

    def delete_memory(self, npc_id: str, memory_id: str) -> bool:
        """
        Delete a memory from long-term storage.

        Args:
            npc_id: NPC identifier
            memory_id: Memory identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=self._get_collection_name(npc_id)
            )

            collection.delete(ids=[memory_id])

            logger.info(f"Deleted memory {memory_id} for {npc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def force_embed(self, npc_id: str) -> int:
        """
        Force immediate embedding of buffered memories (admin operation).

        Args:
            npc_id: NPC identifier

        Returns:
            Number of memories embedded
        """
        logger.info(f"Force embedding requested for {npc_id}")
        return self._embed_buffer(npc_id)

    def clear_npc(self, npc_id: str) -> Dict[str, int]:
        """
        Clear all long-term memories for an NPC (buffer + vector DB).

        Args:
            npc_id: NPC identifier

        Returns:
            Dict with counts of deleted items
        """
        counts = {"buffer": 0, "longterm": 0}

        # Clear buffer
        buffer = self._load_buffer(npc_id)
        counts["buffer"] = len(buffer)
        if buffer:
            self._save_buffer(npc_id, [])

        # Delete ChromaDB collection
        try:
            collection_name = self._get_collection_name(npc_id)
            collection = self.chroma_client.get_collection(name=collection_name)
            counts["longterm"] = collection.count()
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}' with {counts['longterm']} memories")
        except Exception as e:
            logger.warning(f"Collection may not exist for {npc_id}: {e}")

        logger.info(
            f"Cleared {counts['buffer']} buffer + {counts['longterm']} "
            f"longterm memories for {npc_id}"
        )

        return counts

    def get_stats(self, npc_id: str) -> Dict[str, int]:
        """
        Get statistics for an NPC's long-term memory.

        Args:
            npc_id: NPC identifier

        Returns:
            Dict with buffer_count and longterm_count
        """
        stats = {
            "buffer_count": self.get_buffer_count(npc_id),
            "longterm_count": 0
        }

        try:
            collection = self.chroma_client.get_collection(
                name=self._get_collection_name(npc_id)
            )
            stats["longterm_count"] = collection.count()
        except Exception:
            # Collection doesn't exist yet
            pass

        return stats

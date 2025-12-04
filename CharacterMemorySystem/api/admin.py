"""
Admin API Endpoints - System management and developer operations.

This module provides FastAPI endpoints for administrative tasks:
- List all NPCs with statistics
- View paginated memories for debugging
- Update/delete individual memories
- Force buffer embedding
- Clear all memories for an NPC
- Bulk import/export operations
- System health monitoring
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from models.requests import BulkImportRequest, UpdateMemoryRequest
from models.responses import (
    NPCListResponse,
    BaseResponse,
    ErrorResponse,
    HealthResponse
)
from models.admin import (
    PaginatedMemories,
    ImportResult,
    ExportData,
    EmbedNowResult,
    ClearMemoryResult
)
from models.memory import MemoryEntry, MemoryWithLocation, NPCMemoryStats
from services.memory_manager import MemoryManager
from utils.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(
    prefix="/admin",
    tags=["Admin Operations"],
    responses={
        400: {"description": "Validation error", "model": ErrorResponse},
        404: {"description": "Resource not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse}
    }
)

# Global dependencies (set during application startup)
_memory_manager: Optional[MemoryManager] = None
_embedding_service: Optional[EmbeddingService] = None
_chroma_client: Optional[Any] = None


def set_memory_manager(manager: MemoryManager) -> None:
    """Set the global memory manager instance."""
    global _memory_manager
    _memory_manager = manager
    logger.info("Admin: Memory Manager dependency injected")


def set_embedding_service(service: EmbeddingService) -> None:
    """Set the global embedding service instance."""
    global _embedding_service
    _embedding_service = service
    logger.info("Admin: Embedding Service dependency injected")


def set_chroma_client(client: Any) -> None:
    """Set the global ChromaDB client instance."""
    global _chroma_client
    _chroma_client = client
    logger.info("Admin: ChromaDB client dependency injected")


def get_memory_manager() -> MemoryManager:
    """Dependency for injecting MemoryManager into routes."""
    if _memory_manager is None:
        logger.error("Memory Manager not initialized")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Memory Manager not initialized",
                "error_code": "SERVICE_UNAVAILABLE"
            }
        )
    return _memory_manager


def get_embedding_service() -> EmbeddingService:
    """Dependency for injecting EmbeddingService into routes."""
    if _embedding_service is None:
        logger.error("Embedding Service not initialized")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Embedding Service not initialized",
                "error_code": "SERVICE_UNAVAILABLE"
            }
        )
    return _embedding_service


def get_chroma_client() -> Any:
    """Dependency for injecting ChromaDB client into routes."""
    if _chroma_client is None:
        logger.error("ChromaDB client not initialized")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "ChromaDB client not initialized",
                "error_code": "SERVICE_UNAVAILABLE"
            }
        )
    return _chroma_client


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_memories_with_location(
    npc_id: str,
    manager: MemoryManager
) -> List[MemoryWithLocation]:
    """
    Get all memories for an NPC from all storage locations with location metadata.

    Args:
        npc_id: NPC identifier
        manager: MemoryManager instance

    Returns:
        List of MemoryWithLocation objects
    """
    all_memories: List[MemoryWithLocation] = []

    # Get recent memories
    try:
        recent_memories = manager.recent_service.get_recent(npc_id)
        for mem in recent_memories:
            mem_with_loc = MemoryWithLocation(
                **mem.model_dump(),
                location="recent",
                embedding_id=None
            )
            all_memories.append(mem_with_loc)
        logger.debug(f"Found {len(recent_memories)} recent memories for {npc_id}")
    except Exception as e:
        logger.warning(f"Error fetching recent memories for {npc_id}: {e}")

    # Get buffer memories
    try:
        buffer_data = manager.longterm_service._load_buffer(npc_id)
        for mem_dict in buffer_data:
            # Convert dict to MemoryEntry then to MemoryWithLocation
            mem_entry = MemoryEntry(**mem_dict)
            mem_with_loc = MemoryWithLocation(
                **mem_entry.model_dump(),
                location="buffer",
                embedding_id=None
            )
            all_memories.append(mem_with_loc)
        logger.debug(f"Found {len(buffer_data)} buffer memories for {npc_id}")
    except Exception as e:
        logger.warning(f"Error fetching buffer memories for {npc_id}: {e}")

    # Get longterm memories
    try:
        longterm_memories = manager.longterm_service.get_all_memories(npc_id)

        # Try to get embedding IDs from ChromaDB
        embedding_ids = {}
        try:
            if _chroma_client:
                collection_name = f"npc_{npc_id}_longterm"
                collection = _chroma_client.get_or_create_collection(name=collection_name)
                results = collection.get()

                # Map memory IDs to embedding IDs
                if results and 'ids' in results and 'metadatas' in results:
                    for emb_id, metadata in zip(results['ids'], results['metadatas']):
                        if metadata and 'memory_id' in metadata:
                            embedding_ids[metadata['memory_id']] = emb_id
        except Exception as e:
            logger.warning(f"Could not fetch embedding IDs for {npc_id}: {e}")

        for mem in longterm_memories:
            emb_id = embedding_ids.get(mem.id)
            mem_with_loc = MemoryWithLocation(
                **mem.model_dump(),
                location="longterm",
                embedding_id=emb_id
            )
            all_memories.append(mem_with_loc)
        logger.debug(f"Found {len(longterm_memories)} longterm memories for {npc_id}")
    except Exception as e:
        logger.warning(f"Error fetching longterm memories for {npc_id}: {e}")

    # Sort by timestamp (newest first)
    all_memories.sort(key=lambda m: m.timestamp, reverse=True)

    return all_memories


def find_memory_location(
    npc_id: str,
    memory_id: str,
    manager: MemoryManager
) -> Optional[Tuple[str, MemoryEntry]]:
    """
    Find which storage location contains a specific memory.

    Args:
        npc_id: NPC identifier
        memory_id: Memory identifier
        manager: MemoryManager instance

    Returns:
        Tuple of (location, MemoryEntry) if found, None otherwise
        location is one of: "recent", "buffer", "longterm"
    """
    # Check recent
    try:
        recent_memories = manager.recent_service.get_recent(npc_id)
        for mem in recent_memories:
            if mem.id == memory_id:
                return ("recent", mem)
    except Exception as e:
        logger.warning(f"Error searching recent for {memory_id}: {e}")

    # Check buffer
    try:
        buffer_data = manager.longterm_service._load_buffer(npc_id)
        for mem_dict in buffer_data:
            if mem_dict.get('id') == memory_id:
                return ("buffer", MemoryEntry(**mem_dict))
    except Exception as e:
        logger.warning(f"Error searching buffer for {memory_id}: {e}")

    # Check longterm (try to get by ID)
    try:
        longterm_memories = manager.longterm_service.get_all_memories(npc_id)
        for mem in longterm_memories:
            if mem.id == memory_id:
                return ("longterm", mem)
    except Exception as e:
        logger.warning(f"Error searching longterm for {memory_id}: {e}")

    return None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/npcs",
    response_model=NPCListResponse,
    status_code=200,
    summary="List all NPCs",
    description="Get a list of all NPCs with their memory statistics."
)
async def list_npcs(
    manager: MemoryManager = Depends(get_memory_manager)
) -> NPCListResponse:
    """
    List all NPCs with memory statistics.

    Returns statistics for each NPC including counts of memories
    in recent, buffer, and longterm storage.

    Args:
        manager: Injected MemoryManager dependency

    Returns:
        NPCListResponse with list of NPCs and their stats
    """
    try:
        logger.info("GET /admin/npcs - retrieving all NPC stats")

        # Get all NPC IDs
        npc_ids = manager.get_all_npcs()

        # Get stats for each NPC
        npc_stats_list: List[NPCMemoryStats] = []
        for npc_id in npc_ids:
            try:
                stats = manager.get_stats(npc_id)
                npc_stats_list.append(stats)
            except Exception as e:
                logger.warning(f"Could not get stats for NPC {npc_id}: {e}")
                continue

        logger.info(f"Retrieved stats for {len(npc_stats_list)} NPCs")

        return NPCListResponse(
            status="success",
            message=f"Found {len(npc_stats_list)} NPCs",
            npcs=npc_stats_list,
            total_npcs=len(npc_stats_list)
        )

    except Exception as e:
        logger.error(f"Error listing NPCs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to list NPCs",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.get(
    "/npc/{npc_id}/memories",
    response_model=PaginatedMemories,
    status_code=200,
    summary="Get paginated memories",
    description="Get all memories for an NPC with pagination (recent + buffer + longterm)."
)
async def get_paginated_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> PaginatedMemories:
    """
    Get paginated memories for an NPC across all storage locations.

    Returns memories from recent, buffer, and longterm storage,
    sorted by timestamp (newest first) with pagination.

    Args:
        npc_id: NPC identifier
        page: Page number (starts at 1)
        limit: Number of items per page (1-100)
        manager: Injected MemoryManager dependency

    Returns:
        PaginatedMemories with requested page of memories
    """
    try:
        logger.info(f"GET /admin/npc/{npc_id}/memories - page {page}, limit {limit}")

        # Get all memories with location metadata
        all_memories = get_all_memories_with_location(npc_id, manager)
        total_memories = len(all_memories)

        # Calculate pagination
        total_pages = (total_memories + limit - 1) // limit if total_memories > 0 else 0

        # Validate page number
        if page > total_pages and total_memories > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": f"Page {page} out of range (total pages: {total_pages})",
                    "error_code": "INVALID_PAGINATION"
                }
            )

        # Calculate slice indices
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_memories = all_memories[start_idx:end_idx]

        logger.info(
            f"Returning page {page}/{total_pages} "
            f"({len(paginated_memories)}/{total_memories} memories) for {npc_id}"
        )

        return PaginatedMemories(
            npc_id=npc_id,
            page=page,
            limit=limit,
            total_memories=total_memories,
            total_pages=total_pages,
            memories=paginated_memories
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paginated memories for {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to retrieve paginated memories",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.put(
    "/memory/{npc_id}/{memory_id}",
    response_model=BaseResponse,
    status_code=200,
    summary="Update a memory",
    description="Update the content of a specific memory (searches all storage locations)."
)
async def update_memory(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    memory_id: str = Path(..., min_length=1, description="Memory identifier"),
    request: UpdateMemoryRequest = ...,
    manager: MemoryManager = Depends(get_memory_manager)
) -> BaseResponse:
    """
    Update a memory's content.

    Searches for the memory across recent, buffer, and longterm storage
    and updates it in the appropriate location. For longterm memories,
    regenerates the embedding.

    Args:
        npc_id: NPC identifier
        memory_id: Memory identifier
        request: Update request with new content
        manager: Injected MemoryManager dependency

    Returns:
        BaseResponse with success message
    """
    try:
        logger.info(f"PUT /admin/memory/{npc_id}/{memory_id} - updating content")

        # Find memory location
        result = find_memory_location(npc_id, memory_id, manager)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Memory {memory_id} not found for NPC {npc_id}",
                    "error_code": "MEMORY_NOT_FOUND"
                }
            )

        location, memory = result
        logger.info(f"Found memory {memory_id} in {location} storage")

        # Update based on location
        if location == "recent":
            # Update in-memory recent storage
            success = manager.recent_service.update_memory(
                npc_id=npc_id,
                memory_id=memory_id,
                new_content=request.content,
                new_metadata=request.metadata
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "Failed to update memory in recent storage",
                        "error_code": "UPDATE_FAILED"
                    }
                )
            logger.info(f"Updated memory {memory_id} in recent storage")

        elif location == "buffer":
            # Update buffer JSON file
            buffer_data = manager.longterm_service._load_buffer(npc_id)
            for mem_dict in buffer_data:
                if mem_dict.get('id') == memory_id:
                    mem_dict['content'] = request.content
                    mem_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
                    if request.metadata is not None:
                        mem_dict['metadata'] = request.metadata
                    break
            manager.longterm_service._save_buffer(npc_id, buffer_data)
            logger.info(f"Updated memory {memory_id} in buffer")

        elif location == "longterm":
            # Update in vector DB (will re-embed)
            success = manager.longterm_service.update_memory(
                npc_id=npc_id,
                memory_id=memory_id,
                new_content=request.content
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "Failed to update memory in longterm storage",
                        "error_code": "UPDATE_FAILED"
                    }
                )
            logger.info(f"Updated memory {memory_id} in longterm storage (re-embedded)")

        return BaseResponse(
            status="success",
            message=f"Memory {memory_id} updated successfully in {location} storage"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to update memory",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.delete(
    "/memory/{npc_id}/{memory_id}",
    response_model=BaseResponse,
    status_code=200,
    summary="Delete a memory",
    description="Delete a specific memory from any storage location."
)
async def delete_memory(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    memory_id: str = Path(..., min_length=1, description="Memory identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> BaseResponse:
    """
    Delete a specific memory.

    Searches for the memory across all storage locations and deletes it
    from the appropriate location.

    Args:
        npc_id: NPC identifier
        memory_id: Memory identifier
        manager: Injected MemoryManager dependency

    Returns:
        BaseResponse with success message
    """
    try:
        logger.warning(f"DELETE /admin/memory/{npc_id}/{memory_id} - deleting memory")

        # Find memory location
        result = find_memory_location(npc_id, memory_id, manager)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Memory {memory_id} not found for NPC {npc_id}",
                    "error_code": "MEMORY_NOT_FOUND"
                }
            )

        location, memory = result
        logger.info(f"Found memory {memory_id} in {location} storage")

        # Delete based on location
        if location == "recent":
            # Remove from recent storage
            success = manager.recent_service.delete_memory(npc_id, memory_id)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "Failed to delete memory from recent storage",
                        "error_code": "DELETE_FAILED"
                    }
                )
            logger.info(f"Deleted memory {memory_id} from recent storage")

        elif location == "buffer":
            # Remove from buffer JSON file
            buffer_data = manager.longterm_service._load_buffer(npc_id)
            buffer_data = [m for m in buffer_data if m.get('id') != memory_id]
            manager.longterm_service._save_buffer(npc_id, buffer_data)
            logger.info(f"Deleted memory {memory_id} from buffer")

        elif location == "longterm":
            # Delete from vector DB
            success = manager.longterm_service.delete_memory(npc_id, memory_id)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "Failed to delete memory from longterm storage",
                        "error_code": "DELETE_FAILED"
                    }
                )
            logger.info(f"Deleted memory {memory_id} from longterm storage")

        return BaseResponse(
            status="success",
            message=f"Memory {memory_id} deleted successfully from {location} storage"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to delete memory",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.post(
    "/npc/{npc_id}/embed-now",
    response_model=EmbedNowResult,
    status_code=200,
    summary="Force buffer embedding",
    description="Force immediate embedding of buffered memories to vector DB."
)
async def force_embed_buffer(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> EmbedNowResult:
    """
    Force immediate embedding of buffer to vector DB.

    Normally, the buffer auto-embeds when it reaches the threshold (10 items).
    This endpoint allows admin to force embedding even if threshold not reached.

    Args:
        npc_id: NPC identifier
        manager: Injected MemoryManager dependency

    Returns:
        EmbedNowResult with count of memories embedded
    """
    try:
        logger.info(f"POST /admin/npc/{npc_id}/embed-now - forcing buffer embed")

        # Check buffer count before embedding
        buffer_count_before = manager.longterm_service.get_buffer_count(npc_id)

        # Force embedding
        embedded_count = manager.force_embed_buffer(npc_id)

        buffer_was_empty = (buffer_count_before == 0)

        logger.info(
            f"Force embedded {embedded_count} memories for {npc_id} "
            f"(buffer was {'empty' if buffer_was_empty else 'not empty'})"
        )

        return EmbedNowResult(
            npc_id=npc_id,
            embedded_count=embedded_count,
            buffer_was_empty=buffer_was_empty
        )

    except Exception as e:
        logger.error(f"Error force embedding buffer for {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to force embed buffer",
                "error_code": "EMBEDDING_FAILED",
                "detail": str(e)
            }
        )


@router.delete(
    "/npc/{npc_id}/clear",
    response_model=ClearMemoryResult,
    status_code=200,
    summary="Clear all memories for NPC",
    description="Delete all memories (recent + buffer + longterm) for an NPC."
)
async def clear_npc_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> ClearMemoryResult:
    """
    Clear all memories for an NPC.

    This is a destructive operation that deletes all memories from
    recent, buffer, and longterm storage.

    Args:
        npc_id: NPC identifier
        manager: Injected MemoryManager dependency

    Returns:
        ClearMemoryResult with breakdown of deleted counts
    """
    try:
        logger.warning(f"DELETE /admin/npc/{npc_id}/clear - clearing ALL memories")

        # Clear all memories
        result = manager.clear_npc(npc_id)

        deleted_recent = result.get("recent", 0)
        deleted_buffer = result.get("buffer", 0)
        deleted_longterm = result.get("longterm", 0)
        total_deleted = result.get("total", 0)

        logger.warning(
            f"Cleared {total_deleted} total memories for {npc_id}: "
            f"{deleted_recent} recent, {deleted_buffer} buffer, {deleted_longterm} longterm"
        )

        return ClearMemoryResult(
            npc_id=npc_id,
            deleted_recent=deleted_recent,
            deleted_buffer=deleted_buffer,
            deleted_longterm=deleted_longterm,
            total_deleted=total_deleted
        )

    except Exception as e:
        logger.error(f"Error clearing memories for {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to clear memories",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.post(
    "/import",
    response_model=ImportResult,
    status_code=200,
    summary="Bulk import memories",
    description="Import multiple memories for an NPC from external data."
)
async def bulk_import_memories(
    request: BulkImportRequest,
    manager: MemoryManager = Depends(get_memory_manager)
) -> ImportResult:
    """
    Bulk import memories for an NPC.

    Imports multiple memories at once. Each memory goes through the normal
    flow (recent → buffer → longterm). Validates each memory individually
    and continues on errors (partial success is OK).

    Args:
        request: Bulk import request with NPC ID and list of memories
        manager: Injected MemoryManager dependency

    Returns:
        ImportResult with counts and error details
    """
    try:
        logger.info(
            f"POST /admin/import - importing {len(request.memories)} "
            f"memories for {request.npc_id}"
        )

        imported_count = 0
        failed_count = 0
        errors: List[str] = []

        for idx, memory_data in enumerate(request.memories):
            try:
                # Validate content (memory_data is a dict)
                content = memory_data.get("content", "")
                if len(content) < 1 or len(content) > 10000:
                    raise ValueError("content must be 1-10000 characters")

                metadata = memory_data.get("metadata")

                # Add to memory system
                result = manager.add_memory(request.npc_id, content, metadata)
                imported_count += 1

                logger.debug(f"Imported memory {idx} for {request.npc_id}: {result['memory_id']}")

            except Exception as e:
                failed_count += 1
                error_msg = f"Memory {idx}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Failed to import memory {idx} for {request.npc_id}: {e}")

        logger.info(
            f"Import complete for {request.npc_id}: "
            f"{imported_count} succeeded, {failed_count} failed"
        )

        return ImportResult(
            npc_id=request.npc_id,
            imported_count=imported_count,
            failed_count=failed_count,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error during bulk import for {request.npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to bulk import memories",
                "error_code": "IMPORT_FAILED",
                "detail": str(e)
            }
        )


@router.get(
    "/export/{npc_id}",
    response_model=ExportData,
    status_code=200,
    summary="Export memories",
    description="Export all memories for an NPC as JSON."
)
async def export_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> ExportData:
    """
    Export all memories for an NPC.

    Returns all memories (recent + buffer + longterm) with location metadata
    in a JSON format suitable for backup or migration.

    Args:
        npc_id: NPC identifier
        manager: Injected MemoryManager dependency

    Returns:
        ExportData with all memories and export metadata
    """
    try:
        logger.info(f"GET /admin/export/{npc_id} - exporting all memories")

        # Get all memories with location metadata
        all_memories = get_all_memories_with_location(npc_id, manager)

        export_data = ExportData(
            npc_id=npc_id,
            exported_at=datetime.now(timezone.utc),
            total_memories=len(all_memories),
            memories=all_memories
        )

        logger.info(f"Exported {len(all_memories)} memories for {npc_id}")

        return export_data

    except Exception as e:
        logger.error(f"Error exporting memories for {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to export memories",
                "error_code": "EXPORT_FAILED",
                "detail": str(e)
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=200,
    summary="System health check",
    description="Check overall system health and component status."
)
async def health_check(
    manager: MemoryManager = Depends(get_memory_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> HealthResponse:
    """
    Check system health.

    Checks the status of all major components:
    - Embedding service (loaded/unloaded)
    - ChromaDB (connected/disconnected)
    - Recent memory service (operational/unavailable)

    Args:
        manager: Injected MemoryManager dependency
        embedding_service: Injected EmbeddingService dependency

    Returns:
        HealthResponse with component statuses
    """
    try:
        logger.info("GET /admin/health - checking system health")

        health_status = {
            "status": "healthy",
            "embedding_service": "unknown",
            "chromadb": "unknown",
            "recent_memory": "unknown"
        }

        # Check embedding service
        try:
            if embedding_service.is_loaded():
                health_status["embedding_service"] = "loaded"
            else:
                health_status["embedding_service"] = "unloaded"
                health_status["status"] = "degraded"
        except Exception as e:
            logger.warning(f"Embedding service check failed: {e}")
            health_status["embedding_service"] = "error"
            health_status["status"] = "unhealthy"

        # Check ChromaDB
        try:
            if _chroma_client:
                _chroma_client.list_collections()
                health_status["chromadb"] = "connected"
            else:
                health_status["chromadb"] = "disconnected"
                health_status["status"] = "unhealthy"
        except Exception as e:
            logger.warning(f"ChromaDB check failed: {e}")
            health_status["chromadb"] = "disconnected"
            health_status["status"] = "unhealthy"

        # Check recent memory service
        try:
            # Simple check - try to get count for non-existent NPC
            manager.recent_service.get_count("_health_check_test")
            health_status["recent_memory"] = "operational"
        except Exception as e:
            logger.warning(f"Recent memory check failed: {e}")
            health_status["recent_memory"] = "error"
            health_status["status"] = "unhealthy"

        logger.info(f"Health check complete: {health_status['status']}")

        return HealthResponse(**health_status)

    except Exception as e:
        logger.error(f"Error during health check: {e}", exc_info=True)
        # Still return a response indicating unhealthy
        return HealthResponse(
            status="unhealthy",
            embedding_service="error",
            chromadb="error",
            recent_memory="error"
        )

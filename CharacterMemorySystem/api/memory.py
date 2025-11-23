"""
Memory API Endpoints - REST API for NPC memory operations.

This module provides FastAPI endpoints for managing NPC memories:
- Add new memories
- Retrieve recent memories
- Search for semantically similar memories
- Get combined context (recent + relevant)
- Clear all memories for an NPC
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from models.requests import AddMemoryRequest, SearchMemoryRequest
from models.responses import (
    AddMemoryResponse,
    RecentMemoryResponse,
    SearchMemoryResponse,
    ContextResponse,
    BaseResponse,
    ErrorResponse
)
from models.memory import MemoryEntry, SimilarMemory
from models.memory import MemoryEntry, SimilarMemory
from services.memory_manager import MemoryManager
from config import settings

logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(
    prefix="/memory",
    tags=["Memory Operations"],
    responses={
        404: {"description": "Memory not found", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse}
    }
)

# Global memory manager instance (set during application startup)
_memory_manager: Optional[MemoryManager] = None


def set_memory_manager(manager: MemoryManager) -> None:
    """
    Set the global memory manager instance.

    This function is called during application startup to inject
    the MemoryManager dependency.

    Args:
        manager: The MemoryManager instance to use
    """
    global _memory_manager
    _memory_manager = manager
    logger.info("Memory Manager dependency injected successfully")


def get_memory_manager() -> MemoryManager:
    """
    Dependency function for injecting MemoryManager into routes.

    Returns:
        MemoryManager: The global memory manager instance

    Raises:
        HTTPException: If memory manager is not initialized (503)
    """
    if _memory_manager is None:
        logger.error("Memory Manager not initialized - startup may have failed")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Memory Manager not initialized",
                "error_code": "SERVICE_UNAVAILABLE"
            }
        )
    return _memory_manager


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/{npc_id}",
    response_model=AddMemoryResponse,
    status_code=201,
    summary="Add a new memory",
    description="Add a new memory for an NPC. Returns the memory ID and eviction status."
)
async def add_memory(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    request: AddMemoryRequest = ...,
    manager: MemoryManager = Depends(get_memory_manager)
) -> AddMemoryResponse:
    """
    Add a new memory for an NPC.

    The memory will be added to the NPC's recent memory queue (FIFO, max 5).
    If the queue is full, the oldest memory will be evicted to the long-term buffer.

    Args:
        npc_id: Unique identifier for the NPC
        request: Memory content and optional metadata
        manager: Injected MemoryManager dependency

    Returns:
        AddMemoryResponse with memory_id and eviction status

    Raises:
        HTTPException: 400 for validation errors, 500 for internal errors
    """
    try:
        logger.info(f"Adding memory for NPC: {npc_id}")

        # Add memory via manager
        result = manager.add_memory(
            npc_id=npc_id,
            content=request.content,
            metadata=request.metadata
        )

        # Build response
        response = AddMemoryResponse(
            status="success",
            message=f"Memory added successfully for NPC {npc_id}",
            memory_id=result["memory_id"],
            stored_in=result["stored_in"],
            evicted_to_buffer=result.get("evicted_to_buffer", False)
        )

        # Add buffer auto-embed info if present
        if result.get("buffer_auto_embedded"):
            response.message += " (buffer auto-embedded to vector DB)"

        logger.info(
            f"Memory {result['memory_id']} added for NPC {npc_id}, "
            f"evicted: {result.get('evicted_to_buffer', False)}"
        )

        return response

    except ValueError as e:
        logger.warning(f"Validation error adding memory for NPC {npc_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Error adding memory for NPC {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to add memory",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.get(
    "/{npc_id}",
    response_model=RecentMemoryResponse,
    status_code=200,
    summary="Get recent memories",
    description="Retrieve the most recent memories for an NPC (up to 5)."
)
async def get_recent_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> RecentMemoryResponse:
    """
    Get recent memories for an NPC.

    Returns the NPC's recent memory queue (FIFO, max 5 items).
    If the NPC has no memories, returns an empty list.

    Args:
        npc_id: Unique identifier for the NPC
        manager: Injected MemoryManager dependency

    Returns:
        RecentMemoryResponse with list of recent memories

    Raises:
        HTTPException: 500 for internal errors
    """
    try:
        logger.info(f"Fetching recent memories for NPC: {npc_id}")

        # Get context without query (only recent memories)
        context = manager.get_context(npc_id=npc_id, query=None)

        memories = context.get("recent", [])
        count = context.get("recent_count", 0)

        logger.info(f"Retrieved {count} recent memories for NPC {npc_id}")

        return RecentMemoryResponse(
            status="success",
            message=f"Retrieved {count} recent memories",
            npc_id=npc_id,
            memories=memories,
            count=count
        )

    except Exception as e:
        logger.error(f"Error fetching recent memories for NPC {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to retrieve recent memories",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.get(
    "/{npc_id}/search",
    response_model=SearchMemoryResponse,
    status_code=200,
    summary="Search for similar memories",
    description="Search for semantically similar memories in long-term storage using vector embeddings."
)
async def search_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    top_k: int = Query(settings.similarity_search_results, ge=1, le=20, description="Number of results to return"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> SearchMemoryResponse:
    """
    Search for semantically similar memories in long-term storage.

    Uses vector embeddings to find memories semantically similar to the query.
    Only searches long-term memory (embedded memories), not recent memory or buffer.

    Args:
        npc_id: Unique identifier for the NPC
        query: Search query text
        top_k: Number of similar memories to return (default 3, max 20)
        manager: Injected MemoryManager dependency

    Returns:
        SearchMemoryResponse with list of similar memories and scores

    Raises:
        HTTPException: 400 for validation, 404 if no memories, 500 for errors
    """
    try:
        logger.info(f"Searching memories for NPC {npc_id} with query: '{query[:50]}...'")

        # Search long-term memory
        results = manager.search_longterm(
            npc_id=npc_id,
            query=query,
            top_k=top_k
        )

        count = len(results)
        logger.info(f"Found {count} similar memories for NPC {npc_id}")

        return SearchMemoryResponse(
            status="success",
            message=f"Found {count} similar memories",
            npc_id=npc_id,
            query=query,
            results=results,
            count=count
        )

    except ValueError as e:
        logger.warning(f"Validation error searching memories for NPC {npc_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Error searching memories for NPC {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to search memories",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.get(
    "/{npc_id}/context",
    response_model=ContextResponse,
    status_code=200,
    summary="Get combined context",
    description="Get both recent memories and semantically relevant memories for context."
)
async def get_context(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    query: Optional[str] = Query(None, min_length=1, max_length=1000, description="Optional search query for semantic search"),
    top_k: int = Query(3, ge=1, le=20, description="Number of relevant results if query provided"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> ContextResponse:
    """
    Get combined context for an NPC.

    Returns both:
    - Recent memories (FIFO queue, up to 5)
    - Relevant memories (semantically similar, only if query provided)

    This endpoint is useful for providing full context to an LLM agent.

    Args:
        npc_id: Unique identifier for the NPC
        query: Optional search query for semantic search
        top_k: Number of relevant memories to return if query provided
        manager: Injected MemoryManager dependency

    Returns:
        ContextResponse with recent and relevant memories

    Raises:
        HTTPException: 400 for validation, 500 for errors
    """
    try:
        logger.info(
            f"Getting context for NPC {npc_id}, "
            f"query: {'Yes' if query else 'No'}, top_k: {top_k}"
        )

        # Get combined context
        context = manager.get_context(
            npc_id=npc_id,
            query=query,
            top_k=top_k if query else 0
        )

        recent = context.get("recent", [])
        relevant = context.get("relevant", [])
        recent_count = context.get("recent_count", 0)
        relevant_count = context.get("relevant_count", 0)

        logger.info(
            f"Context for NPC {npc_id}: {recent_count} recent, "
            f"{relevant_count} relevant"
        )

        return ContextResponse(
            status="success",
            message=f"Retrieved context: {recent_count} recent, {relevant_count} relevant",
            npc_id=npc_id,
            recent=recent,
            relevant=relevant,
            recent_count=recent_count,
            relevant_count=relevant_count
        )

    except ValueError as e:
        logger.warning(f"Validation error getting context for NPC {npc_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Error getting context for NPC {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to get context",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )


@router.delete(
    "/{npc_id}",
    response_model=BaseResponse,
    status_code=200,
    summary="Clear all memories",
    description="Clear all memories for an NPC (recent + buffer + long-term)."
)
async def clear_memories(
    npc_id: str = Path(..., min_length=1, description="NPC identifier"),
    manager: MemoryManager = Depends(get_memory_manager)
) -> BaseResponse:
    """
    Clear all memories for an NPC.

    Deletes:
    - Recent memories (FIFO queue)
    - Buffer memories (pending embedding)
    - Long-term memories (vector DB)

    This operation is irreversible.

    Args:
        npc_id: Unique identifier for the NPC
        manager: Injected MemoryManager dependency

    Returns:
        BaseResponse with counts of deleted memories

    Raises:
        HTTPException: 500 for internal errors
    """
    try:
        logger.warning(f"Clearing all memories for NPC: {npc_id}")

        # Clear all memories
        result = manager.clear_npc(npc_id)

        total = result.get("total", 0)
        recent = result.get("recent", 0)
        buffer = result.get("buffer", 0)
        longterm = result.get("longterm", 0)

        logger.info(
            f"Cleared {total} total memories for NPC {npc_id}: "
            f"{recent} recent, {buffer} buffer, {longterm} long-term"
        )

        return BaseResponse(
            status="success",
            message=(
                f"Cleared {total} total memories for NPC {npc_id}: "
                f"{recent} recent, {buffer} buffer, {longterm} long-term"
            )
        )

    except Exception as e:
        logger.error(f"Error clearing memories for NPC {npc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to clear memories",
                "error_code": "INTERNAL_ERROR",
                "detail": str(e)
            }
        )

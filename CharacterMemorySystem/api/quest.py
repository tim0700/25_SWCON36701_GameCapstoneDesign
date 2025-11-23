"""
Quest Generation API Endpoints.

Provides REST API endpoints for Unity to generate quests with automatic
memory saving to CharacterMemorySystem.

Integration of Backend2 functionality into CharacterMemorySystem.
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from services.quest_generator import QuestGeneratorService, QuestContext, get_quest_generator
from services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/quest",
    tags=["Quest Generation"]
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
    logger.info("Quest API: Memory Manager dependency injected")


def get_memory_manager() -> MemoryManager:
    """
    Dependency function for injecting MemoryManager into routes.
    
    Returns:
        MemoryManager: The global memory manager instance
    
    Raises:
        HTTPException: If memory manager is not initialized (503)
    """
    if _memory_manager is None:
        logger.error("Quest API: Memory Manager not initialized - startup may have failed")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Memory Manager not initialized",
                "error_code": "SERVICE_UNAVAILABLE"
            }
        )
    return _memory_manager


@router.post("/generate")
async def generate_quest(
    context: QuestContext,
    quest_gen: QuestGeneratorService = Depends(get_quest_generator),
    memory_mgr: MemoryManager = Depends(get_memory_manager)
):
    """
    Generate a quest from game context (Unity request).
    
    This endpoint:
    1. Receives quest context from Unity (NPCs, location, monster, dungeon, player dialogue)
    2. Generates quest JSON using Gemini AI
    3. Automatically saves quest memory to NPC's memory system (direct call)
    4. Returns quest JSON to Unity
    
    Args:
        context: Quest generation context from Unity
        quest_gen: Quest generator service (dependency injection)
        memory_mgr: Memory manager service (dependency injection)
    
    Returns:
        {
            "quest_json": "...",     # Quest JSON string for Unity
            "memory_saved": bool     # Whether memory was saved successfully
        }
    
    Raises:
        HTTPException: If quest generation fails
    """
    try:
        logger.info(f"Quest generation request for NPC {context.npc1_id}")
        
        # Generate quest using Gemini
        result = await quest_gen.generate_quest(context)
        
        # Save memory DIRECTLY (no HTTP call!)
        memory_saved = False
        if result.get("memory_data"):
            try:
                memory_data = result["memory_data"]
                npc_id = memory_data.get("npc_id")
                content = memory_data.get("content")
                
                if npc_id and content:
                    # Direct internal call to memory manager
                    memory_mgr.add_memory(
                        npc_id=npc_id,
                        content=content,
                        metadata={
                            "source": "quest_generation",
                            "quest_giver": npc_id,
                            "player_dialogue": context.player_dialogue if context.player_dialogue else None
                        }
                    )
                    memory_saved = True
                    logger.info(f"Quest memory saved for NPC {npc_id}")
                else:
                    logger.warning(f"Invalid memory data: npc_id={npc_id}, content={content}")
                    
            except Exception as e:
                logger.warning(f"Failed to save quest memory: {e}")
                # Don't fail quest generation if memory save fails
        
        # Return quest JSON to Unity
        return {
            "quest_json": json.dumps(result["quest_data"]),
            "memory_saved": memory_saved
        }
        
    except Exception as e:
        logger.error(f"Quest generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quest generation failed: {str(e)}"
        )


@router.get("/health")
async def quest_health_check():
    """
    Health check endpoint for quest generation service.
    
    Returns:
        Status of quest generation service
    """
    from config import settings
    
    return {
        "status": "healthy" if settings.quest_generation_enabled else "disabled",
        "model": settings.gemini_model,
        "project": settings.google_cloud_project
    }

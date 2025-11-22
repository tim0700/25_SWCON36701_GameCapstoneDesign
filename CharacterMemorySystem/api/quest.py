"""
Quest Generation API - REST API for AI-powered quest generation.

This module provides FastAPI endpoints for generating quests using Google's
Gemini LLM via Vertex AI. Generated quests automatically save related memories
to the NPC memory system.
"""
import logging
import json
import re
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from vertexai.generative_models import GenerativeModel, Part

from config import settings
from models.quest import QuestContext, QuestGenerationResponse
from services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER & DEPENDENCY INJECTION
# ============================================================================

router = APIRouter(prefix="/quest")

# Global memory manager instance (injected during startup)
_memory_manager: Optional[MemoryManager] = None


def set_memory_manager(manager: MemoryManager) -> None:
    """
    Set the global memory manager instance.
    
    Called during application startup to inject dependencies.
    """
    global _memory_manager
    _memory_manager = manager
    logger.info("Memory manager injected into quest router")


def get_memory_manager() -> MemoryManager:
    """Get memory manager dependency."""
    if _memory_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Memory manager not initialized"
        )
    return _memory_manager


# ============================================================================
# QUEST PROMPT TEMPLATE
# ============================================================================

QUEST_JSON_FORMAT_EXAMPLE = """
{
  "quest_title": "Example: Clear the Ruins",
  "quest_giver_npc_id": "NPC_ID_1",
  "quest_type": "SIDE_QUEST",
  "quest_summary": "A quest to clear out monsters and investigate a dungeon.",
  "quest_steps": [
    {
      "step_id": 1,
      "objective_type": "TALK",
      "description_for_player": "Talk to 'NPC Name 2'.",
      "dialogues": {
        "on_start": [{"speaker_id": "NPC_ID_1", "line": "Go talk to NPC 2."}],
        "on_complete": []
      },
      "details": {"target_npc_id": "NPC_ID_2"}
    },
    {
      "step_id": 2,
      "objective_type": "KILL",
      "description_for_player": "Defeat the Monster.",
      "dialogues": {
        "on_start": [{"speaker_id": "NPC_ID_2", "line": "A monster is attacking!"}],
        "on_complete": []
      },
      "details": {"target_monster_id": "MONSTER_ID_1"}
    },
    {
      "step_id": 3,
      "objective_type": "DUNGEON",
      "description_for_player": "Clear the Dungeon.",
      "dialogues": {
        "on_start": [{"speaker_id": "player_character", "line": "Monster is gone, now for the dungeon."}],
        "on_complete": []
      },
      "details": {"target_dungeon_id": "DUNGEON_ID_1"}
    }
  ],
  "quest_rewards": []
  },
  "memory_data": {
    "npc_id": "NPC_ID_1",
    "content": "Quest requested by NPC_ID_1 (Name) to Player. Task: Go to LOCATION_ID_1 (Name). Goal: Clear monsters. Status: Started."
  }
}
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def call_gemini_async(prompt_text: str) -> str:
    """
    Call Gemini LLM to generate content.
    
    Args:
        prompt_text: The prompt to send to Gemini
        
    Returns:
        Generated text with code blocks removed
    """
    model = GenerativeModel(settings.vertex_model_name)
    response = await model.generate_content_async([Part.from_text(prompt_text)])
    quest_json_string = response.text
    
    # Remove code block markers if present
    if "```json" in quest_json_string:
        quest_json_string = quest_json_string.split("```json")[1].split("```")[0]
    elif "```" in quest_json_string:
        quest_json_string = quest_json_string.split("```")[1].split("```")[0]
    
    return quest_json_string.strip()


def fix_common_json_errors(json_str: str, context: QuestContext) -> str:
    """
    Fix common JSON formatting errors using regex.
    
    Args:
        json_str: Raw JSON string from LLM
        context: Quest context for fixing speaker IDs
        
    Returns:
        Corrected JSON string
    """
    corrected_str = json_str
    try:
        # Fix "on_start": ["dialogue"] pattern to proper format
        pattern = r'("on_start"\s*:\s*\[\s*)"([\s\S]*?)"(\s*\])'
        replacement = f'\\1{{"speaker_id": "{context.npc1_id}", "line": "\\2"}}\\3'
        corrected_str = re.sub(pattern, replacement, corrected_str, flags=re.IGNORECASE)
    except Exception as e:
        logger.warning(f"JSON correction failed: {e}")
        return json_str
    return corrected_str


def create_retry_prompt(original_prompt: str, bad_json: str, error_message: str) -> str:
    """
    Create a retry prompt for when quest generation fails.
    
    Args:
        original_prompt: Original generation prompt
        bad_json: The malformed JSON that failed
        error_message: Error message from parsing failure
        
    Returns:
        Retry prompt asking for correction
    """
    return f"""
    Your previous JSON generation failed. Error: {error_message}
    Failed JSON: {bad_json}
    Please correct the JSON structure. 
    Ensure you generate a ROOT object containing both "quest_data" and "memory_data".
    Original Instructions: {original_prompt}
    """


def create_quest_prompt(context: QuestContext) -> str:
    """
    Build quest generation prompt dynamically based on context.
    
    Args:
        context: Quest context with NPC, location, dungeon, monster info
        
    Returns:
        Complete prompt for Gemini
    """
    elements = [
        f"- Quest Giver (NPC 1): ID: {context.npc1_id}, Name: {context.npc1_name}",
        f"- Target NPC (NPC 2): ID: {context.npc2_id}, Name: {context.npc2_name}",
        f"- Target Location: ID: {context.location_id}, Name: {context.location_name}"
    ]
    
    rules = [
        f"1. The `quest_giver_npc_id` inside `quest_data` MUST be \"{context.npc1_id}\".",
        f"2. `quest_data` MUST follow the Unity quest structure rules (GOTO/TALK types).",
        f"3. `memory_data.npc_id` MUST be \"{context.npc1_id}\"."
    ]

    # Add optional monster objective
    if context.monster_id:
        rules.append(f"4. `quest_data` MAY use KILL type with target_monster_id: \"{context.monster_id}\".")
        elements.append(f"- Target Monster: ID: {context.monster_id}")
    else:
        rules.append("4. DO NOT use KILL type.")

    # Add optional dungeon objective
    if context.dungeon_id:
        rules.append(f"5. `quest_data` MAY use DUNGEON type with target_dungeon_id: \"{context.dungeon_id}\".")
        elements.append(f"- Target Dungeon: ID: {context.dungeon_id}")
    else:
        rules.append("5. DO NOT use DUNGEON type.")

    elements_str = "\n    ".join(elements)
    rules_str = "\n    ".join(rules)

    return f"""
    You are a quest designer. Generate a JSON response containing TWO parts: "quest_data" and "memory_data".

    *** INPUT ELEMENTS ***
    {elements_str}

    *** CRITICAL RULES ***
    {rules_str}
    6. The OUTPUT MUST be a single JSON object with two keys: "quest_data" and "memory_data".
    7. "quest_data": The standard quest JSON for the game engine.
    8. "memory_data": Information for the NPC's long-term vector memory.
    
    9. (!!!) LANGUAGE RULE: All content (Quest Title, Summary, Dialogues, Descriptions, Memory Content) MUST BE IN ENGLISH. Do NOT use Korean.

    *** JSON OUTPUT FORMAT ***
    {QUEST_JSON_FORMAT_EXAMPLE}

    Generate the JSON now.
    """


def save_memory_direct(memory_data: dict, manager: MemoryManager) -> bool:
    """
    Save quest-related memory directly to memory manager.
    
    This replaces the HTTP-based save_memory_log from Backend2.
    Now it's a direct function call - faster and more reliable.
    
    Args:
        memory_data: {"npc_id": str, "content": str}
        manager: Memory manager instance
        
    Returns:
        True if saved successfully, False otherwise
    """
    npc_id = memory_data.get("npc_id")
    content = memory_data.get("content")
    
    if not npc_id or not content:
        logger.error(f"Invalid memory data: npc_id={npc_id}, content={content}")
        return False
    
    try:
        logger.info(f"Saving quest memory for NPC: {npc_id}")
        
        # Direct call to memory manager (no HTTP!)
        result = manager.add_memory(
            npc_id=npc_id,
            content=content,
            metadata={
                "source": "quest_generation",
                "quest_giver": npc_id
            }
        )
        
        logger.info(
            f"✅ Quest memory saved successfully (ID: {result['memory_id']}, "
            f"stored_in: {result['stored_in']})"
        )
        return True
        
    except Exception as e:
        logger.error(f"Failed to save quest memory: {type(e).__name__}: {e}")
        return False


# ============================================================================
# API ENDPOINT
# ============================================================================

@router.post("/generate", response_model=QuestGenerationResponse)
async def generate_quest(context: QuestContext) -> QuestGenerationResponse:
    """
    Generate a quest using AI based on provided context.
    
    This endpoint:
    1. Builds a dynamic prompt from context
    2. Calls Gemini LLM to generate quest data
    3. Parses and validates the response
    4. Automatically saves quest-related memory to NPC
    5. Returns quest data to Unity client
    
    Args:
        context: Quest context with NPC, location, dungeon, monster info
        
    Returns:
        QuestGenerationResponse with quest_json string
        
    Raises:
        HTTPException: 500 if generation fails after retries
    """
    logger.info(
        f"Quest generation requested: quest_giver={context.npc1_id}, "
        f"location={context.location_id}"
    )
    
    memory_manager = get_memory_manager()
    original_prompt = create_quest_prompt(context)
    
    try:
        # First attempt
        logger.debug("Quest generation attempt 1")
        raw_response = await call_gemini_async(original_prompt)
        
        # Fix common errors
        fixed_response = fix_common_json_errors(raw_response, context)

        try:
            # Parse JSON
            root_json = json.loads(fixed_response)
            
            # Extract quest_data and memory_data
            quest_data = root_json.get("quest_data")
            memory_data = root_json.get("memory_data")

            if not quest_data or not memory_data:
                raise ValueError("JSON must contain both 'quest_data' and 'memory_data' keys.")

            # Save memory (direct call, no HTTP!)
            save_memory_direct(memory_data, memory_manager)

            # Return quest data to Unity
            quest_json_string = json.dumps(quest_data)
            
            logger.info("✅ Quest generated successfully")
            return QuestGenerationResponse(quest_json=quest_json_string)

        except Exception as e_parse1:
            # Retry on parse failure
            logger.warning(f"Parse failed (attempt 1): {e_parse1}. Retrying...")
            retry_prompt = create_retry_prompt(original_prompt, raw_response, str(e_parse1))
            
            raw_response_v2 = await call_gemini_async(retry_prompt)
            fixed_response_v2 = fix_common_json_errors(raw_response_v2, context)
            
            try:
                root_json_v2 = json.loads(fixed_response_v2)
                
                quest_data_v2 = root_json_v2.get("quest_data")
                memory_data_v2 = root_json_v2.get("memory_data")
                
                if not quest_data_v2 or not memory_data_v2:
                    raise ValueError("Missing keys in retry response.")

                save_memory_direct(memory_data_v2, memory_manager)
                
                quest_json_string_v2 = json.dumps(quest_data_v2)
                logger.info("✅ Quest generated successfully (after retry)")
                return QuestGenerationResponse(quest_json=quest_json_string_v2)
            
            except Exception as e_parse2:
                logger.error(f"Parse failed (attempt 2): {e_parse2}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Quest generation failed after retry: {str(e_parse2)}"
                )

    except HTTPException:
        raise
    except Exception as e_initial:
        logger.error(f"Quest generation error: {e_initial}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quest generation failed: {str(e_initial)}"
        )

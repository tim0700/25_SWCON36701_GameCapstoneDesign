"""
Quest Generation Service using Google Gemini API.

This service handles:
- Quest context processing from Unity
- Gemini API interaction via Vertex AI
- Quest JSON generation with retry logic
- Player dialogue integration
- Error correction and validation

Integrated from Backend2 into CharacterMemorySystem.
"""
import json
import re
import logging
from typing import Dict, Any, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, Part
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# QUEST CONTEXT MODEL
# ============================================================================

class QuestContext(BaseModel):
    """Quest generation context received from Unity."""
    npc1_id: str
    npc1_name: str
    npc1_desc: str
    npc2_id: str
    npc2_name: str
    npc2_desc: str
    location_id: str
    location_name: str
    dungeon_id: str
    monster_id: str
    player_dialogue: str = ""  # Player's dialogue input (optional)
    recent_memories_json: Optional[str] = None
    search_results_json: Optional[str] = None


# ============================================================================
# QUEST JSON FORMAT EXAMPLE
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
# QUEST GENERATOR SERVICE
# ============================================================================

class QuestGeneratorService:
    """Service for generating quests using Gemini AI."""
    
    def __init__(self):
        """Initialize Vertex AI and Gemini model."""
        if not settings.quest_generation_enabled:
            logger.warning("Quest generation is disabled in settings")
            return
        
        # Initialize Vertex AI
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location
        )
        
        self.model = GenerativeModel(settings.gemini_model)
        logger.info(f"Quest generator initialized: {settings.gemini_model} @ {settings.google_cloud_project}")
    
    async def generate_quest(self, context: QuestContext) -> Dict[str, Any]:
        """
        Generate quest JSON from game context.
        
        Args:
            context: Quest generation context from Unity
        
        Returns:
            {
                "quest_data": {...},  # Quest JSON for Unity
                "memory_data": {...}  # Memory to save to CharacterMemorySystem
            }
        
        Raises:
            Exception: If quest generation fails after retry
        """
        prompt = self._create_quest_prompt(context)
        
        try:
            # First attempt
            logger.info(f"Generating quest for NPC {context.npc1_id}")
            raw_response = await self._call_gemini(prompt)
            quest_json = self._parse_and_validate(raw_response, context)
            
            logger.info("Quest generated successfully")
            return quest_json
            
        except Exception as e:
            # Retry logic with error feedback
            logger.warning(f"First attempt failed: {e}. Retrying with error feedback...")
            retry_prompt = self._create_retry_prompt(prompt, raw_response, str(e))
            
            try:
                raw_response_v2 = await self._call_gemini(retry_prompt)
                quest_json = self._parse_and_validate(raw_response_v2, context)
                
                logger.info("Quest generated successfully on retry")
                return quest_json
                
            except Exception as e2:
                logger.error(f"Quest generation failed after retry: {e2}")
                raise Exception(f"Quest generation failed: {e2}")
    
    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with prompt.
        
        Args:
            prompt: Formatted prompt string
        
        Returns:
            Raw response text from Gemini
        """
        response = await self.model.generate_content_async([Part.from_text(prompt)])
        response_text = response.text
        
        # Remove code fences if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        return response_text.strip()
    
    def _create_quest_prompt(self, context: QuestContext) -> str:
        """
        Create prompt for Gemini with game context.
        
        Generates dynamic prompt based on available game elements.
        """
        elements = [
            f"- Quest Giver (NPC 1): ID: {context.npc1_id}, Name: {context.npc1_name}",
            f"- Target NPC (NPC 2): ID: {context.npc2_id}, Name: {context.npc2_name}",
            f"- Target Location: ID: {context.location_id}, Name: {context.location_name}"
        ]
        
        # NOTE: player_dialogue는 벡터 검색 쿼리로만 사용됨 (프롬프트에 직접 포함 안 함)
        # 검색 결과는 아래 memory_section을 통해 프롬프트에 포함됨
        
        # Add memory section if memory data is provided
        memory_section = ""
        if context.recent_memories_json or context.search_results_json:
            memory_section = """
    *** NPC MEMORY CONTEXT ***
    The NPC has memories of past interactions with the player. Use this information to create a quest that feels personalized and references past events.
    """
            
            # Parse and add recent memories
            if context.recent_memories_json:
                try:
                    recent_data = json.loads(context.recent_memories_json)
                    if recent_data.get("memories") and len(recent_data["memories"]) > 0:
                        memory_section += "\n    Recent Memories (Most Recent First):\n"
                        for mem in recent_data["memories"]:
                            timestamp = mem.get("timestamp", "Unknown time")
                            content = mem.get("content", "")
                            memory_section += f"    - [{timestamp}] {content}\n"
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse recent_memories_json: {e}")
            
            # Parse and add search results (relevant memories)
            if context.search_results_json:
                try:
                    search_data = json.loads(context.search_results_json)
                    if search_data.get("results") and len(search_data["results"]) > 0:
                        memory_section += "\n    Relevant Past Memories (Sorted by Relevance):\n"
                        for result in search_data["results"]:
                            mem = result.get("memory", {})
                            score = result.get("similarity_score", 0.0)
                            content = mem.get("content", "")
                            memory_section += f"    - [Similarity: {score:.2f}] {content}\n"
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse search_results_json: {e}")
            
            memory_section += """
    IMPORTANT: Incorporate these memories naturally into the quest narrative. For example:
    - Reference past events in NPC dialogues
    - Create quests that follow up on previous interactions
    - Reward the player for past achievements or address past failures
    """
        
        rules = [
            f'1. The `quest_giver_npc_id` inside `quest_data` MUST be "{context.npc1_id}".',
            f'2. `quest_data` MUST follow the Unity quest structure rules (GOTO/TALK types).',
            f'3. `memory_data.npc_id` MUST be "{context.npc1_id}".'
        ]
        
        # Dynamic rules based on available game elements
        if context.monster_id:
            rules.append(f'4. `quest_data` MAY use KILL type with target_monster_id: "{context.monster_id}".')
            elements.append(f"- Target Monster: ID: {context.monster_id}")
        else:
            rules.append("4. DO NOT use KILL type.")
        
        if context.dungeon_id:
            rules.append(f'5. `quest_data` MAY use DUNGEON type with target_dungeon_id: "{context.dungeon_id}".')
            elements.append(f"- Target Dungeon: ID: {context.dungeon_id}")
        else:
            rules.append("5. DO NOT use DUNGEON type.")
        
        elements_str = "\\n    ".join(elements)
        rules_str = "\\n    ".join(rules)
        
        return f"""
    You are a quest designer. Generate a JSON response containing TWO parts: "quest_data" and "memory_data".
    {memory_section}
    
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
    
    def _parse_and_validate(self, json_str: str, context: QuestContext) -> Dict:
        """
        Parse and validate JSON response from Gemini.
        
        Args:
            json_str: Raw JSON string from Gemini
            context: Original quest context for error fixing
        
        Returns:
            Validated JSON dict with quest_data and memory_data
        
        Raises:
            ValueError: If JSON is invalid or missing required keys
        """
        # Fix common formatting errors
        fixed = self._fix_common_errors(json_str, context)
        
        # Parse JSON
        try:
            data = json.loads(fixed)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        # Validate structure
        if "quest_data" not in data:
            raise ValueError("Missing 'quest_data' key in response")
        if "memory_data" not in data:
            raise ValueError("Missing 'memory_data' key in response")
        
        return data
    
    def _fix_common_errors(self, json_str: str, context: QuestContext) -> str:
        """
        Fix common JSON formatting errors using regex.
        
        Specifically fixes dialogue array format issues.
        """
        corrected_str = json_str
        
        try:
            # Fix "on_start": [ "dialogue text" ] -> proper format
            pattern = r'("on_start"\\s*:\\s*\\[\\s*)"([\\s\\S]*?)"(\\s*\\])'
            replacement = f'\\1{{"speaker_id": "{context.npc1_id}", "line": "\\2"}}\\3'
            corrected_str = re.sub(pattern, replacement, corrected_str, flags=re.IGNORECASE)
        except Exception as e:
            logger.warning(f"Error while fixing JSON: {e}")
            return json_str
        
        return corrected_str
    
    def _create_retry_prompt(self, original_prompt: str, bad_json: str, error_message: str) -> str:
        """
        Create retry prompt with error feedback.
        
        Args:
            original_prompt: The original prompt that failed
            bad_json: The invalid JSON that was generated
            error_message: Error message from parsing
        
        Returns:
            New prompt with error feedback
        """
        return f"""
    Your previous JSON generation failed. Error: {error_message}
    Failed JSON: {bad_json}
    
    Please correct the JSON structure. 
    Ensure you generate a ROOT object containing both "quest_data" and "memory_data".
    
    Original Instructions: {original_prompt}
    """


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_quest_generator_instance = None

def get_quest_generator() -> QuestGeneratorService:
    """Get or create singleton quest generator instance."""
    global _quest_generator_instance
    
    if _quest_generator_instance is None:
        _quest_generator_instance = QuestGeneratorService()
    
    return _quest_generator_instance

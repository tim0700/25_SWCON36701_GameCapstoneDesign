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
from typing import Dict, Any, Optional, List
import random # 임시로 테스트할때 랜덤으로 고르기 위해 추가 

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
    # Quest Giver NPC (NPC1)
    quest_giver_npc_id: str
    quest_giver_npc_name: str
    quest_giver_npc_role: str
    quest_giver_npc_personality: str
    quest_giver_npc_speaking_style: str
    
    # NPCs in the same location (arrays)
    inLocation_npc_ids: List[str]
    inLocation_npc_names: List[str]
    inLocation_npc_roles: List[str]
    inLocation_npc_personalities: List[str]
    inLocation_npc_speaking_styles: List[str]
    
    # Location info
    location_id: str
    location_name: str
    
    # Dungeons (arrays)
    dungeon_ids: List[str]
    dungeon_names: List[str]
    
    # Monsters (arrays)
    monster_ids: List[str]
    monster_names: List[str]

    # NPC relationships
    """
      "relations": [
    ["npc_bob", "friend"],
    ["npc_charlie", "rival"]
  ]
    이러한 형식으로 전달 
    """
    relations: List[List[str]] = []
    
    # Optional fields
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
      "objective_type": "DUNGEON",  // <--- ★ 다시 DUNGEON으로 변경
      "description_for_player": "Clear the Dungeon.",
      "dialogues": {
        "on_start": [{"speaker_id": "player_character", "line": "Monster is gone, now for the dungeon."}],
        "on_complete": []
      },
      "details": {"target_dungeon_id": "DUNGEON_ID_1"} 
    }
  ],
  "quest_rewards": [],
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
        raw_response = None  # Initialize to avoid UnboundLocalError
        
        try:
            # First attempt
            logger.info(f"Generating quest for NPC {context.quest_giver_npc_id}")
            raw_response = await self._call_gemini(prompt)
            quest_json = self._parse_and_validate(raw_response, context)
            
            logger.info("Quest generated successfully")
            return quest_json
            
        except Exception as e:
            # Retry logic with error feedback
            logger.warning(f"First attempt failed: {e}. Retrying with error feedback...")
            retry_prompt = self._create_retry_prompt(prompt, raw_response if raw_response else "", str(e))
            
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
        
        Modified:
        - Added Debug Logs to check if player_dialogue is received.
        - Enforced 'Theme' as the highest priority rule.
        - NPC Selection Logic (Memory > Relation > Random).
        """
        
        # [DEBUG] 로그 출력: 데이터가 잘 들어왔는지 확인
        logger.info(f"====== [Prompt Gen] Player Dialogue: '{context.player_dialogue}' ======")
        
        # ==================================================================
        # 1. SMART SELECTION LOGIC (Python Side)
        # ==================================================================
        
        # ------------------------------------------------------------------
        # Pick a Target NPC (Priority: Keyword Relevance > Relation > Random)
        # ------------------------------------------------------------------
        selected_npc_str = ""
        target_npc_id = None
        relation_info = "None"
        
        if context.inLocation_npc_ids and len(context.inLocation_npc_ids) > 0:
            candidate_indices = range(len(context.inLocation_npc_ids))
            best_idx = -1
            selection_reason = ""
            
            # --- Logic A: Check Search Results (Keyword Relevance) ---
            if context.search_results_json:
                try:
                    s_data = json.loads(context.search_results_json)
                    for result in s_data.get("results", []):
                        if best_idx != -1: break 
                        
                        # ★ [추가] 유사도 점수 확인 (커트라인 도입)
                        # 점수가 0.35 (35%) 미만이면 "관련 없음"으로 치고 무시
                        # (테스트해보면서 이 수치를 0.3 ~ 0.5 사이로 조절하세요)
                        similarity_score = result.get("similarity_score", 0.0)
                        if similarity_score < 0.35: 
                            continue 

                        memory_content = result.get("memory", {}).get("content", "")
                        
                        for i in candidate_indices:
                            n_id = context.inLocation_npc_ids[i]
                            n_name = context.inLocation_npc_names[i]
                            
                            if n_id in memory_content or n_name in memory_content:
                                best_idx = i
                                selection_reason = f"(Selected because they are related to player's input: '{context.player_dialogue}')"
                                
                                logger.info(f"   [Reasoning] Found Keyword Match! (Score: {similarity_score:.2f})")
                                logger.info(f"   [Reasoning] Memory: '{memory_content}'")
                                logger.info(f"   [Reasoning] Matched NPC: {n_name} ({n_id}) inside this memory.")
                                break
                except: pass

            # --- Logic B: Check Relations (Fallback) ---
            rel_map = {item[0]: item[1] for item in context.relations if len(item) >= 2}
            
            if best_idx == -1:
                related_indices = [i for i in candidate_indices if context.inLocation_npc_ids[i] in rel_map]
                if related_indices:
                    best_idx = random.choice(related_indices)
                    selection_reason = "(Selected based on Relation)"
            
            # --- Logic C: Fallback to Random ---
            if best_idx == -1:
                best_idx = random.randint(0, len(context.inLocation_npc_ids) - 1)
                selection_reason = "(Randomly Selected)"

            # [DEBUG] 선택된 NPC 로그
            logger.info(f"====== [Prompt Gen] Selected NPC: {context.inLocation_npc_names[best_idx]} {selection_reason} ======")

            # Finalize Target NPC
            target_npc_id = context.inLocation_npc_ids[best_idx]
            t_name = context.inLocation_npc_names[best_idx]
            t_role = context.inLocation_npc_roles[best_idx]
            t_pers = context.inLocation_npc_personalities[best_idx]
            
            if target_npc_id in rel_map:
                relation_info = rel_map[target_npc_id]
            else:
                relation_info = "Stranger/Neutral"
                
            selected_npc_str = (
                f"- TARGET NPC: {t_name} (ID: {target_npc_id}) {selection_reason}\n"
                f"  Role: {t_role}, Personality: {t_pers}\n"
                f"  RELATIONSHIP to Quest Giver: {relation_info}"
            )

        # ------------------------------------------------------------------
        # Pick a Dungeon (Random)
        # ------------------------------------------------------------------
        selected_dungeon_str = ""
        target_dungeon_id = None
        
        if context.dungeon_ids and len(context.dungeon_ids) > 0:
            d_idx = random.randint(0, len(context.dungeon_ids) - 1)
            target_dungeon_id = context.dungeon_ids[d_idx]
            selected_dungeon_str = f"- TARGET DUNGEON: {context.dungeon_names[d_idx]} (ID: {target_dungeon_id})"

        # ------------------------------------------------------------------
        # Pick a Monster (Random)
        # ------------------------------------------------------------------
        selected_monster_str = ""
        
        if context.monster_ids and len(context.monster_ids) > 0:
            m_idx = random.randint(0, len(context.monster_ids) - 1)
            selected_monster_str = f"- TARGET MONSTER: {context.monster_names[m_idx]} (ID: {context.monster_ids[m_idx]})"

        # ==================================================================
        # 2. PROMPT CONSTRUCTION
        # ==================================================================

        elements = [
            f"- Quest Giver (NPC): ID: {context.quest_giver_npc_id}, Name: {context.quest_giver_npc_name}",
            f"  Role: {context.quest_giver_npc_role}",
            f"  Personality: {context.quest_giver_npc_personality}",
            f"  Speaking Style: {context.quest_giver_npc_speaking_style}",
            f"  Location: ID: {context.location_id}, Name: {context.location_name}"
        ]
        
        available_ingredients = []
        if selected_npc_str: available_ingredients.append(selected_npc_str)
        if selected_dungeon_str: available_ingredients.append(selected_dungeon_str)
        if selected_monster_str: available_ingredients.append(selected_monster_str)
        
        ingredients_str = "\n".join(available_ingredients)
        
        # Player Dialogue (Theme) - ★★★ 수정됨: 위치 이동 및 강력한 지시
        player_theme_section = ""
        theme_rules = ""
        
        if context.player_dialogue and context.player_dialogue.strip():
            player_theme_section = f"""
    ####################################################################
    *** ABSOLUTE PRIORITY THEME ***
    PLAYER INPUT: "{context.player_dialogue}"
    ####################################################################
    """
            theme_rules = f"""
    0. **THEME ENFORCEMENT (HIGHEST PRIORITY)**: 
       - The generated quest MUST be about "{context.player_dialogue}".
       - The `quest_title` MUST reference this theme.
       - The Quest Giver's first dialogue MUST explicitly mention or react to the player saying "{context.player_dialogue}".
       - **CREATIVE CONNECTION**: If the selected Monster/Dungeon seems unrelated, you MUST invent a magical or metaphorical reason to connect them.
         (e.g., If Input="Sky" and Monster="Slime" -> "A Slime that fell from the Sky" or "Slime eating a cloud".)
    """
        else:
            player_theme_section = "The player approached silently. Create a quest based on the NPC's needs."
            theme_rules = "0. Create a natural quest based on the NPC's role and situation."
        
        # Memory Section
        memory_section = ""
        if context.recent_memories_json or context.search_results_json:
            memory_section = "*** NPC MEMORY CONTEXT ***\n"
            
            if context.search_results_json:
                try:
                    search_data = json.loads(context.search_results_json)
                    if search_data.get("results"):
                        memory_section += "\n    [Related to Player Input]:\n"
                        for res in search_data["results"]:
                            memory_section += f"    - {res.get('memory', {}).get('content')}\n"
                except: pass

            if context.recent_memories_json:
                try:
                    recent_data = json.loads(context.recent_memories_json)
                    if recent_data.get("memories"):
                        memory_section += "\n    [Recent History]:\n"
                        for mem in recent_data["memories"]:
                            memory_section += f"    - [{mem.get('timestamp')}] {mem.get('content')}\n"
                except: pass
        
        elements_str = "\n    ".join(elements)
        
        return f"""
    You are a creative Game Master. Create a narrative-driven quest.
    
    {player_theme_section}
    
    {memory_section}
    
    *** QUEST GIVER INFO ***
    {elements_str}

    *** AVAILABLE INGREDIENTS (Must Use) ***
    {ingredients_str}

    *** CRITICAL RULES ***
    {theme_rules}

    1. **Structure**: Create a logical flow (2-5 steps).
    2. **Usage**: You MUST use the `AVAILABLE INGREDIENTS` listed above.
       - Monster provided? -> Add `KILL` step.
       - Dungeon provided? -> Add `DUNGEON` step.
       - Target NPC provided? -> Add `TALK` step.
    
    3. **Narrative Connection**: 
       - Explain *why* the player needs to do these tasks based on the THEME.
    
    4. **JSON Keys**:
       - DUNGEON type -> `"target_dungeon_id"`
       - GOTO type -> `"target_location_id"`
       - KILL type -> `"target_monster_id"`
       - TALK type -> `"target_npc_id"`

    5. The OUTPUT MUST be a single JSON object with two keys: "quest_data" and "memory_data".
    6. **LANGUAGE**: All content MUST BE IN KOREAN.

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
            replacement = f'\\1{{"speaker_id": "{context.quest_giver_npc_id}", "line": "\\2"}}\\3'
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

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

    # Landmarks (arrays)
    landmark_ids: List[str]
    landmark_names: List[str]
    landmark_descriptions: List[str]

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
        Call Gemini API with JSON Mode enabled.
        
        Args:
            prompt: Formatted prompt string
        
        Returns:
            Raw JSON string from Gemini (Clean, no markdown)
        """
        # JSON 모드 설정
        # response_mime_type을 "application/json"으로 설정하면
        # 모델이 강제로 JSON 포맷만 출력합니다.
        generation_config = {
            "temperature": 0.5,        # 0.0 ~ 1.0 (낮을수록 정해진 답, 높을수록 창의적)
            "max_output_tokens": 4000, # 퀘스트 내용이 잘리지 않도록 넉넉하게
            "response_mime_type": "application/json"  # ★ JSON 모드 활성화 키워드
        }

        try:
            # 설정(config)을 함께 전달하며 비동기 호출
            response = await self.model.generate_content_async(
                [Part.from_text(prompt)],
                generation_config=generation_config
            )
            
            # JSON Mode를 켰기 때문에, 응답(response.text)에는 
            # ```json ... ``` 같은 마크다운 태그가 붙지 않습니다.
            # 따라서 별도의 문자열 파싱/제거 로직 없이 바로 리턴하면 됩니다.
            return response.text.strip()

        except Exception as e:
            # API 호출 자체에서 에러가 발생했을 때 로깅
            logger.error(f"Gemini API Error: {e}")
            raise e
        
    def _create_quest_prompt(self, context: QuestContext) -> str:
        """
        Create prompt for Gemini with game context.

        """
        
        # [DEBUG] 로그 출력
        logger.info(f"====== [Prompt Gen] Player Dialogue: '{context.player_dialogue}' ======")
        
        # ==================================================================
        # 0. GAME STORY & ATMOSPHERE (New!)
        # ==================================================================
        # 여기에 게임의 전체적인 스토리나 분위기를 적으세요.
        story_context = """
    **GAME SETTING**: A dark medieval fantasy world'.
    **CURRENT ATMOSPHERE**: Tension is high. The forest is becoming dangerous.
    **LORE**: Long ago, the ancient kingdom fell due to betrayal. Now, monsters are agitated by the approaching eclipse.
    """

        # ==================================================================
        # 1. SMART SELECTION LOGIC (Target NPC Only)
        # ==================================================================
        # (NPC는 대화의 핵심 대상이므로, 여전히 Python이 '기억' 기반으로 한 명을 콕 집어주는 게 좋습니다.)
        
        selected_npc_str = ""
        target_npc_id = None
        relation_info = "None"
        
        if context.inLocation_npc_ids and len(context.inLocation_npc_ids) > 0:
            candidate_indices = range(len(context.inLocation_npc_ids))
            best_idx = -1
            selection_reason = ""
            
            # --- Logic A: Check Search Results ---
            if context.search_results_json:
                try:
                    s_data = json.loads(context.search_results_json)
                    for result in s_data.get("results", []):
                        if best_idx != -1: break 
                        if result.get("similarity_score", 0.0) < 0.35: continue 

                        memory_content = result.get("memory", {}).get("content", "")
                        for i in candidate_indices:
                            n_id = context.inLocation_npc_ids[i]
                            n_name = context.inLocation_npc_names[i]
                            if n_id in memory_content or n_name in memory_content:
                                best_idx = i
                                selection_reason = f"(Selected: Related to Input)"
                                logger.info(f"   [Reasoning] Match found! NPC: {n_name}")
                                break
                except: pass

            # --- Logic B & C: Relation & Random ---
            rel_map = {item[0]: item[1] for item in context.relations if len(item) >= 2}
            if best_idx == -1:
                related_indices = [i for i in candidate_indices if context.inLocation_npc_ids[i] in rel_map]
                best_idx = random.choice(related_indices) if related_indices else random.randint(0, len(context.inLocation_npc_ids) - 1)
                selection_reason = "(Selected: Relation/Random)"

            # NPC 확정
            target_npc_id = context.inLocation_npc_ids[best_idx]
            selected_npc_str = (
                f"- [TARGET NPC] {context.inLocation_npc_names[best_idx]} (ID: {target_npc_id}) {selection_reason}\n"
                f"  Role: {context.inLocation_npc_roles[best_idx]}, Personality: {context.inLocation_npc_personalities[best_idx]}\n"
                f"  RELATIONSHIP: {relation_info}"
            )

        # ==================================================================
        # 2. RESOURCE LIST GENERATION (Changed!)
        # ==================================================================
        # 파이썬이 고르지 않고, "전체 목록"을 문자열로 만듭니다.
        
        interaction_available_resources_list = []
        
        # 1. Target NPC (Must be included as an option)
        if selected_npc_str:
            interaction_available_resources_list.append(selected_npc_str)
            
        # 2. All Available Dungeons
        if context.dungeon_ids:
            for i in range(len(context.dungeon_ids)):
                interaction_available_resources_list.append(f"- [DUNGEON] {context.dungeon_names[i]} (ID: {context.dungeon_ids[i]})")
                
        # 3. All Available Monsters
        if context.monster_ids:
            for i in range(len(context.monster_ids)):
                interaction_available_resources_list.append(f"- [MONSTER] {context.monster_names[i]} (ID: {context.monster_ids[i]})")
        
        interaction_unavailable_resources_list = []
        # 1. All unavailable Landmarks
        if context.landmark_ids:
            for i in range(len(context.landmark_ids)):
                interaction_unavailable_resources_list.append(f"- [LANDMARK] {context.landmark_names[i]} (ID: {context.landmark_ids[i]}) (Description: {context.landmark_descriptions[i]})")

        resources_str = "\n".join(interaction_available_resources_list)
        interaction_unavailable_resources_str = "\n".join(interaction_unavailable_resources_list)

        # ==================================================================
        # 3. PROMPT CONSTRUCTION
        # ==================================================================

        elements = [
            f"- Quest Giver: {context.quest_giver_npc_name} (ID: {context.quest_giver_npc_id})",
            f"  Role: {context.quest_giver_npc_role}",
            f"  Personality: {context.quest_giver_npc_personality}",
            f"  Speaking Style: {context.quest_giver_npc_speaking_style}",
            f"  Location: {context.location_name}"
        ]
        
        # Theme & Mood Logic
        player_theme_section = ""
        theme_rule = "0. Create a quest that fits the WORLD LORE and NPC's situation."
        
        if context.player_dialogue and context.player_dialogue.strip():
            player_theme_section = f"*** PLAYER INPUT: \"{context.player_dialogue}\" ***"
            theme_rule = f"""0. **THEME ENFORCEMENT (HIGHEST PRIORITY)**: 
       - The quest MUST revolve around "{context.player_dialogue}".
       - **SELECTION RULE**: Look at the 'AVAILABLE RESOURCES' list. Pick only the Monsters/Dungeons that logically fit this theme.
       - If the theme is "Hunger", pick a Beast-type monster (for meat).
       - If the theme is "Treasure", pick a Dungeon.
       - If nothing fits perfectly, pick the closest one and invent a creative reason."""

        # Memory Logic
        memory_section = ""
        if context.search_results_json or context.recent_memories_json:
            memory_section = "*** MEMORY CONTEXT ***\n"
            # (Memory parsing omitted for brevity - same as before)
            if context.search_results_json:
                try:
                    s_data = json.loads(context.search_results_json)
                    for res in s_data.get("results", []):
                        memory_section += f"    - [Related]: {res.get('memory', {}).get('content')}\n"
                except: pass
            if context.recent_memories_json:
                try:
                    recent_data = json.loads(context.recent_memories_json)
                    for mem in recent_data.get("memories", []):
                        memory_section += f"    - [Recent]: {mem.get('content')}\n"
                except: pass

        quest_giver_str = "\n    ".join(elements)

        return f"""
    You are a Master Quest Designer for a **Medieval Fantasy RPG**.
    
    *** WORLD STORY & LORE ***
    {story_context}
    
    {player_theme_section}
    {memory_section}
    
    *** QUEST GIVER ***
    {quest_giver_str}

    *** AVAILABLE RESOURCES (MENU) ***
    {resources_str}

    *** INTERACTION UNAVAILABLE RESOURCES (CANNOT INTERACT) ***
    {interaction_unavailable_resources_str}

    *** CRITICAL RULES ***
    {theme_rule}

    1. **Intelligent Selection**: 
       - From the `AVAILABLE RESOURCES` list above, **YOU (the AI) MUST SELECT 0 to 3 items** that best fit the Theme and Story.
       - Do NOT use everything. Only use what makes sense.
       - If the Player Input implies fighting, pick a Monster.
       - If the Player Input implies exploration, pick a Dungeon.
       - Always include the 'Target NPC' if one is listed.

    1-2. **Exclusion of Unavailable Resources**:
        - You can use the 'INTERACTION UNAVAILABLE RESOURCES' list for story flavor, but you CANNOT make them direct objectives. 
        - It means you cannot have objectives like "Go to LANDMARK" or "Talk to LANDMARK".
        - But you can mention them in dialogues or quest summaries.
        - For example, some NPC has a shack. Shack is a landmark. You can make a dialogue like "I live near the old shack, and I need to fix it. Can you help me?" And you can make an objective like "Talk to NPC to get wood planks to fix the shack.", but you cannot make an objective like "Go to the shack and fix it."

    2. **The "Bridge" Rule (Causality)**: 
       - Every dialogue MUST explain *why* the player needs to do the NEXT objective.
       - Connect the selected resources to the Quest Giver's problem and the World Lore.

    3. **Mandatory Structure**:
       - **Step 1**: Interaction with Quest Giver.
       - **Middle Steps**: Steps for the resources YOU SELECTED (Kill X, Go to Y, Talk to Z).
       - **Final Step**: MUST return to Quest Giver (`{context.quest_giver_npc_id}`).

    4. **JSON Keys**:
       - KILL -> `target_monster_id`
       - DUNGEON -> `target_dungeon_id`
       - TALK -> `target_npc_id`
       - GOTO -> `target_location_id`

    5. **Output**: A single JSON object with `quest_data` and `memory_data`.
    6. **Language**: KOREAN ONLY. Use a tone appropriate for the Medieval Fantasy setting.

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
            pattern = r'("on_start"\s*:\s*\[\s*)"([\s\S]*?)"(\s*\])'
            replacement = r'\1{"speaker_id": "' + context.quest_giver_npc_id + r'", "line": "\2"}\3'
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

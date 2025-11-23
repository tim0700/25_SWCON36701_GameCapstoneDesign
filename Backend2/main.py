import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import re
import time
import requests 

# --- 1. Vertex AI ?¤ì  ---
PROJECT_ID = "questtest-477417"  # ? ë³¸ì¸??Google Cloud Project ID
LOCATION = "us-central1"            # ? Vertex AIë¥??¬ì©?ë ë¦¬ì 
MODEL_NAME = "gemini-2.5-pro"   # ? ?¬ì©??Gemini ëª¨ë¸
# ---------------------------------------------

# --- 2. CharacterMemorySystem ?°ë ?¤ì  ---
MEMORY_SYSTEM_URL = "http://localhost:8123"  # CharacterMemorySystem API URL
MEMORY_SYSTEM_TIMEOUT = 5  # API ?¸ì¶ ??ì??(ì´?
# ---------------------------------------------

# Vertex AI ì´ê¸°??
vertexai.init(project=PROJECT_ID, location=LOCATION)

# FastAPI ???ì±
app = FastAPI()

# --- 2. Unityê° ë³´ë¼ ?°ì´?°ì ëª¨ë¸ ?ì ---
# (NpcInfo -> QuestContextë¡??´ë¦ ë³ê²?ë°??ë ?ì¥)
class QuestContext(BaseModel):
    npc1_id: str; npc1_name: str; npc1_desc: str
    npc2_id: str; npc2_name: str; npc2_desc: str
    location_id: str; location_name: str
    dungeon_id: str 
    monster_id: str
    player_dialogue: str = " \ # NEW: Player dialogue input (optional)

# --- 3. ?ì¤???ì±???í ?ë¡¬?í¸ ?íë¦?---
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

# --- 4. ê¸°ìµ ???ëª¨ë (CharacterMemorySystem ?°ë) ---
def save_memory_log(memory_json: dict):
    """
    ?ì±??ê¸°ìµ ?°ì´?°ë? CharacterMemorySystem????¥í©?ë¤.
    
    Args:
        memory_json: {"npc_id": str, "content": str}
        
    Returns:
        bool: ????±ê³µ ?¬ë?
    """
    npc_id = memory_json.get("npc_id")
    content = memory_json.get("content")
    
    # ?°ì´??ê²ì¦?
    if not npc_id or not content:
        print(f"??[Memory Log] Invalid data: npc_id={npc_id}, content={content}")
        return False
    
    # CharacterMemorySystem API ?ì²­ ?°ì´??
    payload = {
        "content": content,
        "metadata": {
            "source": "quest_generation",
            "timestamp": time.time(),
            "quest_giver": npc_id
        }
    }
    
    try:
        print(f"\n[Memory Log] Saving to CharacterMemorySystem...")
        print(f" - Target URL: {MEMORY_SYSTEM_URL}/memory/{npc_id}")
        print(f" - NPC ID: {npc_id}")
        print(f" - Content: {content[:50]}..." if len(content) > 50 else f" - Content: {content}")
        
        # CharacterMemorySystem POST ?ì²­
        response = requests.post(
            f"{MEMORY_SYSTEM_URL}/memory/{npc_id}",
            json=payload,
            timeout=MEMORY_SYSTEM_TIMEOUT
        )
        
        # ?±ê³µ ?ëµ (201 Created)
        if response.status_code == 201:
            result = response.json()
            memory_id = result.get("memory_id", "unknown")
            print(f"??[Memory Log] Successfully saved (ID: {memory_id})")
            print(f" - Stored in: {result.get('stored_in', 'recent')}")
            print(f" - Evicted to buffer: {result.get('evicted_to_buffer', False)}")
            return True
        else:
            print(f"? ï¸ [Memory Log] Unexpected status code: {response.status_code}")
            print(f" - Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"??[Memory Log] Timeout: CharacterMemorySystem not responding")
        print(f"   Make sure CharacterMemorySystem is running on {MEMORY_SYSTEM_URL}")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"??[Memory Log] Connection Error: Cannot reach CharacterMemorySystem")
        print(f"   Is the server running? Check {MEMORY_SYSTEM_URL}")
        return False
        
    except Exception as e:
        print(f"??[Memory Log] Unexpected error: {type(e).__name__}: {e}")
        return False

# --- 5. LLM ?¤ë¥ ë³´ì  ?¨ì??---

async def call_gemini_async(prompt_text: str) -> str:
    model = GenerativeModel(MODEL_NAME)
    response = await model.generate_content_async([Part.from_text(prompt_text)])
    quest_json_string = response.text
    if "```json" in quest_json_string:
        quest_json_string = quest_json_string.split("```json")[1].split("```")[0]
    elif "```" in quest_json_string:
         quest_json_string = quest_json_string.split("```")[1].split("```")[0]
    return quest_json_string.strip()

def fix_common_json_errors(json_str: str, context: QuestContext) -> str:
    """JSON ë¬¸ì???´ì ?í ?¤ë¥(????¬ë§· ??ë¥??ê·?ì¼ë¡?ë³´ì ?©ë??"""
    corrected_str = json_str
    try:
        # "on_start": [ "??? ] ?¨í´ ë³´ì 
        pattern = r'("on_start"\s*:\s*\[\s*)"([\s\S]*?)"(\s*\])'
        replacement = f'\\1{{"speaker_id": "{context.npc1_id}", "line": "\\2"}}\\3'
        corrected_str = re.sub(pattern, replacement, corrected_str, flags=re.IGNORECASE)
    except Exception as e:
        print(f"JSON ë³´ì  ì¤??¤ë¥: {e}")
        return json_str
    return corrected_str

def create_retry_prompt(original_prompt: str, bad_json: str, error_message: str) -> str:
    return f"""
    Your previous JSON generation failed. Error: {error_message}
    Failed JSON: {bad_json}
    Please correct the JSON structure. 
    Ensure you generate a ROOT object containing both "quest_data" and "memory_data".
    Original Instructions: {original_prompt}
    """


# --- 6. create_quest_prompt ?¨ì (?ì  ê·ì¹ ?ì±) ---
def create_quest_prompt(context: QuestContext) -> str:
    
    elements = [
        f"- Quest Giver (NPC 1): ID: {context.npc1_id}, Name: {context.npc1_name}",
        f"- Target NPC (NPC 2): ID: {context.npc2_id}, Name: {context.npc2_name}",
        f"- Target Location: ID: {context.location_id}, Name: {context.location_name}"
    ]
    
    # NEW: Add player request section if dialogue is provided
    player_request_section = ""
    if context.player_dialogue and context.player_dialogue.strip():
        player_request_section = f"""
    *** PLAYER REQUEST ***
    The player specifically said to {context.npc1_name}: "{context.player_dialogue}"
    
    CRITICAL: The generated quest MUST incorporate this player request as the primary objective.
    Make the quest about fulfilling what the player asked for, while using the available game elements below.
    """
    
    rules = [
        f"1. The `quest_giver_npc_id` inside `quest_data` MUST be \"{context.npc1_id}\".",
        f"2. `quest_data` MUST follow the Unity quest structure rules (GOTO/TALK types).",
        f"3. `memory_data.npc_id` MUST be \"{context.npc1_id}\"."
    ]

    if context.monster_id:
        rules.append(f"4. `quest_data` MAY use KILL type with target_monster_id: \"{context.monster_id}\".")
        elements.append(f"- Target Monster: ID: {context.monster_id}")
    else:
        rules.append("4. DO NOT use KILL type.")

    if context.dungeon_id:
        rules.append(f"5. `quest_data` MAY use DUNGEON type with target_dungeon_id: \"{context.dungeon_id}\".")
        elements.append(f"- Target Dungeon: ID: {context.dungeon_id}")
    else:
        rules.append("5. DO NOT use DUNGEON type.")

    elements_str = "\n    ".join(elements)
    rules_str = "\n    ".join(rules)

    return f"""
    You are a quest designer. Generate a JSON response containing TWO parts: "quest_data" and "memory_data".
    {player_request_section}
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
# --- 7. FastAPI ?ë?¬ì¸???ì± ---
# (NpcInfo -> QuestContextë¡????ë³ê²?
@app.post("/generate-quest")
async def generate_quest(context: QuestContext):
    
    original_prompt = create_quest_prompt(context)
    
    try:
        # 1ì°??ë
        print("--- 1ì°??ì± ?ë ---")
        raw_response = await call_gemini_async(original_prompt)
        
        # ë³´ì  (Regex)
        fixed_response = fix_common_json_errors(raw_response, context)

        try:
            # 1. ?ì²´ JSON ?ì±
            root_json = json.loads(fixed_json_string_v1 := fixed_response)
            
            # 2. ?°ì´??ë¶ë¦¬
            quest_data = root_json.get("quest_data")
            memory_data = root_json.get("memory_data")

            if not quest_data or not memory_data:
                raise ValueError("JSON must contain both 'quest_data' and 'memory_data' keys.")

            # 3. ê¸°ìµ ?°ì´??ì²ë¦¬ (??ì¤?¬í ì¶ê? ë°????
            save_memory_log(memory_data)

            # 4. Unity?ë 'quest_data'ë§?ë¬¸ì?´ë¡ ?¤ì ë³?í´???ì¡
            # (Unity???´ì ê³??ê°? ?¬ë§·??ë¬¸ì?´ì ë°ê² ??
            quest_json_string = json.dumps(quest_data)
            
            print("--- ?±ê³µ: ?ì¤?¸ë Unityë¡? ê¸°ìµ? ??¥ìë¡?ë¶ê¸°??---")
            return {"quest_json": quest_json_string}

        except Exception as e_parse1:
            # --- ?¤í¨ ???¬ì??ë¡ì§ (Hybrid Retry) ---
            print(f"--- 1ì°??¤í¨: {e_parse1}. 2ì°??¬ì??---")
            retry_prompt = create_retry_prompt(original_prompt, raw_response, str(e_parse1))
            
            raw_response_v2 = await call_gemini_async(retry_prompt)
            fixed_response_v2 = fix_common_json_errors(raw_response_v2, context)
            
            try:
                root_json_v2 = json.loads(fixed_response_v2)
                
                quest_data_v2 = root_json_v2.get("quest_data")
                memory_data_v2 = root_json_v2.get("memory_data")
                
                if not quest_data_v2 or not memory_data_v2:
                    raise ValueError("Missing keys in v2.")

                save_memory_log(memory_data_v2)
                
                quest_json_string_v2 = json.dumps(quest_data_v2)
                return {"quest_json": quest_json_string_v2}
            
            except Exception as e_parse2:
                return {"error": f"Final failure: {e_parse2}"}

    except Exception as e_initial:
        return {"error": str(e_initial)}



# --- 8. ?ë² ?¤í (?ì¤?¸ì©) ---
if __name__ == "__main__":
    # 0.0.0.0?¼ë¡ ?¤í?´ì¼ Unity?ì localhost ?ë 127.0.0.1ë¡??ê·¼ ê°??
    # ?¬í¸ 8001 ?¬ì© (CharacterMemorySystem??8000 ?¬ì©)
    uvicorn.run(app, host="0.0.0.0", port=8001)

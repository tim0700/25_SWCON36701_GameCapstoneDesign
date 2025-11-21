import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import re
import time 

# --- 1. Vertex AI 설정 ---
PROJECT_ID = "questtest-477417"  # 👈 본인의 Google Cloud Project ID
LOCATION = "us-central1"            # 👈 Vertex AI를 사용하는 리전
MODEL_NAME = "gemini-2.5-pro"   # 👈 사용할 Gemini 모델
# ---------------------------------------------

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=LOCATION)

# FastAPI 앱 생성
app = FastAPI()

# --- 2. Unity가 보낼 데이터의 모델 정의 ---
# (NpcInfo -> QuestContext로 이름 변경 및 필드 확장)
class QuestContext(BaseModel):
    npc1_id: str; npc1_name: str; npc1_desc: str
    npc2_id: str; npc2_name: str; npc2_desc: str
    location_id: str; location_name: str
    dungeon_id: str 
    monster_id: str

# --- 3. 퀘스트 생성을 위한 프롬프트 템플릿 ---
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

# --- 4. 기억 저장 모듈 (아직 만들지 않은 파일 시뮬레이션) ---
def save_memory_log(memory_json: dict):
    """
    생성된 기억 데이터를 처리하는 함수입니다.
    추후 DB 저장이나 다른 백엔드로 전송하는 로직이 이곳에 들어갑니다.
    """
    # 타임스탬프 추가 (float)
    memory_json["timestamp"] = time.time()
    
    print(f"\n[Memory Log] Saving to backend...")
    print(f" - NPC ID: {memory_json.get('npc_id')}")
    print(f" - Content (Vector Optimized): {memory_json.get('content')}")
    print(f" - Timestamp: {memory_json['timestamp']}")
    

    # 예: save_to_vector_db(memory_json)
    
    return True

# --- 5. LLM 오류 보정 함수들 ---

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
    """JSON 문자열 내의 흔한 오류(대사 포맷 등)를 정규식으로 보정합니다."""
    corrected_str = json_str
    try:
        # "on_start": [ "대사" ] 패턴 보정
        pattern = r'("on_start"\s*:\s*\[\s*)"([\s\S]*?)"(\s*\])'
        replacement = f'\\1{{"speaker_id": "{context.npc1_id}", "line": "\\2"}}\\3'
        corrected_str = re.sub(pattern, replacement, corrected_str, flags=re.IGNORECASE)
    except Exception as e:
        print(f"JSON 보정 중 오류: {e}")
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


# --- 6. create_quest_prompt 함수 (동적 규칙 생성) ---
def create_quest_prompt(context: QuestContext) -> str:
    
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
# --- 7. FastAPI 엔드포인트 생성 ---
# (NpcInfo -> QuestContext로 타입 변경)
@app.post("/generate-quest")
async def generate_quest(context: QuestContext):
    
    original_prompt = create_quest_prompt(context)
    
    try:
        # 1차 시도
        print("--- 1차 생성 시도 ---")
        raw_response = await call_gemini_async(original_prompt)
        
        # 보정 (Regex)
        fixed_response = fix_common_json_errors(raw_response, context)

        try:
            # 1. 전체 JSON 파싱
            root_json = json.loads(fixed_json_string_v1 := fixed_response)
            
            # 2. 데이터 분리
            quest_data = root_json.get("quest_data")
            memory_data = root_json.get("memory_data")

            if not quest_data or not memory_data:
                raise ValueError("JSON must contain both 'quest_data' and 'memory_data' keys.")

            # 3. 기억 데이터 처리 (타임스탬프 추가 및 저장)
            save_memory_log(memory_data)

            # 4. Unity에는 'quest_data'만 문자열로 다시 변환해서 전송
            # (Unity는 이전과 똑같은 포맷의 문자열을 받게 됨)
            quest_json_string = json.dumps(quest_data)
            
            print("--- 성공: 퀘스트는 Unity로, 기억은 저장소로 분기됨 ---")
            return {"quest_json": quest_json_string}

        except Exception as e_parse1:
            # --- 실패 시 재시도 로직 (Hybrid Retry) ---
            print(f"--- 1차 실패: {e_parse1}. 2차 재시도 ---")
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



# --- 8. 서버 실행 (테스트용) ---
if __name__ == "__main__":
    # 0.0.0.0으로 실행해야 Unity에서 localhost 또는 127.0.0.1로 접근 가능
    uvicorn.run(app, host="0.0.0.0", port=8000)
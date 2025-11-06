import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Part

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
    # NPC 1 (퀘스트 제공자)
    npc1_id: str
    npc1_name: str
    npc1_desc: str
    # NPC 2 (대상)
    npc2_id: str
    npc2_name: str
    npc2_desc: str
    # Location (대상)
    location_id: str
    location_name: str

# --- 3. 퀘스트 생성을 위한 프롬프트 템플릿 ---
QUEST_JSON_FORMAT_EXAMPLE = """
{
  "quest_title": "Example Quest: Monster Hunt",
  "quest_giver_npc_id": "npc_quest_giver",
  "quest_type": "SIDE_QUEST",
  "quest_summary": "A quest to clear out monsters and investigate a dungeon.",
  "quest_steps": [
    {
      "step_id": 1,
      "objective_type": "TALK",
      "description_for_player": "Talk to the target NPC.",
      "dialogues": {
        "on_start": [
          {"speaker_id": "npc_quest_giver", "line": "Please go talk to NPC B."}
        ],
        "on_complete": []
      },
      "details": {
        "target_npc_id": "npc_b_character"
      }
    },
    {
      "step_id": 2,
      "objective_type": "KILL",
      "description_for_player": "Defeat 5 slimes near the lake.",
      "dialogues": {
        "on_start": [
          {"speaker_id": "npc_b_character", "line": "We are being overrun by slimes! Please defeat them."}
        ],
        "on_complete": []
      },
      "details": {
        "target_monster_id": "monster_slime_blue"
      }
    },
    {
      "step_id": 3,
      "objective_type": "DUNGEON",
      "description_for_player": "Investigate the 'Old Ruin' dungeon.",
      "dialogues": {
        "on_start": [
          {"speaker_id": "player_character", "line": "That's all of them. Now to check those ruins."}
        ],
        "on_complete": []
      },
      "details": {
        "target_dungeon_id": "loc_old_ruin_dungeon"
      }
    },
    {
      "step_id": 4,
      "objective_type": "GOTO",
      "description_for_player": "Go to the safe zone.",
      "dialogues": {
        "on_start": [],
        "on_complete": [
          {"speaker_id": "player_character", "line": "This area seems safe."}
        ]
      },
      "details": {
        "target_location_id": "loc_safe_zone"
      }
    }
  ],
  "quest_rewards": []
}
"""

def create_quest_prompt(context: QuestContext) -> str:
    """Unity에서 받은 퀘스트 재료로 Gemini 프롬프트를 생성합니다."""
    
    return f"""
    You are a quest designer. Generate a quest JSON based on the provided characters and location.

    Here are the elements you MUST use:
    - Quest Giver (NPC 1): 
      - ID: {context.npc1_id}
      - Name: {context.npc1_name}
    - Target NPC (NPC 2):
      - ID: {context.npc2_id}
      - Name: {context.npc2_name}
    - Target Location:
      - ID: {context.location_id}
      - Name: {context.location_name}

    *** CRITICAL, ABSOLUTE RULES: YOU MUST FOLLOW THIS EXACT STRUCTURE ***
    1.  The root object MUST have a key named "quest_steps".
    2.  The `quest_giver_npc_id` MUST be "{context.npc1_id}".
    3.  All step details MUST be inside a "details" object (e.g., {{"target_location_id": "...", "target_npc_id": "..."}}).
        - "GOTO" steps MUST use "target_location_id".
        - "TALK" steps MUST use "target_npc_id".
        - You can also use "KILL" (with "target_monster_id") and "DUNGEON" (with "target_dungeon_id").
    4.  DO NOT add extra root fields like "start_dialogue".

    5.  (!!!) THIS IS THE MOST IMPORTANT RULE: DIALOGUE STRUCTURE
        - The "on_start" and "on_complete" arrays MUST contain *OBJECTS*, not simple strings.
        - Each object MUST look like this: {{"speaker_id": "some_id", "line": "Some text..."}}
        - **WRONG:** "on_start": [ "Hello world" ]
        - **CORRECT:** "on_start": [ {{"speaker_id": "{context.npc1_id}", "line": "Hello world"}} ]
        - You MUST follow the CORRECT format.

    6.  "GOTO" steps MUST have `on_complete` dialogues (as objects).
    7.  "TALK", "KILL", and "DUNGEON" steps MUST have empty `[]` `on_complete` dialogues.
    8.  The response MUST be ONLY the raw JSON object. Do NOT include ```json ... ```.

    JSON Format Example (FOLLOW THIS STRUCTURE PRECISELY):
    {QUEST_JSON_FORMAT_EXAMPLE} 
    
    Generate a quest linking {context.npc1_name}, {context.npc2_name}, and {context.location_name} using these strict rules.
    """
# --- 4. FastAPI 엔드포인트 생성 ---
# (NpcInfo -> QuestContext로 타입 변경)
@app.post("/generate-quest")
async def generate_quest(context: QuestContext): # <-- 타입 변경
    """Unity로부터 퀘스트 재료를 받아 Vertex AI로 퀘스트 생성을 요청합니다."""
    
    try:
        # 1. 퀘스트 생성 프롬프트 만들기
        prompt_text = create_quest_prompt(context) # <-- context 전달
        
        # 2. Vertex AI 모델 로드 및 호출
        model = GenerativeModel(MODEL_NAME)
        response = await model.generate_content_async(
            [Part.from_text(prompt_text)]
        )
        
        # 3. 응답에서 텍스트(퀘스트 JSON) 추출
        quest_json_string = response.text
        
        if "```" in quest_json_string:
            quest_json_string = quest_json_string.split("```json")[1].split("```")[0]
        quest_json_string = quest_json_string.strip()

        print("--- Quest Generated (using context) ---")
        print(quest_json_string)
        print("---------------------------------------")

        return {"quest_json": quest_json_string}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

# --- 5. 서버 실행 (테스트용) ---
if __name__ == "__main__":
    # 0.0.0.0으로 실행해야 Unity에서 localhost 또는 127.0.0.1로 접근 가능
    uvicorn.run(app, host="0.0.0.0", port=8000)
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
}
"""

# --- 3. (수정) create_quest_prompt 함수 (동적 규칙 생성) ---
def create_quest_prompt(context: QuestContext) -> str:
    """Unity에서 받은 퀘스트 재료로 Gemini 프롬프트를 생성합니다."""

    # (신규) 재료가 있는지(빈 문자열이 아닌지) 확인하여 프롬프트 구성
    
    elements = [
        f"- Quest Giver (NPC 1): ID: {context.npc1_id}, Name: {context.npc1_name}",
        f"- Target NPC (NPC 2): ID: {context.npc2_id}, Name: {context.npc2_name}",
        f"- Target Location: ID: {context.location_id}, Name: {context.location_name}"
    ]
    
    rules = [
        f"1.  The `quest_giver_npc_id` MUST be \"{context.npc1_id}\".",
        f"2.  At least one \"GOTO\" step MUST use \"details\": {{\"target_location_id\": \"{context.location_id}\"}}.",
        f"3.  At least one \"TALK\" step MUST use \"details\": {{\"target_npc_id\": \"{context.npc2_id}\"}}."
    ]

    # --- (신규) 동적 규칙 생성 ---
    # 몬스터 ID가 DB에 존재하면(빈 문자열이 아니면) KILL 규칙 추가
    if context.monster_id:
        rules.append(f"4.  You MAY use a \"KILL\" objective. If you do, you MUST use \"details\": {{\"target_monster_id\": \"{context.monster_id}\"}}.")
        elements.append(f"- Target Monster (OBJECT): ID: {context.monster_id}")
    else:
        rules.append("4.  DO NOT use the \"KILL\" objective type, as no monster_id was provided.")

    # 던전 ID가 DB에 존재하면(빈 문자열이 아니면) DUNGEON 규칙 추가
    if context.dungeon_id:
        rules.append(f"5.  You MAY use a \"DUNGEON\" objective. If you do, you MUST use \"details\": {{\"target_dungeon_id\": \"{context.dungeon_id}\"}}.")
        elements.append(f"- Target Dungeon: ID: {context.dungeon_id}")
    else:
        rules.append("5.  DO NOT use the \"DUNGEON\" objective type, as no dungeon_id was provided.")
        
    # --- (이하 규칙은 동일) ---
    rules.append("6.  (!!!) DO NOT invent new IDs. Use ONLY the IDs provided in the 'Elements' list.")
    rules.append("7.  All dialogue MUST be objects ( {{\"speaker_id\": \"...\", \"line\": \"...\"}} ), NOT simple strings.")
    rules.append("8.  \"GOTO\" steps MUST have `on_complete` dialogues.")
    rules.append("9.  \"TALK\", \"KILL\", and \"DUNGEON\" steps MUST have empty `[]` `on_complete` dialogues.")
    rules.append("10. The response MUST be ONLY the raw JSON object. Do NOT include ```json ... ```.")

    elements_str = "\n    ".join(elements)
    rules_str = "\n    ".join(rules)

    return f"""
    You are a quest designer. Generate a quest JSON based ONLY on the provided elements.

    *** YOU MUST USE THESE EXACT ELEMENTS ***
    {elements_str}

    *** CRITICAL, ABSOLUTE RULES ***
    {rules_str}

    JSON Format Example (FOLLOW THIS STRUCTURE PRECISELY):
    {QUEST_JSON_FORMAT_EXAMPLE} 
    
    Generate a creative quest linking the provided elements using ONLY these rules.
    """
# --- 4. FastAPI 엔드포인트 생성 ---
# (NpcInfo -> QuestContext로 타입 변경)
@app.post("/generate-quest")
async def generate_quest(context: QuestContext):
    """Unity로부터 퀘스트 "재료"를 받아 Gemini로 중계합니다."""
    
    try:
        prompt_text = create_quest_prompt(context)
        
        model = GenerativeModel(MODEL_NAME)
        response = await model.generate_content_async([Part.from_text(prompt_text)])
        quest_json_string = response.text
        
        # ... (JSON 정리 로직) ...
        if "```" in quest_json_string:
            quest_json_string = quest_json_string.split("```json")[1].split("```")[0]
        quest_json_string = quest_json_string.strip()

        print(f"--- Quest Generated for {context.npc1_name} ---")
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
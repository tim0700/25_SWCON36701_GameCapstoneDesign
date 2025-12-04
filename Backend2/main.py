import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import re

# --- 1. Vertex AI 설정 ---
PROJECT_ID = "questgenerator-476501"  # 👈 본인의 Google Cloud Project ID
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

# LLM 오류 보정 함수들

# Gemini 호출 헬퍼 함수
async def call_gemini_async(prompt_text: str) -> str:
    model = GenerativeModel(MODEL_NAME)
    response = await model.generate_content_async([Part.from_text(prompt_text)])
    
    quest_json_string = response.text
    
    # 마크다운(` ```json ... ``` `) 제거
    if "```json" in quest_json_string:
        quest_json_string = quest_json_string.split("```json")[1].split("```")[0]
    elif "```" in quest_json_string:
         quest_json_string = quest_json_string.split("```")[1].split("```")[0]
         
    return quest_json_string.strip()

# Python 오류 보정 함수 
def fix_common_json_errors(json_str: str, context: QuestContext) -> str:
    
    corrected_str = json_str
    
    try:
        # 오류 1: "on_start": [ "대사" ] -> [ {"speaker_id": ..., "line": ...} ]
        # ([\s\S]*?는 줄바꿈을 포함한 모든 문자를 찾습니다)
        pattern = r'("on_start"\s*:\s*\[\s*)"([\s\S]*?)"(\s*\])'
        
        # 보정: speaker_id를 퀘스트 제공자(npc1)로 우선 지정
        replacement = f'\\1{{"speaker_id": "{context.npc1_id}", "line": "\\2"}}\\3'
        corrected_str = re.sub(pattern, replacement, corrected_str, flags=re.IGNORECASE)
        
        # 추후 오류에 따라 보강

    except Exception as e:
        print(f"JSON 보정 중 오류 발생: {e}")
        return json_str # 보정 실패 시 원본 반환
        
    return corrected_str

# 재시도 프롬프트 생성 함수
def create_retry_prompt(original_prompt: str, bad_json: str, error_message: str) -> str:
    return f"""
    Your previous attempt to generate a JSON failed with a parsing error.
    
    ERROR MESSAGE:
    {error_message}
    
    FAILED JSON (This is what you generated):
    {bad_json}
    
    Please correct your mistake and regenerate the JSON exactly according to the original instructions.
    Do NOT include any text other than the raw JSON object.
    
    ORIGINAL INSTRUCTIONS:
    {original_prompt}
    """


# --- 3. create_quest_prompt 함수 (동적 규칙 생성) ---
def create_quest_prompt(context: QuestContext) -> str:
    """Unity에서 받은 퀘스트 재료로 Gemini 프롬프트를 생성합니다."""

    # 재료가 있는지(빈 문자열이 아닌지) 확인하여 프롬프트 구성
    
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

    # --- 동적 규칙 생성 ---
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
    
    # 1. 원본 프롬프트 생성
    original_prompt = create_quest_prompt(context)
    
    try:
        # --- 1차 시도 ---
        print("--- 1차 퀘스트 생성 시도 ---")
        json_string_v1 = await call_gemini_async(original_prompt)

        # --- 방법 2: 1차 보정 시도 (Python Regex) ---
        print("--- 1차 보정 시도 (Python Regex) ---")
        fixed_json_string_v1 = fix_common_json_errors(json_string_v1, context)

        try:
            # --- 1차 파싱 시도 (Python 검증) ---
            json.loads(fixed_json_string_v1) # 파싱 테스트
            
            print("--- 1차 시도: 보정 후 파싱 성공! ---")
            print(fixed_json_string_v1)
            print("---------------------------------------")
            return {"quest_json": fixed_json_string_v1} # (성공) Unity로 전송

        except Exception as e_parse1:
            # --- 1차 파싱 실패 -> 2차 시도 (스마트 재시도) 실행 ---
            print(f"--- 1차 파싱 실패 (오류: {e_parse1}). 2차 재시도(Smart Retry) 시작 ---")
            
            # --- 방법 1: 오류 피드백 프롬프트 생성 ---
            retry_prompt = create_retry_prompt(original_prompt, json_string_v1, str(e_parse1))
            
            # --- 2차 생성 시도 ---
            json_string_v2 = await call_gemini_async(retry_prompt)
            
            # --- 방법 2: 2차 보정 시도 ---
            print("--- 2차 보정 시도 (Python Regex) ---")
            fixed_json_string_v2 = fix_common_json_errors(json_string_v2, context)
            
            try:
                # --- 2차 파싱 시도 (Python 검증) ---
                json.loads(fixed_json_string_v2) # 파싱 테스트
                
                print("--- 2차 시도: 보정 후 파싱 성공! ---")
                print(fixed_json_string_v2)
                print("---------------------------------")
                return {"quest_json": fixed_json_string_v2} # (성공) Unity로 전송
            
            except Exception as e_parse2:
                # --- 최종 실패 ---
                print(f"--- 2차 재시도도 최종 실패 (오류: {e_parse2}) ---")
                print(f"--- 실패한 JSON: {fixed_json_string_v2} ---")
                return {"error": f"Failed to generate valid JSON after 2 attempts: {e_parse2}"}

    except Exception as e_initial:
        # (Google 403 권한 오류 등) 1차 호출 자체가 실패한 경우
        print(f"--- 1차 생성부터 실패 (Gemini API 오류): {e_initial} ---")
        return {"error": str(e_initial)}



# --- 5. 서버 실행 (테스트용) ---
if __name__ == "__main__":
    # 0.0.0.0으로 실행해야 Unity에서 localhost 또는 127.0.0.1로 접근 가능
    uvicorn.run(app, host="0.0.0.0", port=8000)
import requests
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import re
import os

# ==========================================
# 1. 테스트 설정 (Configuration)
# ==========================================
# ★ 서버 주소 확인 (포트 번호가 8000인지 8123인지 확인하세요!)
SERVER_URL = "http://127.0.0.1:8123/quest/generate"

# ★ 테스트 반복 횟수 (모델당 n회)
TEST_COUNT_PER_SCENARIO = 3  # (너무 많으면 HTML 파일이 커지니 3~5회 추천)

# ★ 비교할 시나리오 설정
TEST_SCENARIOS = [
    # 1. Gemini 2.5 token 4080
    {"name": "Gemini 2.5 Flash Lite 4080",   "model": "gemini-2.5-flash-lite",   "tokens": 4080},
    {"name": "Gemini 2.5 Flash 4080", "model": "gemini-2.5-flash", "tokens": 4080},
    {"name": "Gemini 2.5 Pro 4080", "model": "gemini-2.5-pro", "tokens": 4080},

    # 2. Gemini 2.5 token 8192
    {"name": "Gemini 2.5 Flash Lite 8192",   "model": "gemini-2.5-flash-lite",   "tokens": 8192},
    {"name": "Gemini 2.5 Flash 8192", "model": "gemini-2.5-flash", "tokens": 8192},
    {"name": "Gemini 2.5 Pro 8192", "model": "gemini-2.5-pro", "tokens": 8192},

    # 3. Gemini 3.0 (실험적 모델)
    {"name": "Gemini 3 Pro 4080", "model": "gemini-3-pro-preview", "tokens": 4080}, 
    {"name": "Gemini 3 Pro 8192", "model": "gemini-3-pro-preview", "tokens": 8192},
]

OUTPUT_FILE = "model_comparison_results.csv"
HTML_OUTPUT_FILE = "quest_report.html"

# 테스트용 키워드
KEYWORDS = ["배고파", "전쟁", "사랑", "마법", "배신", "보물", "평화"]

# 기본 페이로드
BASE_PAYLOAD = {
    "quest_giver_npc_id": "NPC001_Amber",
    "quest_giver_npc_name": "Amber",
    "quest_giver_npc_role": "Hunter",
    "quest_giver_npc_personality": "Resourceful, Wary",
    "quest_giver_npc_speaking_style": "Direct",
    "inLocation_npc_ids": ["NPC002_Aura"],
    "inLocation_npc_names": ["Aura"],
    "inLocation_npc_roles": ["Logger"],
    "inLocation_npc_personalities": ["Quiet"],
    "inLocation_npc_speaking_styles": ["Quiet"],
    "location_id": "LOC002_forest",
    "location_name": "forest",
    "dungeon_ids": ["DUN001_woods", "DUN002_cave"],
    "dungeon_names": ["woods", "cave"],
    "monster_ids": ["MON001_goblin", "MON002_deer"],
    "monster_names": ["goblin", "deer"],
    "landmark_ids": ["LMK001_Tree"], 
    "landmark_names": ["Old Tree"], 
    "landmark_descriptions": ["Ancient tree"],
    "relations": [],
    "recent_memories_json": "{}", 
    "search_results_json": "{}"   
}

# ==========================================
# 2. 테스트 실행 함수
# ==========================================
def run_comparison_test():
    results = []
    print(f"🚀 모델 비교 테스트 시작: 총 {len(TEST_SCENARIOS)}개 시나리오 x {TEST_COUNT_PER_SCENARIO}회")
    print(f"📡 타겟 서버: {SERVER_URL}\n")

    for scenario in TEST_SCENARIOS:
        sc_name = scenario["name"]
        model_id = scenario["model"]
        max_tokens = scenario["tokens"]
        
        print(f"▶ Testing Scenario: [{sc_name}] (Model: {model_id}, Token: {max_tokens})")
        
        for i in range(TEST_COUNT_PER_SCENARIO):
            keyword = random.choice(KEYWORDS)
            
            # ★ 동적 설정 적용
            payload = BASE_PAYLOAD.copy()
            payload["player_dialogue"] = keyword
            payload["target_model"] = model_id        # 서버에 모델 전달
            payload["target_max_tokens"] = max_tokens # 서버에 토큰 전달

            start_time = time.time()
            success = False
            latency = 0
            text_length = 0
            error_msg = "None"
            quest_data = {} # HTML 리포트용 데이터 저장
            
            try:
                # 타임아웃 120초 (Pro 모델은 오래 걸릴 수 있음)
                response = requests.post(SERVER_URL, json=payload, timeout=120)
                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    success = True
                    data = response.json()
                    if isinstance(data, str): data = json.loads(data)
                    
                    # quest_json 추출
                    if "quest_json" in data:
                        raw = data["quest_json"]
                        quest_data = json.loads(raw) if isinstance(raw, str) else raw
                    else:
                        quest_data = data
                    
                    # 텍스트 길이 측정 (제목+설명+대사)
                    full_text = quest_data.get("quest_summary", "")
                    for step in quest_data.get("quest_steps", []):
                        full_text += step.get("description_for_player", "")
                        for line in step.get("dialogues", {}).get("on_start", []):
                            full_text += line.get("line", "")
                    text_length = len(full_text)
                else:
                    error_msg = f"HTTP {response.status_code}"
                    print(f"   ❌ 실패: {response.text}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ⚠️ 에러: {e}")

            results.append({
                "Scenario": sc_name,
                "Model": model_id,
                "MaxTokens": max_tokens,
                "Keyword": keyword,
                "Success": success,
                "Latency_ms": latency,
                "Text_Length": text_length,
                "QuestData": quest_data, # ★ HTML 생성을 위해 전체 데이터 저장
                "Error": error_msg
            })
            
            # 진행 상황 출력
            status = "✅" if success else "❌"
            print(f"   [{i+1}/{TEST_COUNT_PER_SCENARIO}] {status} {latency:.0f}ms ({keyword})")
            time.sleep(1) # 부하 방지용 딜레이

    return results # DataFrame 변환 전, raw list 반환

# ==========================================
# 3. HTML 리포트 생성 함수 (★ 추가됨)
# ==========================================
def generate_html_report(results):
    print("\n📝 HTML 리포트 생성 중...")
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Quest Generation Comparative Report</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f4f4f9; color: #333; }
            h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
            .container { max-width: 1000px; margin: 0 auto; }
            .card { background: white; padding: 25px; margin-bottom: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #3498db; }
            .card.fail { border-left-color: #e74c3c; }
            .meta { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px; }
            .meta-info { font-size: 0.95em; color: #555; }
            .tag { display: inline-block; padding: 4px 10px; border-radius: 15px; font-size: 0.85em; color: white; margin-right: 8px; font-weight: bold; }
            .tag-model { background-color: #3498db; }
            .tag-keyword { background-color: #27ae60; }
            .tag-time { background-color: #f39c12; }
            .quest-title { font-size: 1.4em; font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
            .quest-summary { color: #7f8c8d; font-style: italic; margin-bottom: 20px; line-height: 1.5; }
            .steps-container { display: flex; flex-direction: column; gap: 10px; }
            .step { padding: 15px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }
            .step-header { font-weight: bold; color: #e67e22; margin-bottom: 5px; }
            .step-desc { margin-bottom: 8px; }
            .dialogue-box { background-color: #fff3cd; padding: 8px 12px; border-radius: 6px; font-size: 0.95em; color: #856404; border: 1px solid #ffeeba; }
            .error-box { color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📜 모델별 퀘스트 생성 비교 리포트</h1>
    """

    for i, res in enumerate(results):
        scenario_name = res['Scenario']
        keyword = res['Keyword']
        latency = res['Latency_ms']
        
        card_class = "card" if res['Success'] else "card fail"
        
        quest_html = ""
        if res['Success']:
            q = res.get('QuestData', {})
            steps_html = ""
            if 'quest_steps' in q:
                for step in q['quest_steps']:
                    dialogue_html = ""
                    dialogues = step.get('dialogues', {}).get('on_start', [])
                    if dialogues:
                        line = dialogues[0].get('line', '')
                        dialogue_html = f'<div class="dialogue-box">🗣️ "{line}"</div>'
                    
                    steps_html += f"""
                    <div class="step">
                        <div class="step-header">[{step.get('objective_type')}] Step {step.get('step_id')}</div>
                        <div class="step-desc">{step.get('description_for_player')}</div>
                        {dialogue_html}
                    </div>
                    """
            
            quest_html = f"""
            <div class="quest-title">{q.get('quest_title', 'No Title')}</div>
            <div class="quest-summary">{q.get('quest_summary', 'No Summary')}</div>
            <div class="steps-container">{steps_html}</div>
            """
        else:
            quest_html = f'<div class="error-box">❌ 생성 실패: {res["Error"]}</div>'

        html_content += f"""
        <div class="{card_class}">
            <div class="meta">
                <div>
                    <span class="tag tag-model">{scenario_name}</span>
                    <span class="tag tag-keyword">Keyword: {keyword}</span>
                </div>
                <div class="meta-info">
                    <span class="tag tag-time">⏱️ {latency:.0f}ms</span>
                    <span>📝 {res['Text_Length']} chars</span>
                </div>
            </div>
            {quest_html}
        </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """
    
    try:
        with open(HTML_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✨ [성공] HTML 리포트 생성 완료: {os.path.abspath(HTML_OUTPUT_FILE)}")
    except Exception as e:
        print(f"⚠️ HTML 파일 저장 실패: {e}")

# ==========================================
# 4. 시각화 및 메인 실행
# ==========================================
def visualize_comparison(results_list):
    if not results_list:
        print("데이터가 없습니다.")
        return

    df = pd.DataFrame(results_list)

    # CSV 저장
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n💾 CSV 저장 완료: {OUTPUT_FILE}")

    # 성공한 데이터만 필터링
    success_df = df[df["Success"] == True]
    
    if success_df.empty:
        print("성공한 데이터가 없어 그래프를 그릴 수 없습니다.")
        return

    # 통계 요약 출력
    print("\n" + "="*40)
    print("📊 [모델별 성능 요약]")
    print("="*40)
    summary = success_df.groupby("Scenario")[["Latency_ms", "Text_Length"]].mean().reset_index()
    print(summary)

    # 그래프 그리기
    plt.figure(figsize=(16, 8))

    # [그래프 1] 응답 속도 비교 (Box Plot)
    plt.subplot(1, 2, 1)
    sns.boxplot(x="Scenario", y="Latency_ms", data=success_df, palette="coolwarm")
    plt.title("Response Time Comparison (Lower is Better)")
    plt.ylabel("Latency (ms)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # [그래프 2] 텍스트 생성량 비교 (Bar Plot)
    plt.subplot(1, 2, 2)
    sns.barplot(x="Scenario", y="Text_Length", data=success_df, palette="viridis")
    plt.title("Content Richness (Text Length)")
    plt.ylabel("Character Count")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        # 서버 연결 확인
        requests.get("http://127.0.0.1:8123/docs", timeout=5)
        
        # 1. 테스트 실행 및 데이터 수집
        raw_results = run_comparison_test()
        
        # 2. HTML 리포트 생성 (리스트 형태 그대로 사용)
        generate_html_report(raw_results)
        
        # 3. 그래프 그리기 (DataFrame으로 변환하여 사용)
        visualize_comparison(raw_results)
        
    except requests.exceptions.ConnectionError:
        print("\n🚨 [오류] 서버에 연결할 수 없습니다!")
        print("1. main.py가 실행 중인지 확인하세요.")
        print("2. 포트 번호(8000/8123)가 코드와 일치하는지 확인하세요.")
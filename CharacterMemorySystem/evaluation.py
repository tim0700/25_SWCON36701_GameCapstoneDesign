import requests
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import re
from collections import Counter
import os

# ==========================================
# 1. 설정 (Configuration)
# ==========================================
SERVER_URL = "http://127.0.0.1:8123/quest/generate" 
TEST_COUNT = 20
  # 테스트 반복 횟수
OUTPUT_FILE = "evaluation_results.csv"

# 테스트용 입력 키워드 (다양성을 위해 랜덤 선택)
KEYWORDS = ["배고파", "싸우자", "보물", "비밀", "사랑", "복수", "평화", "하늘", "동굴", "숲", "전설", "마법"]

# ★  기본 요청 데이터 (Landmark 추가됨)
BASE_PAYLOAD = {
    "quest_giver_npc_id": "NPC001_Amber",
    "quest_giver_npc_name": "Amber",
    "quest_giver_npc_role": "Hunter",
    "quest_giver_npc_personality": "Resourceful, Wary",
    "quest_giver_npc_speaking_style": "Direct and terse",
    
    "inLocation_npc_ids": ["NPC002_Aura", "NPC003_Katie"],
    "inLocation_npc_names": ["Aura", "Katie"],
    "inLocation_npc_roles": ["Logger", "Student"],
    "inLocation_npc_personalities": ["Solitary", "Cheerful"],
    "inLocation_npc_speaking_styles": ["Quiet", "Friendly"],
    
    "location_id": "LOC002_forest",
    "location_name": "forest",
    
    "dungeon_ids": ["DUN001_woods", "DUN002_cave"],
    "dungeon_names": ["woods", "cave"],
    
    "monster_ids": ["MON001_goblin", "MON002_deer"],
    "monster_names": ["goblin", "deer"],
    
    # ★ [NEW] 랜드마크 정보 추가
    "landmark_ids": ["LMK001_OldTree", "LMK002_BrokenStatue"],
    "landmark_names": ["Ancient Oak", "Hero's Statue"],
    "landmark_descriptions": ["A giant tree that has stood for centuries.", "A statue of a forgotten hero, half buried in moss."],

    "relations": [["NPC002_Aura", "friend"], ["NPC003_Katie", "rival"]],
    
    "recent_memories_json": "{}", 
    "search_results_json": "{}"   
}

# ==========================================
# 2. 테스트 실행 함수
# ==========================================
def run_stress_test():
    results = []
    print(f"🚀 테스트 시작: 총 {TEST_COUNT}회 요청...")
    print(f"📡 타겟 서버: {SERVER_URL}")

    for i in range(TEST_COUNT):
        keyword = random.choice(KEYWORDS)
        payload = BASE_PAYLOAD.copy()
        payload["player_dialogue"] = keyword

        start_time = time.time()
        success = False
        latency = 0
        quest_types = []
        text_length = 0
        step_count = 0
        unique_words = 0
        total_words = 0
        
        try:
            # 1. 요청 전송
            response = requests.post(SERVER_URL, json=payload, timeout=120)
            end_time = time.time()
            latency = (end_time - start_time) * 1000 # ms 단위 변환

            if response.status_code == 200:
                success = True
                data = response.json()
                
                # 2. JSON 파싱
                if isinstance(data, str):
                    data = json.loads(data)
                
                if "quest_json" in data:
                    # quest_json이 문자열이면 파싱, 딕셔너리면 그대로 사용
                    q_data_raw = data["quest_json"]
                    if isinstance(q_data_raw, str):
                        quest_data = json.loads(q_data_raw)
                    else:
                        quest_data = q_data_raw
                else:
                    quest_data = data 

                # 3. 다양성 지표 추출
                steps = quest_data.get("quest_steps", [])
                step_count = len(steps)
                
                full_text = quest_data.get("quest_summary", "")
                
                for step in steps:
                    q_type = step.get("objective_type", "UNKNOWN")
                    quest_types.append(q_type)
                    
                    desc = step.get("description_for_player", "")
                    full_text += " " + desc
                    
                    dialogues = step.get("dialogues", {})
                    for line in dialogues.get("on_start", []):
                        full_text += " " + line.get("line", "")
                
                # 4. 텍스트 분석
                text_length = len(full_text)
                words = re.findall(r'\w+', full_text)
                total_words = len(words)
                unique_words = len(set(words))

            else:
                print(f"❌ 요청 실패 (Status: {response.status_code})")
                print(f"   응답 내용: {response.text}")

        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            end_time = time.time()
            latency = (end_time - start_time) * 1000

        ttr = (unique_words / total_words) if total_words > 0 else 0
        
        results.append({
            "Round": i + 1,
            "Keyword": keyword,
            "Success": success,
            "Latency_ms": round(latency, 2),
            "Step_Count": step_count,
            "Quest_Types": ",".join(quest_types),
            "Text_Length": text_length,
            "TTR": round(ttr, 4)
        })
        
        print(f"[{i+1}/{TEST_COUNT}] 완료 - {latency:.2f}ms (키워드: {keyword})")
        time.sleep(0.2) 

    return pd.DataFrame(results)

# ==========================================
# 3. 결과 분석 및 시각화 함수
# ==========================================
def analyze_and_visualize(df):
    if df.empty:
        print("데이터가 없습니다.")
        return

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n💾 결과 저장 완료: {os.path.abspath(OUTPUT_FILE)}")

    success_df = df[df["Success"] == True]
    if success_df.empty:
        print("성공한 요청이 없어 그래프를 그릴 수 없습니다.")
        return

    print("\n" + "="*30)
    print("📊 [정량 평가 결과 요약]")
    print("="*30)
    print(f"1. 성공률: {(len(success_df)/len(df))*100:.1f}%")
    print(f"2. 평균 응답 속도: {success_df['Latency_ms'].mean():.2f} ms")
    print(f"3. 평균 텍스트 길이: {success_df['Text_Length'].mean():.1f} 자")
    
    # 그래프 설정 (한글 폰트 깨짐 방지 위해 영문 표기 권장)
    plt.figure(figsize=(15, 10))
    
    # 1. Latency Boxplot
    plt.subplot(2, 2, 1)
    sns.boxplot(y=success_df['Latency_ms'], color='lightblue')
    plt.title('Performance: Response Time Distribution')
    plt.ylabel('Latency (ms)')

    # 2. Quest Type Pie Chart
    plt.subplot(2, 2, 2)
    all_types = []
    for types in success_df['Quest_Types']:
        if types: all_types.extend(types.split(','))
    type_counts = Counter(all_types)
    if type_counts:
        plt.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%', startangle=140)
        plt.title('Diversity: Quest Type Distribution')

    # 3. Latency by Keyword Bar Chart
    plt.subplot(2, 2, 3)
    sns.barplot(x='Keyword', y='Latency_ms', data=success_df, palette='viridis', errorbar=None)
    plt.title('Performance by Input Keyword')
    plt.xticks(rotation=45)

    # 4. Text Length Distribution
    plt.subplot(2, 2, 4)
    sns.histplot(success_df['Text_Length'], bins=10, kde=True, color='salmon')
    plt.title('Diversity: Narrative Length')
    
    plt.tight_layout()
    plt.show()

# ==========================================
# 메인 실행
# ==========================================
if __name__ == "__main__":
    try:
        # 혹시 모를 연결 에러 체크를 위해 1회용 더미 요청
        requests.get("http://127.0.0.1:8123/docs", timeout=10)
        
        # 본격 테스트 시작
        df_result = run_stress_test()
        analyze_and_visualize(df_result)
        
    except requests.exceptions.ConnectionError:
        print("\n🚨 [오류] 서버에 연결할 수 없습니다!")
        print("1. 'CharacterMemorySystem' 폴더에서 main.py를 실행했는지 확인하세요.")
        print("2. 서버 주소가 'http://127.0.0.1:8123'인지 확인하세요.")
    except Exception as e:
        print(f"\n🚨 예상치 못한 오류 발생: {e}")
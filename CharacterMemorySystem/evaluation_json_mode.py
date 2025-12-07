import requests
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import os

# ==========================================
# 1. 설정
# ==========================================
SERVER_URL = "http://127.0.0.1:8123/quest/generate" # 포트 확인!
TEST_COUNT_PER_SCENARIO = 5  # 시나리오당 5회 반복

# ★ 비교 시나리오: JSON Mode 끔 vs 켬
TEST_SCENARIOS = [
    {"name": "Legacy (Text Mode)", "use_json_mode": False},
    {"name": "New (JSON Mode)",    "use_json_mode": True},
]

KEYWORDS = ["배고파", "전쟁", "사랑", "보물", "비밀"]
OUTPUT_FILE = "json_mode_comparison.csv"

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
    "dungeon_ids": ["DUN001"], "dungeon_names": ["Cave"],
    "monster_ids": ["MON001"], "monster_names": ["Goblin"],
    "landmark_ids": ["LMK001"], "landmark_names": ["Old Tree"], "landmark_descriptions": ["Big Tree"],
    "relations": [],
    "recent_memories_json": "{}", 
    "search_results_json": "{}"   
}

# ==========================================
# 2. 테스트 실행 함수
# ==========================================
def run_test():
    results = []
    print(f"🚀 성능 비교 시작: {len(TEST_SCENARIOS)} 시나리오 x {TEST_COUNT_PER_SCENARIO} 회")
    print(f"📡 타겟 서버: {SERVER_URL}\n")

    for scenario in TEST_SCENARIOS:
        sc_name = scenario["name"]
        json_mode = scenario["use_json_mode"]
        
        print(f"▶ Testing: [{sc_name}] (JSON_Mode={json_mode})")
        
        for i in range(TEST_COUNT_PER_SCENARIO):
            keyword = random.choice(KEYWORDS)
            
            # 페이로드 설정
            payload = BASE_PAYLOAD.copy()
            payload["player_dialogue"] = keyword
            payload["use_json_mode"] = json_mode # ★ 핵심 설정

            start_time = time.time()
            success = False
            latency = 0
            error_msg = "None"
            
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=120)
                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    success = True
                else:
                    error_msg = f"HTTP {response.status_code}"
            
            except Exception as e:
                error_msg = str(e)
                latency = (time.time() - start_time) * 1000

            results.append({
                "Scenario": sc_name,
                "Keyword": keyword,
                "Success": success,
                "Latency_ms": latency,
                "Error": error_msg
            })
            
            status = "✅" if success else "❌"
            print(f"   [{i+1}/{TEST_COUNT_PER_SCENARIO}] {status} {latency:.0f}ms")
            time.sleep(0.5)

    return pd.DataFrame(results)

# ==========================================
# 3. 시각화 함수
# ==========================================
def visualize(df):
    if df.empty: return

    df.to_csv(OUTPUT_FILE, index=False)
    success_df = df[df["Success"] == True]
    
    if success_df.empty:
        print("성공한 데이터가 없습니다.")
        return

    # 평균 비교 출력
    print("\n" + "="*30)
    print("📊 [평균 속도 비교]")
    print("="*30)
    print(success_df.groupby("Scenario")["Latency_ms"].mean())

    # 그래프
    plt.figure(figsize=(8, 6))
    sns.boxplot(x="Scenario", y="Latency_ms", data=success_df, palette="Set2")
    plt.title("Response Time: Legacy vs JSON Mode")
    plt.ylabel("Latency (ms)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

# ==========================================
# 4. 실행
# ==========================================
if __name__ == "__main__":
    try:
        requests.get("http://127.0.0.1:8123/docs", timeout=5)
        df = run_test()
        visualize(df)
    except Exception as e:
        print(f"\n🚨 Error: {e}")
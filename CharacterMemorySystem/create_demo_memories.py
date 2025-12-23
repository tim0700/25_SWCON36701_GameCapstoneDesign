import requests
import time
import json

BASE_URL = "http://127.0.0.1:8123"

# 데모용 NPC 초기 기억 데이터 (한국어)
demo_memories = {
    "NPC001_Garon": [
        "나는 달빛 숲 마을의 대장장이 가론이다. 쇠를 두드리는 것이 내 천직이다.",
        "내 대장간은 마을 구석에 있지만, 마을 사람들은 튼튼한 농기구가 필요할 때 항상 나를 찾는다.",
        "사냥꾼 세론과 거래하고 있다. 그가 가져오는 질 좋은 가죽은 칼자루를 감싸는 데 최고다.",
        "장로 엘다 님을 존경한다. 그녀의 지혜는 마을의 등불과 같다.",
        "최근 버려진 광산 쪽에서 이상한 기운이 느껴진다. 광석의 질도 예전 같지 않다.",
        "내 목표는 전설적인 무기를 만들어 후대에 남기는 것이다. 그것이 내 인생의 과업이다.",
        "떠돌이 상인 리라는 가끔 희귀한 광석을 가져오지만, 너무 수다스러운 게 흠이다.",
        "어릴 때 아버지가 말씀하시길, 진정한 대장장이는 불을 다루는 게 아니라 불과 대화한다고 하셨다.",
        "고대 신전에 숨겨진 금속에 대한 전설을 들은 적이 있다. 영원히 녹슬지 않는 금속이라던데...",
        "마을 우물가에서 쉬는 것을 좋아한다. 망치질로 달아오른 몸을 식히기에 딱 좋다."
    ],
    "NPC002_Lyra": [
        "안녕! 난 리라야. 이 세상 모든 희귀한 물건은 내 손을 거쳐가야 직성이 풀리지!",
        "달빛 숲 마을은 작지만 알찬 곳이야. 특히 가론 아저씨가 만드는 물건은 제법이라니까.",
        "세론? 아, 그 무뚝뚝한 사냥꾼? 겉으론 차가워 보여도 내 가장 친한 친구야.",
        "고대 신전에 엄청난 보물이 숨겨져 있다는 소문을 들었어. 내가 꼭 찾아낼 거야!",
        "마을 우물가는 정보의 보고야. 여기서 마을의 모든 소문을 들을 수 있지.",
        "저번에 숲에서 길을 잃을 뻔했는데, 세론이 도와줬어. 그 빚은 꼭 갚아야지.",
        "엘다 할머니는 뭔가 신비로운 힘이 있는 것 같아. 내 물건의 가치를 단번에 알아보시더라고.",
        "돈이 전부가 아니라고? 틀린 말은 아니지만, 돈이 있으면 모험이 훨씬 편해지는 걸.",
        "버려진 광산 입구에서 기분 나쁜 소리를 들었어. 고블린들이 뭔가 꾸미고 있는 게 분명해.",
        "언젠가 전설의 보물을 찾아서 나만의 거대한 상단을 꾸리는 게 내 꿈이야."
    ],
    "NPC003_Theron": [
        "숲은 사냥터이자 내 집이다. 바람의 소리를 들으면 숲의 상태를 알 수 있지.",
        "대장장이 가론에게 짐승 가죽을 주고 화살촉을 받는다. 공정한 거래지.",
        "리라는 시끄럽지만 미워할 수 없는 녀석이다. 위험한 숲길을 갈 땐 내가 지켜줘야 한다.",
        "최근 숲의 짐승들이 난폭해졌다. 고블린들의 움직임도 심상치 않아.",
        "내 활은 빗나가는 법이 없다. 하지만 무의미한 살생은 하지 않는다.",
        "늑대 무리가 마을 가까이 내려오고 있다. 경계를 강화해야 해.",
        "고대 신전 쪽은 금역이다. 그곳엔 우리가 알지 못하는 위험이 도사리고 있다.",
        "자연의 균형이 무너지고 있다. 부패가 숲을 잠식하기 전에 막아야 한다.",
        "엘다 장로님은 숲의 목소리를 들을 줄 아신다. 그녀의 경고를 무시해서는 안 된다.",
        "거대 거미가 나타났다는 흔적을 발견했다. 혼자 상대하기엔 벅찬 놈일 수도 있어."
    ],
    "NPC004_Elda": [
        "이 숲은 아주 오래된 기억을 품고 있단다. 나는 그 기억을 지키는 파수꾼이지.",
        "가론은 겉으론 무뚝뚝해 보여도 속은 따뜻한 아이야. 내 친손자나 다름없지.",
        "고대 신전의 봉인이 약해지고 있어. 밤마다 달빛 연못이 불안하게 일렁이는구나.",
        "마을의 평화는 위태로운 균형 위에 서 있어. 다가오는 어둠에 대비해야 한다.",
        "젊은이들은 전설을 잊어가지만, 역사는 반복되는 법이지.",
        "리라 저 아이의 호기심이 화를 부를까 걱정이구나. 신전은 함부로 들어갈 곳이 아니야.",
        "세론이 숲을 잘 지켜주고 있어 든든하구나. 하지만 그 혼자서는 역부족일지도 몰라.",
        "마을 중앙의 고목은 단순한 나무가 아니야. 우리 마을의 수호신이자 봉인의 열쇠란다.",
        "옛 예언에 따르면, 외부에서 온 여행자가 우리 마을의 운명을 바꿀 것이라고 했지.",
        "달빛이 붉게 물드는 날, 신전의 문이 열릴 게다. 그때가 오지 않기를 바랄 뿐이지."
    ]
}

def clear_memories(npc_id):
    """NPC의 기존 기억 삭제"""
    url = f"{BASE_URL}/admin/npc/{npc_id}/clear"
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            print(f"🧹 Cleared memories for {npc_id}")
            return True
        else:
            print(f"⚠️ Failed to clear memories for {npc_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error clearing memories: {e}")
        return False

def add_memory(npc_id, content):
    """NPC에게 기억 추가"""
    url = f"{BASE_URL}/memory/{npc_id}"
    payload = {
        "content": content,
        "metadata": {
            "source": "demo_initialization",
            "type": "background_story"
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print(f"✅ [{npc_id}] Added: {content[:30]}...")
            return True
        else:
            print(f"❌ [{npc_id}] Failed to add memory: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error adding memory: {e}")
        return False

def force_embed(npc_id):
    """메모리 임베딩 강제 실행 (ChromaDB 저장)"""
    url = f"{BASE_URL}/admin/npc/{npc_id}/embed-now"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            result = response.json()
            print(f"💾 [{npc_id}] Embedded {result['embedded_count']} memories to ChromaDB")
            return True
        else:
            print(f"⚠️ [{npc_id}] Force embed failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error force embedding: {e}")
        return False

def main():
    print(f"\n{'='*60}")
    print("🚀 Starting NPC Demo Memory Generation")
    print(f"Target Server: {BASE_URL}")
    print(f"{'='*60}\n")
    
    # 서버 연결 확인
    try:
        requests.get(f"{BASE_URL}/docs", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("Please make sure the CharacterMemorySystem server is running on port 8123")
        return

    for npc_id, memories in demo_memories.items():
        print(f"\nPROCESSING {npc_id}...")
        
        # 1. 기존 기억 삭제 (선택 사항, 깨끗한 시작을 위해)
        clear_memories(npc_id)
        time.sleep(0.5)
        
        # 2. 기억 추가
        count = 0
        for memory in memories:
            if add_memory(npc_id, memory):
                count += 1
            time.sleep(0.1)  # 서버 부하 방지
            
        print(f"Total {count} memories added for {npc_id}")
        
        # 3. 임베딩 강제 실행
        force_embed(npc_id)
        
        time.sleep(1)

    print(f"\n{'='*60}")
    print("✨ Demo Memory Generation Completed!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

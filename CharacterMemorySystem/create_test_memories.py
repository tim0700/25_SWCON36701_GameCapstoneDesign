"""
Create test memories for NPC002_Aura to demonstrate vector search with "golden sword" keyword.

This script creates:
- Recent memories (5): Will be in FIFO queue
- Long-term memories (10+): Some related to "golden sword", some unrelated
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8123"
NPC_ID = "NPC002_Aura"

def add_memory(content, metadata=None):
    """Add a memory to NPC."""
    url = f"{BASE_URL}/memory/{NPC_ID}"
    payload = {
        "content": content,
        "metadata": metadata or {"source": "test"}
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 201:
        print(f"✅ Added: {content[:50]}...")
        return response.json()
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None

def force_embed():
    """Force embed buffered memories to ChromaDB."""
    url = f"{BASE_URL}/admin/npc/{NPC_ID}/force-embed"
    response = requests.post(url)
    if response.status_code == 200:
        result = response.json()
        print(f"🔄 Force embedded {result['embedded_count']} memories")
        return result
    else:
        print(f"❌ Force embed failed: {response.status_code}")
        return None

def main():
    print(f"\n{'='*60}")
    print(f"Creating test memories for {NPC_ID}")
    print(f"{'='*60}\n")
    
    # ============================================================================
    # PART 1: Long-term memories (장기 기억) - 버퍼에 넣고 임베딩할 것들
    # ============================================================================
    print("\n[1/3] Creating LONG-TERM memories (will be embedded)...\n")
    
    # 🔥 HIGH SIMILARITY to "golden sword" (유사도 높음)
    longterm_memories_related = [
        "Player asked about a legendary golden sword hidden in the ancient forest ruins. The sword is said to glow with divine light.",
        "An old hermit once told stories of a golden blade forged by the gods, lost somewhere in the deep woods.",
        "The village elder mentioned a sacred golden weapon that can only be wielded by the pure of heart.",
        "Travelers spoke of seeing a golden shimmer near the abandoned temple, possibly the legendary sword.",
        "Ancient texts describe a divine golden sword as the key to unsealing the forest's greatest treasure.",
    ]
    
    # ❄️ LOW SIMILARITY to "golden sword" (유사도 낮음)
    longterm_memories_unrelated = [
        "Player helped gather firewood for the winter. It was a cold day but we managed to collect enough.",
        "The weather has been unusually rainy this season. The crops are struggling to grow properly.",
        "A pack of wolves was spotted near the village outskirts. We need to be more careful at night.",
        "The blacksmith repaired my axe yesterday. The craftsmanship is excellent as always.",
        "There was a festival last month celebrating the harvest. Everyone enjoyed the music and dancing.",
        "My cottage roof is leaking again. I need to find someone to fix it before the next storm.",
        "The logging quota has increased this year. It's becoming harder to meet the demands.",
    ]
    
    # Add all long-term memories
    all_longterm = longterm_memories_related + longterm_memories_unrelated
    
    for i, content in enumerate(all_longterm, 1):
        is_related = content in longterm_memories_related
        topic = "golden_sword" if is_related else "daily_life"
        
        add_memory(
            content=content,
            metadata={
                "source": "test_longterm",
                "topic": topic,
                "similarity_expected": "high" if is_related else "low"
            }
        )
        time.sleep(0.2)  # Rate limiting
    
    print(f"\n✅ Added {len(all_longterm)} long-term memories")
    print(f"   - {len(longterm_memories_related)} related to 'golden sword'")
    print(f"   - {len(longterm_memories_unrelated)} unrelated")
    
    # Force embed to ChromaDB
    print("\n🔄 Force embedding to ChromaDB...")
    force_embed()
    
    # ============================================================================
    # PART 2: Recent memories (단기 기억) - FIFO 큐에 남을 것들
    # ============================================================================
    print("\n[2/3] Creating RECENT memories (will stay in FIFO)...\n")
    
    recent_memories = [
        "Player just arrived at my cottage and greeted me warmly.",
        "I offered the player some fresh water from the well.",
        "Player asked about the condition of the nearby forest trails.",
        "I warned the player about the increased goblin activity in the area.",
        "Player seemed interested in exploring the deeper parts of the woods.",
    ]
    
    for i, content in enumerate(recent_memories, 1):
        add_memory(
            content=content,
            metadata={
                "source": "test_recent",
                "topic": "current_interaction",
                "sequence": i
            }
        )
        time.sleep(0.2)
    
    print(f"\n✅ Added {len(recent_memories)} recent memories")
    
    # ============================================================================
    # PART 3: Verification
    # ============================================================================
    print("\n[3/3] Verifying memory setup...\n")
    
    # Get stats
    stats_url = f"{BASE_URL}/admin/npc/{NPC_ID}/stats"
    stats_response = requests.get(stats_url)
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("📊 Memory Statistics:")
        print(f"   - Recent: {stats['recent_count']}")
        print(f"   - Buffer: {stats['buffer_count']}")
        print(f"   - Long-term (ChromaDB): {stats['longterm_count']}")
        print(f"   - Total: {stats['total_count']}")
    
    # Test vector search
    print("\n🔍 Testing vector search with 'golden sword'...\n")
    search_url = f"{BASE_URL}/memory/{NPC_ID}/search?query=golden+sword"
    search_response = requests.get(search_url)
    
    if search_response.status_code == 200:
        results = search_response.json()
        print(f"Found {results['count']} similar memories:")
        for i, result in enumerate(results['results'][:5], 1):
            score = result['similarity_score']
            content = result['memory']['content']
            print(f"   {i}. [Score: {score:.3f}] {content[:60]}...")
    
    print(f"\n{'='*60}")
    print("✅ Test memories created successfully!")
    print(f"{'='*60}\n")
    print("Now you can test quest generation with NPC002_Aura")
    print("using player input: 'golden sword'")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

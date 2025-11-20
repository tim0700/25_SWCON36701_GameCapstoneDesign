"""
Test data persistence across server restarts.

This script verifies that:
1. Recent memories are saved to disk on shutdown
2. Recent memories are restored on startup
3. ChromaDB data persists across restarts
4. Buffer data persists across restarts
"""
import requests
import time

BASE_URL = "http://localhost:8000"
TEST_NPC_ID = "persistence_test_npc"

def wait_for_server(max_retries=15):
    """Wait for server to be ready."""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is ready (attempt {i+1}/{max_retries})")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False

def add_test_memories():
    """Add 3 test memories."""
    print("\n📝 Adding 3 test memories...")
    memories = [
        "Persistence test memory 1: The player greeted me.",
        "Persistence test memory 2: We discussed the quest.",
        "Persistence test memory 3: The player left the shop."
    ]

    memory_ids = []
    for content in memories:
        response = requests.post(
            f"{BASE_URL}/memory/{TEST_NPC_ID}",
            json={"content": content},
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            memory_ids.append(data.get("memory_id"))
            print(f"  ✅ Added: {content[:40]}...")
        else:
            print(f"  ❌ Failed to add memory: {response.status_code}")
            return []

    return memory_ids

def verify_memories(expected_ids):
    """Verify memories exist."""
    print("\n🔍 Verifying memories still exist...")
    response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)

    if response.status_code != 200:
        print(f"  ❌ Failed to get memories: {response.status_code}")
        return False

    data = response.json()
    memories = data.get("memories", [])
    count = len(memories)

    print(f"  Found {count} memories")

    if count != len(expected_ids):
        print(f"  ❌ Expected {len(expected_ids)} memories, found {count}")
        return False

    # Verify IDs match
    found_ids = [mem.get("id") for mem in memories]
    for expected_id in expected_ids:
        if expected_id in found_ids:
            print(f"  ✅ Memory {expected_id} found")
        else:
            print(f"  ❌ Memory {expected_id} NOT found")
            return False

    return True

def main():
    print("=" * 70)
    print("DATA PERSISTENCE TEST")
    print("=" * 70)

    # Step 1: Verify server is running
    print("\nStep 1: Verifying server is running...")
    if not wait_for_server():
        print("❌ Server is not running. Please start it first.")
        return False

    # Step 2: Clear any existing data for this NPC
    print("\nStep 2: Clearing existing test data...")
    try:
        requests.delete(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)
        print("  ✅ Test NPC cleared")
    except:
        print("  ℹ️  No existing data to clear")

    # Step 3: Add test memories
    print("\nStep 3: Adding test memories BEFORE restart...")
    memory_ids = add_test_memories()
    if not memory_ids:
        print("❌ Failed to add memories")
        return False

    # Step 4: Verify memories exist
    print("\nStep 4: Verifying memories exist BEFORE restart...")
    if not verify_memories(memory_ids):
        print("❌ Memories not found before restart")
        return False

    # Step 5: Wait for user to restart server
    print("\n" + "=" * 70)
    print("🔄 MANUAL STEP REQUIRED")
    print("=" * 70)
    print("Please restart the server now:")
    print("  1. Press Ctrl+C to stop the server")
    print("  2. Run: source venv/bin/activate && python main.py")
    print("  3. Wait for server to fully start")
    print("  4. Press ENTER here to continue testing")
    print("=" * 70)
    input("\nPress ENTER after server has restarted...")

    # Step 6: Wait for server
    print("\nStep 6: Waiting for server to be ready after restart...")
    if not wait_for_server():
        print("❌ Server failed to start after restart")
        return False

    # Step 7: Verify memories still exist
    print("\nStep 7: Verifying memories still exist AFTER restart...")
    if not verify_memories(memory_ids):
        print("\n❌ PERSISTENCE TEST FAILED: Memories were lost after restart")
        return False

    # Step 8: Clean up
    print("\nStep 8: Cleaning up test data...")
    try:
        requests.delete(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)
        print("  ✅ Test data cleaned up")
    except:
        print("  ⚠️  Failed to clean up (manual cleanup may be needed)")

    print("\n" + "=" * 70)
    print("✅ PERSISTENCE TEST PASSED!")
    print("=" * 70)
    print("Recent memories successfully persisted across server restart.")
    print("=" * 70)

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

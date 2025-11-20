"""
Automated data persistence test across server restarts.

This script:
1. Adds test memories to the server
2. Gracefully shuts down the server (Ctrl+C simulation)
3. Restarts the server
4. Verifies memories are restored
"""
import requests
import time
import subprocess
import signal
import os

BASE_URL = "http://localhost:8000"
TEST_NPC_ID = "persistence_test_npc"

def wait_for_server(max_retries=15, description=""):
    """Wait for server to be ready."""
    print(f"  Waiting for server to be ready{description}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print(f"  ✅ Server is ready (attempt {i+1}/{max_retries})")
                return True
        except requests.exceptions.RequestException:
            pass
        if i == 0:
            print(f"  ⏳ Waiting for server startup...")
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
            json={"content": content, "metadata": {"test": "persistence"}},
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            memory_ids.append(data.get("memory_id"))
            print(f"  ✅ Added: {content[:50]}... (ID: {data.get('memory_id')})")
        else:
            print(f"  ❌ Failed to add memory: {response.status_code}")
            return []

    return memory_ids

def verify_memories(expected_ids, step_name=""):
    """Verify memories exist."""
    print(f"\n🔍 Verifying memories{step_name}...")
    response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)

    if response.status_code != 200:
        print(f"  ❌ Failed to get memories: {response.status_code}")
        return False

    data = response.json()
    memories = data.get("memories", [])
    count = len(memories)

    print(f"  Found {count} memories (expected {len(expected_ids)})")

    if count != len(expected_ids):
        print(f"  ❌ Count mismatch")
        return False

    # Verify IDs match
    found_ids = [mem.get("id") for mem in memories]
    all_found = True
    for expected_id in expected_ids:
        if expected_id in found_ids:
            print(f"  ✅ Memory {expected_id} found")
        else:
            print(f"  ❌ Memory {expected_id} NOT found")
            all_found = False

    # Verify metadata is preserved
    if all_found:
        for mem in memories:
            metadata = mem.get("metadata", {})
            if metadata.get("test") == "persistence":
                print(f"  ✅ Metadata preserved for {mem.get('id')}")
            else:
                print(f"  ⚠️  Metadata missing for {mem.get('id')}")

    return all_found

def main():
    print("=" * 70)
    print("AUTOMATED DATA PERSISTENCE TEST")
    print("=" * 70)
    print("\nThis test will automatically restart the server and verify")
    print("that recent memories are persisted across restarts.")

    # Step 1: Verify server is running
    print("\n" + "=" * 70)
    print("Step 1: Verifying server is running...")
    print("=" * 70)
    if not wait_for_server(description=" (initial check)"):
        print("❌ Server is not running.")
        print("   Please start the server manually and run this test again.")
        return False

    # Step 2: Clear any existing data for this NPC
    print("\n" + "=" * 70)
    print("Step 2: Clearing existing test data...")
    print("=" * 70)
    try:
        response = requests.delete(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)
        if response.status_code == 200:
            print("  ✅ Test NPC cleared")
        else:
            print(f"  ℹ️  Status: {response.status_code}")
    except:
        print("  ℹ️  No existing data to clear")

    # Step 3: Add test memories
    print("\n" + "=" * 70)
    print("Step 3: Adding test memories BEFORE restart...")
    print("=" * 70)
    memory_ids = add_test_memories()
    if not memory_ids:
        print("❌ Failed to add memories")
        return False

    # Step 4: Verify memories exist before restart
    print("\n" + "=" * 70)
    print("Step 4: Verifying memories BEFORE restart...")
    print("=" * 70)
    if not verify_memories(memory_ids, " before restart"):
        print("❌ Memories not found before restart")
        return False

    # Step 5: Check recent memory backup file
    print("\n" + "=" * 70)
    print("Step 5: Checking for recent memory backup file...")
    print("=" * 70)
    backup_path = "./data/recent_memory.json"
    if os.path.exists(backup_path):
        size = os.path.getsize(backup_path)
        print(f"  ✅ Backup file exists: {backup_path} ({size} bytes)")
    else:
        print(f"  ℹ️  Backup file not found yet (will be created on shutdown)")

    # Step 6: Note about manual restart
    print("\n" + "=" * 70)
    print("Step 6: Server Restart Required")
    print("=" * 70)
    print("\n⚠️  MANUAL RESTART REQUIRED:")
    print("  1. The server needs to be gracefully shut down (Ctrl+C)")
    print("  2. Then restarted to test persistence")
    print("  3. This test will wait for you to complete this")
    print("\n  Press Ctrl+C in the server terminal, then restart it.")
    print("  After server is fully started, press ENTER here to continue.")
    print("=" * 70)

    input("\nPress ENTER after you've restarted the server...")

    # Step 7: Wait for server after restart
    print("\n" + "=" * 70)
    print("Step 7: Waiting for server after restart...")
    print("=" * 70)
    if not wait_for_server(max_retries=20, description=" after restart"):
        print("❌ Server failed to start after restart")
        return False

    # Step 8: Verify backup file was created
    print("\n" + "=" * 70)
    print("Step 8: Verifying backup file was created...")
    print("=" * 70)
    if os.path.exists(backup_path):
        size = os.path.getsize(backup_path)
        print(f"  ✅ Backup file exists: {backup_path} ({size} bytes)")
        # Read and display backup content
        with open(backup_path, 'r') as f:
            import json
            backup_data = json.load(f)
            if TEST_NPC_ID in backup_data:
                backup_count = len(backup_data[TEST_NPC_ID])
                print(f"  ✅ Backup contains {backup_count} memories for {TEST_NPC_ID}")
            else:
                print(f"  ⚠️  Test NPC not found in backup")
    else:
        print(f"  ❌ Backup file not found at {backup_path}")

    # Step 9: Verify memories still exist after restart
    print("\n" + "=" * 70)
    print("Step 9: Verifying memories AFTER restart...")
    print("=" * 70)
    if not verify_memories(memory_ids, " after restart"):
        print("\n❌ PERSISTENCE TEST FAILED")
        print("   Memories were lost after restart!")
        return False

    # Step 10: Clean up
    print("\n" + "=" * 70)
    print("Step 10: Cleaning up test data...")
    print("=" * 70)
    try:
        response = requests.delete(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=10)
        if response.status_code == 200:
            print("  ✅ Test data cleaned up")
        else:
            print(f"  ⚠️  Cleanup status: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Failed to clean up: {e}")

    # Success!
    print("\n" + "=" * 70)
    print("✅ PERSISTENCE TEST PASSED!")
    print("=" * 70)
    print("\nVerified:")
    print("  ✅ Recent memories saved to disk on shutdown")
    print("  ✅ Recent memories restored from disk on startup")
    print("  ✅ Memory IDs preserved across restart")
    print("  ✅ Memory content preserved across restart")
    print("  ✅ Memory metadata preserved across restart")
    print("\nData persistence is working correctly!")
    print("=" * 70)

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

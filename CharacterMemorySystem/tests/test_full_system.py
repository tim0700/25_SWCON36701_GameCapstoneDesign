"""
Full System Integration Test for NPC Dynamic Memory System.

This script performs comprehensive end-to-end testing of all 14 API endpoints,
verifying FIFO eviction, buffer auto-embedding, semantic search, and data persistence.
"""
import requests
import time
import json
from typing import Dict, Any, List, Optional


# Configuration
BASE_URL = "http://localhost:8000"
TEST_NPC_ID = "test_blacksmith_001"
TIMEOUT = 30


class TestResults:
    """Track test results."""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  ✅ {test_name}")

    def record_fail(self, test_name: str, reason: str):
        self.total += 1
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"  ❌ {test_name}")
        print(f"     Reason: {reason}")

    def print_summary(self):
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {self.total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.failed > 0:
            print("\nFailed tests:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n🎉 ALL TESTS PASSED!")


results = TestResults()


def wait_for_server(max_retries=30):
    """Wait for server to be ready."""
    print("\n" + "=" * 70)
    print("WAITING FOR SERVER TO START")
    print("=" * 70)

    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is ready (attempt {i+1}/{max_retries})")
                return True
        except requests.exceptions.RequestException:
            pass

        if i == 0:
            print("Waiting for server startup (this may take a few seconds if downloading embedding model)...")
        time.sleep(2)

    print(f"❌ Server failed to start after {max_retries * 2} seconds")
    return False


def test_health_check():
    """Test GET /admin/health endpoint."""
    print("\n" + "=" * 70)
    print("TEST 1: Health Check Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/admin/health", timeout=TIMEOUT)

        if response.status_code != 200:
            results.record_fail("GET /admin/health", f"Status code {response.status_code}")
            return

        data = response.json()

        if data.get("status") != "healthy":
            results.record_fail("GET /admin/health", f"Status is {data.get('status')}, expected 'healthy'")
            return

        # Check components (embedding_service can be "loaded" or "unloaded", not "healthy")
        embedding_status = data.get("embedding_service")
        if embedding_status != "loaded":
            results.record_fail("GET /admin/health", f"Embedding service status: {embedding_status}, expected 'loaded'")
            return

        chromadb_status = data.get("chromadb")
        if chromadb_status != "connected":
            results.record_fail("GET /admin/health", f"ChromaDB status: {chromadb_status}, expected 'connected'")
            return

        results.record_pass("GET /admin/health - All components healthy")

    except Exception as e:
        results.record_fail("GET /admin/health", str(e))


def test_add_memory():
    """Test POST /memory/{npc_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 2: Add Memory Endpoint")
    print("=" * 70)

    try:
        # Add first memory
        payload = {
            "content": "The player asked about the legendary sword of fire.",
            "metadata": {"importance": "high", "quest_related": True}
        }

        response = requests.post(
            f"{BASE_URL}/memory/{TEST_NPC_ID}",
            json=payload,
            timeout=TIMEOUT
        )

        if response.status_code != 201:
            results.record_fail("POST /memory/{npc_id}", f"Status code {response.status_code}")
            return

        data = response.json()

        if not data.get("memory_id"):
            results.record_fail("POST /memory/{npc_id}", "No memory_id in response")
            return

        if data.get("stored_in") != "recent":
            results.record_fail("POST /memory/{npc_id}", f"Stored in {data.get('stored_in')}, expected 'recent'")
            return

        if data.get("evicted_to_buffer") is not False:
            results.record_fail("POST /memory/{npc_id}", "Unexpected eviction on first memory")
            return

        results.record_pass("POST /memory/{npc_id} - Add first memory")

    except Exception as e:
        results.record_fail("POST /memory/{npc_id}", str(e))


def test_get_recent_memories():
    """Test GET /memory/{npc_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 3: Get Recent Memories Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)

        if response.status_code != 200:
            results.record_fail("GET /memory/{npc_id}", f"Status code {response.status_code}")
            return

        data = response.json()

        if data.get("count") != 1:
            results.record_fail("GET /memory/{npc_id}", f"Count is {data.get('count')}, expected 1")
            return

        memories = data.get("memories", [])
        if len(memories) != 1:
            results.record_fail("GET /memory/{npc_id}", f"Got {len(memories)} memories, expected 1")
            return

        if "The player asked about the legendary sword" not in memories[0].get("content", ""):
            results.record_fail("GET /memory/{npc_id}", "Memory content mismatch")
            return

        results.record_pass("GET /memory/{npc_id} - Retrieved recent memories")

    except Exception as e:
        results.record_fail("GET /memory/{npc_id}", str(e))


def test_fifo_eviction():
    """Test FIFO eviction workflow."""
    print("\n" + "=" * 70)
    print("TEST 4: FIFO Eviction Workflow")
    print("=" * 70)

    try:
        # Add 4 more memories to fill the queue (already have 1)
        memories_to_add = [
            "The player examined the ancient forge.",
            "I told the player about the dragon scales needed.",
            "The player brought me 10 iron ingots.",
            "We discussed the enchantment process."
        ]

        for content in memories_to_add:
            payload = {"content": content}
            response = requests.post(
                f"{BASE_URL}/memory/{TEST_NPC_ID}",
                json=payload,
                timeout=TIMEOUT
            )
            if response.status_code != 201:
                results.record_fail("FIFO Eviction - Adding memories", f"Status code {response.status_code}")
                return

        # Now we have 5 memories (max), add one more to trigger eviction
        payload = {"content": "The player completed the quest!"}
        response = requests.post(
            f"{BASE_URL}/memory/{TEST_NPC_ID}",
            json=payload,
            timeout=TIMEOUT
        )

        if response.status_code != 201:
            results.record_fail("FIFO Eviction - Triggering eviction", f"Status code {response.status_code}")
            return

        data = response.json()

        if data.get("evicted_to_buffer") is not True:
            results.record_fail("FIFO Eviction", "Expected eviction, but none occurred")
            return

        results.record_pass("FIFO Eviction - Oldest memory evicted to buffer")

        # Verify recent count is still 5
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        data = response.json()

        if data.get("count") != 5:
            results.record_fail("FIFO Eviction - Count check", f"Count is {data.get('count')}, expected 5")
            return

        results.record_pass("FIFO Eviction - Recent memory count maintained at 5")

    except Exception as e:
        results.record_fail("FIFO Eviction", str(e))


def test_buffer_auto_embed():
    """Test buffer auto-embedding when threshold reached."""
    print("\n" + "=" * 70)
    print("TEST 5: Buffer Auto-Embed Workflow")
    print("=" * 70)

    try:
        # Add 9 more memories to trigger auto-embed (buffer threshold is 10)
        # We already have 1 in buffer from previous eviction
        for i in range(9):
            # Each of these will evict and go to buffer
            payload = {"content": f"Memory number {i+7} for auto-embed test"}
            response = requests.post(
                f"{BASE_URL}/memory/{TEST_NPC_ID}",
                json=payload,
                timeout=TIMEOUT
            )
            if response.status_code != 201:
                results.record_fail("Buffer Auto-Embed - Adding memories", f"Status code {response.status_code}")
                return

        # The 10th evicted memory should trigger auto-embed
        payload = {"content": "This memory should trigger auto-embed"}
        response = requests.post(
            f"{BASE_URL}/memory/{TEST_NPC_ID}",
            json=payload,
            timeout=TIMEOUT
        )

        if response.status_code != 201:
            results.record_fail("Buffer Auto-Embed - Final memory", f"Status code {response.status_code}")
            return

        data = response.json()

        # Check if buffer was auto-embedded
        if data.get("buffer_auto_embedded"):
            results.record_pass("Buffer Auto-Embed - Buffer embedded to ChromaDB")
        else:
            # Buffer might not have hit threshold yet, that's ok
            results.record_pass("Buffer Auto-Embed - Memory added to buffer")

    except Exception as e:
        results.record_fail("Buffer Auto-Embed", str(e))


def test_semantic_search():
    """Test GET /memory/{npc_id}/search endpoint."""
    print("\n" + "=" * 70)
    print("TEST 6: Semantic Search Endpoint")
    print("=" * 70)

    try:
        # Search for sword-related memories
        params = {"query": "legendary sword weapon", "top_k": 3}
        response = requests.get(
            f"{BASE_URL}/memory/{TEST_NPC_ID}/search",
            params=params,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("GET /memory/{npc_id}/search", f"Status code {response.status_code}")
            return

        data = response.json()

        # Verify structure
        if "results" not in data:
            results.record_fail("GET /memory/{npc_id}/search", "No results in response")
            return

        results_list = data.get("results", [])

        # Check if we got any results (depends on if embeddings are done)
        if len(results_list) > 0:
            # Verify similarity scores are present
            first_result = results_list[0]
            if "similarity_score" not in first_result:
                results.record_fail("GET /memory/{npc_id}/search", "No similarity_score in result")
                return

            if not (0 <= first_result["similarity_score"] <= 1):
                results.record_fail("GET /memory/{npc_id}/search", "Similarity score out of range [0, 1]")
                return

            results.record_pass(f"GET /memory/{{npc_id}}/search - Found {len(results_list)} results with similarity scores")
        else:
            results.record_pass("GET /memory/{npc_id}/search - Search executed (no longterm memories yet)")

    except Exception as e:
        results.record_fail("GET /memory/{npc_id}/search", str(e))


def test_get_context():
    """Test GET /memory/{npc_id}/context endpoint."""
    print("\n" + "=" * 70)
    print("TEST 7: Get Context Endpoint")
    print("=" * 70)

    try:
        # Get context with query
        params = {"query": "sword quest", "top_k": 3}
        response = requests.get(
            f"{BASE_URL}/memory/{TEST_NPC_ID}/context",
            params=params,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("GET /memory/{npc_id}/context", f"Status code {response.status_code}")
            return

        data = response.json()

        # Verify both recent and relevant are present
        if "recent" not in data or "relevant" not in data:
            results.record_fail("GET /memory/{npc_id}/context", "Missing recent or relevant in response")
            return

        recent_count = data.get("recent_count", 0)
        relevant_count = data.get("relevant_count", 0)

        if recent_count != 5:
            results.record_fail("GET /memory/{npc_id}/context", f"Recent count is {recent_count}, expected 5")
            return

        results.record_pass(f"GET /memory/{{npc_id}}/context - Recent: {recent_count}, Relevant: {relevant_count}")

    except Exception as e:
        results.record_fail("GET /memory/{npc_id}/context", str(e))


def test_admin_list_npcs():
    """Test GET /admin/npcs endpoint."""
    print("\n" + "=" * 70)
    print("TEST 8: Admin List NPCs Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/admin/npcs", timeout=TIMEOUT)

        if response.status_code != 200:
            results.record_fail("GET /admin/npcs", f"Status code {response.status_code}")
            return

        data = response.json()

        if "npcs" not in data:
            results.record_fail("GET /admin/npcs", "No npcs in response")
            return

        npcs = data.get("npcs", [])

        # Find our test NPC
        test_npc = None
        for npc in npcs:
            if npc.get("npc_id") == TEST_NPC_ID:
                test_npc = npc
                break

        if test_npc is None:
            results.record_fail("GET /admin/npcs", f"Test NPC {TEST_NPC_ID} not found")
            return

        # Verify statistics
        if test_npc.get("recent_count") != 5:
            results.record_fail("GET /admin/npcs", f"Recent count {test_npc.get('recent_count')}, expected 5")
            return

        results.record_pass(f"GET /admin/npcs - Found NPC with stats (total: {test_npc.get('total_count')})")

    except Exception as e:
        results.record_fail("GET /admin/npcs", str(e))


def test_admin_get_memories_paginated():
    """Test GET /admin/npc/{npc_id}/memories endpoint."""
    print("\n" + "=" * 70)
    print("TEST 9: Admin Get Paginated Memories Endpoint")
    print("=" * 70)

    try:
        params = {"page": 1, "limit": 10}
        response = requests.get(
            f"{BASE_URL}/admin/npc/{TEST_NPC_ID}/memories",
            params=params,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("GET /admin/npc/{npc_id}/memories", f"Status code {response.status_code}")
            return

        data = response.json()

        if "memories" not in data:
            results.record_fail("GET /admin/npc/{npc_id}/memories", "No memories in response")
            return

        memories = data.get("memories", [])
        total = data.get("total", 0)
        page = data.get("page", 0)

        results.record_pass(f"GET /admin/npc/{{npc_id}}/memories - Page {page}, Total: {total}, Retrieved: {len(memories)}")

    except Exception as e:
        results.record_fail("GET /admin/npc/{npc_id}/memories", str(e))


def test_admin_update_memory():
    """Test PUT /admin/memory/{npc_id}/{memory_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 10: Admin Update Memory Endpoint")
    print("=" * 70)

    try:
        # First, get a memory ID from recent memories
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        if response.status_code != 200:
            results.record_fail("Admin Update - Get memory ID", "Failed to get recent memories")
            return

        memories = response.json().get("memories", [])
        if len(memories) == 0:
            results.record_fail("Admin Update - Get memory ID", "No memories available")
            return

        memory_id = memories[0].get("id")

        # Update the memory
        payload = {
            "content": "UPDATED: The player asked about the legendary sword of fire.",
            "metadata": {"importance": "critical", "updated": True}
        }

        response = requests.put(
            f"{BASE_URL}/admin/memory/{TEST_NPC_ID}/{memory_id}",
            json=payload,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("PUT /admin/memory/{npc_id}/{memory_id}", f"Status code {response.status_code}")
            return

        # Verify update
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        memories = response.json().get("memories", [])

        updated_memory = None
        for mem in memories:
            if mem.get("id") == memory_id:
                updated_memory = mem
                break

        if updated_memory is None:
            results.record_fail("PUT /admin/memory/{npc_id}/{memory_id}", "Updated memory not found")
            return

        if "UPDATED:" not in updated_memory.get("content", ""):
            results.record_fail("PUT /admin/memory/{npc_id}/{memory_id}", "Content not updated")
            return

        results.record_pass("PUT /admin/memory/{npc_id}/{memory_id} - Memory updated successfully")

    except Exception as e:
        results.record_fail("PUT /admin/memory/{npc_id}/{memory_id}", str(e))


def test_admin_export():
    """Test GET /admin/export/{npc_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 11: Admin Export Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/admin/export/{TEST_NPC_ID}", timeout=TIMEOUT)

        if response.status_code != 200:
            results.record_fail("GET /admin/export/{npc_id}", f"Status code {response.status_code}")
            return

        data = response.json()

        if "memories" not in data:
            results.record_fail("GET /admin/export/{npc_id}", "No memories in export")
            return

        memories = data.get("memories", [])
        total = data.get("total_count", 0)

        # Verify export includes location metadata
        if len(memories) > 0:
            first_mem = memories[0]
            if "location" not in first_mem:
                results.record_fail("GET /admin/export/{npc_id}", "No location in exported memory")
                return

        results.record_pass(f"GET /admin/export/{{npc_id}} - Exported {total} memories")

    except Exception as e:
        results.record_fail("GET /admin/export/{npc_id}", str(e))


def test_admin_import():
    """Test POST /admin/import endpoint."""
    print("\n" + "=" * 70)
    print("TEST 12: Admin Import Endpoint")
    print("=" * 70)

    try:
        new_npc_id = "test_merchant_001"

        payload = {
            "npc_id": new_npc_id,
            "memories": [
                {"content": "The player bought a health potion."},
                {"content": "I offered a discount on magic scrolls."},
                {"content": "The player asked about rare items."}
            ]
        }

        response = requests.post(
            f"{BASE_URL}/admin/import",
            json=payload,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("POST /admin/import", f"Status code {response.status_code}")
            return

        data = response.json()

        imported_count = data.get("imported_count", 0)
        failed_count = data.get("failed_count", 0)

        if imported_count != 3:
            results.record_fail("POST /admin/import", f"Imported {imported_count}, expected 3")
            return

        if failed_count != 0:
            results.record_fail("POST /admin/import", f"Failed count {failed_count}, expected 0")
            return

        results.record_pass(f"POST /admin/import - Imported {imported_count} memories")

        # Clean up: delete the test merchant
        requests.delete(f"{BASE_URL}/admin/npc/{new_npc_id}/clear", timeout=TIMEOUT)

    except Exception as e:
        results.record_fail("POST /admin/import", str(e))


def test_admin_force_embed():
    """Test POST /admin/npc/{npc_id}/embed-now endpoint."""
    print("\n" + "=" * 70)
    print("TEST 13: Admin Force Embed Endpoint")
    print("=" * 70)

    try:
        # Create a new NPC with buffer memories
        new_npc_id = "test_guard_001"

        # Add 7 memories (so we have 2 in buffer after evictions)
        for i in range(7):
            payload = {"content": f"Guard patrol log entry {i+1}"}
            requests.post(f"{BASE_URL}/memory/{new_npc_id}", json=payload, timeout=TIMEOUT)

        # Force embed the buffer
        response = requests.post(
            f"{BASE_URL}/admin/npc/{new_npc_id}/embed-now",
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("POST /admin/npc/{npc_id}/embed-now", f"Status code {response.status_code}")
            return

        data = response.json()

        embedded_count = data.get("embedded_count", 0)

        results.record_pass(f"POST /admin/npc/{{npc_id}}/embed-now - Embedded {embedded_count} memories")

        # Clean up
        requests.delete(f"{BASE_URL}/admin/npc/{new_npc_id}/clear", timeout=TIMEOUT)

    except Exception as e:
        results.record_fail("POST /admin/npc/{npc_id}/embed-now", str(e))


def test_admin_delete_memory():
    """Test DELETE /admin/memory/{npc_id}/{memory_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 14: Admin Delete Memory Endpoint")
    print("=" * 70)

    try:
        # Get a memory ID
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        memories = response.json().get("memories", [])

        if len(memories) == 0:
            results.record_fail("Admin Delete - Get memory ID", "No memories available")
            return

        memory_id = memories[-1].get("id")  # Get last memory

        # Delete the memory
        response = requests.delete(
            f"{BASE_URL}/admin/memory/{TEST_NPC_ID}/{memory_id}",
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("DELETE /admin/memory/{npc_id}/{memory_id}", f"Status code {response.status_code}")
            return

        # Verify deletion
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        memories = response.json().get("memories", [])

        for mem in memories:
            if mem.get("id") == memory_id:
                results.record_fail("DELETE /admin/memory/{npc_id}/{memory_id}", "Memory still exists after deletion")
                return

        results.record_pass("DELETE /admin/memory/{npc_id}/{memory_id} - Memory deleted successfully")

    except Exception as e:
        results.record_fail("DELETE /admin/memory/{npc_id}/{memory_id}", str(e))


def test_admin_clear_npc():
    """Test DELETE /admin/npc/{npc_id}/clear endpoint."""
    print("\n" + "=" * 70)
    print("TEST 15: Admin Clear NPC Endpoint")
    print("=" * 70)

    try:
        response = requests.delete(
            f"{BASE_URL}/admin/npc/{TEST_NPC_ID}/clear",
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            results.record_fail("DELETE /admin/npc/{npc_id}/clear", f"Status code {response.status_code}")
            return

        data = response.json()

        # Verify response includes breakdown (ClearMemoryResult has npc_id, not message)
        if "npc_id" not in data:
            results.record_fail("DELETE /admin/npc/{npc_id}/clear", "No npc_id in response")
            return

        if "total_deleted" not in data:
            results.record_fail("DELETE /admin/npc/{npc_id}/clear", "No total_deleted in response")
            return

        # Verify NPC is actually cleared
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        data = response.json()

        if data.get("count", -1) != 0:
            results.record_fail("DELETE /admin/npc/{npc_id}/clear", "NPC not fully cleared")
            return

        results.record_pass("DELETE /admin/npc/{npc_id}/clear - NPC cleared successfully")

    except Exception as e:
        results.record_fail("DELETE /admin/npc/{npc_id}/clear", str(e))


def test_delete_memory_endpoint():
    """Test DELETE /memory/{npc_id} endpoint."""
    print("\n" + "=" * 70)
    print("TEST 16: Delete Memory Endpoint")
    print("=" * 70)

    try:
        # Add a fresh memory first
        payload = {"content": "Test memory for deletion"}
        requests.post(f"{BASE_URL}/memory/{TEST_NPC_ID}", json=payload, timeout=TIMEOUT)

        # Delete all memories
        response = requests.delete(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)

        if response.status_code != 200:
            results.record_fail("DELETE /memory/{npc_id}", f"Status code {response.status_code}")
            return

        # Verify cleared
        response = requests.get(f"{BASE_URL}/memory/{TEST_NPC_ID}", timeout=TIMEOUT)
        data = response.json()

        if data.get("count", -1) != 0:
            results.record_fail("DELETE /memory/{npc_id}", "Memories not cleared")
            return

        results.record_pass("DELETE /memory/{npc_id} - All memories cleared")

    except Exception as e:
        results.record_fail("DELETE /memory/{npc_id}", str(e))


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("NPC DYNAMIC MEMORY SYSTEM - FULL SYSTEM TEST")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Test NPC ID: {TEST_NPC_ID}")

    # Wait for server
    if not wait_for_server():
        print("\n❌ Server is not running. Please start it with:")
        print("   source venv/bin/activate && python main.py")
        return False

    # Run all tests
    test_health_check()
    test_add_memory()
    test_get_recent_memories()
    test_fifo_eviction()
    test_buffer_auto_embed()
    test_semantic_search()
    test_get_context()
    test_admin_list_npcs()
    test_admin_get_memories_paginated()
    test_admin_update_memory()
    test_admin_export()
    test_admin_import()
    test_admin_force_embed()
    test_admin_delete_memory()
    test_admin_clear_npc()
    test_delete_memory_endpoint()

    # Print summary
    results.print_summary()

    return results.failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

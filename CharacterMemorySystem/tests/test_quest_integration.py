"""
Integration test for quest generation endpoint.

Tests the unified backend quest generation with memory integration.
"""
import pytest
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8123"
TEST_NPC_ID = "test_elder_marcus"


class TestQuestIntegration:
    """Integration tests for quest generation."""
    
    def test_health_check(self):
        """Verify server is running."""
        response = requests.get(f"{BASE_URL}/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_quest_generation_basic(self):
        """Test basic quest generation."""
        quest_context = {
            "npc1_id": TEST_NPC_ID,
            "npc1_name": "Test Elder Marcus",
            "npc1_desc": "Wise village elder for testing",
            "npc2_id": "test_merchant",
            "npc2_name": "Test Merchant Sarah",
            "npc2_desc": "Traveling merchant for testing",
            "location_id": "test_forest",
            "location_name": "Test Forest Ruins",
            "dungeon_id": "",
            "monster_id": ""
        }
        
        response = requests.post(
            f"{BASE_URL}/quest/generate",
            json=quest_context,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quest_json" in data
        
        # Parse quest JSON
        quest_data = json.loads(data["quest_json"])
        assert "quest_title" in quest_data
        assert quest_data["quest_giver_npc_id"] == TEST_NPC_ID
    
    def test_memory_integration(self):
        """Verify quest generation saves memory."""
        # Generate a quest
        quest_context = {
            "npc1_id": TEST_NPC_ID,
            "npc1_name": "Test Elder Marcus",
            "npc1_desc": "Wise village elder",
            "npc2_id": "test_merchant2",
            "npc2_name": "Test Merchant Jane",
            "npc2_desc": "Another merchant",
            "location_id": "test_ruins",
            "location_name": "Ancient Ruins",
            "dungeon_id": "test_crypt",
            "monster_id": "test_goblin"
        }
        
        response = requests.post(
            f"{BASE_URL}/quest/generate",
            json=quest_context,
            timeout=60
        )
        
        assert response.status_code == 200
        
        # Give memory system a moment to process
        time.sleep(0.5)
        
        # Check if memory was saved
        memory_response = requests.get(
            f"{BASE_URL}/memory/{TEST_NPC_ID}/recent"
        )
        
        assert memory_response.status_code == 200
        memories = memory_response.json()
        
        # Find the quest-related memory
        quest_memories = [
            m for m in memories
            if "metadata" in m and
            m.get("metadata", {}).get("source") == "quest_generation"
        ]
        
        assert len(quest_memories) > 0, "Quest memory should be saved"
    
    def test_quest_with_optional_fields(self):
        """Test quest generation with dungeon and monster."""
        quest_context = {
            "npc1_id": "test_quest_giver",
            "npc1_name": "Quest Giver",
            "npc1_desc": "Gives quests",
            "npc2_id": "test_helper",
            "npc2_name": "Helper NPC",
            "npc2_desc": "Helps players",
            "location_id": "danger_zone",
            "location_name": "Dangerous Zone",
            "dungeon_id": "dark_dungeon",
            "monster_id": "boss_monster"
        }
        
        response = requests.post(
            f"{BASE_URL}/quest/generate",
            json=quest_context,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        quest_data = json.loads(data["quest_json"])
        
        # Check that quest includes dungeon/monster objectives
        assert "quest_steps" in quest_data
        assert len(quest_data["quest_steps"]) > 0


if __name__ == "__main__":
    print("Running quest integration tests...")
    print(f"Target: {BASE_URL}")
    print("\nMake sure the unified backend is running:")
    print("  cd CharacterMemorySystem")
    print("  .\\venv\\Scripts\\python.exe main.py")
    print("\nRunning tests...\n")
    
    pytest.main([__file__, "-v", "-s"])

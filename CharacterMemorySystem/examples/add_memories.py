#!/usr/bin/env python3
"""
Example: Adding Memories to NPC Dynamic Memory System

This script demonstrates how to:
1. Add individual memories to NPCs
2. Add memories with metadata
3. Handle FIFO eviction
4. Trigger buffer auto-embedding
5. Retrieve recent memories

Requirements:
- Server running on http://localhost:8000
- Python 3.10+ with requests library

Usage:
    python examples/add_memories.py
"""

import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional


# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def add_memory(
    npc_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a memory to an NPC.

    Args:
        npc_id: Unique identifier for the NPC
        content: Memory text content
        metadata: Optional metadata dictionary

    Returns:
        API response as dictionary
    """
    url = f"{BASE_URL}/memory/{npc_id}"
    payload = {"content": content}
    if metadata:
        payload["metadata"] = metadata

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error adding memory: {e}")
        return {"status": "error", "message": str(e)}


def get_recent_memories(npc_id: str) -> Dict[str, Any]:
    """
    Get recent memories for an NPC.

    Args:
        npc_id: Unique identifier for the NPC

    Returns:
        API response with memories
    """
    url = f"{BASE_URL}/memory/{npc_id}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting memories: {e}")
        return {"status": "error", "message": str(e)}


def clear_npc_memories(npc_id: str):
    """Clear all memories for an NPC (cleanup)."""
    url = f"{BASE_URL}/memory/{npc_id}"
    try:
        response = requests.delete(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Warning: Could not clear memories: {e}")
        return None


def main():
    """Main demonstration function."""
    print_section("NPC Dynamic Memory System - Add Memories Example")

    # Test NPC
    npc_id = "example_blacksmith_001"

    # Clean start
    print("\n🧹 Cleaning up any existing test data...")
    clear_npc_memories(npc_id)

    # =========================================================================
    # Example 1: Add a simple memory
    # =========================================================================
    print_section("Example 1: Adding a Simple Memory")

    result = add_memory(
        npc_id=npc_id,
        content="The player greeted me warmly and asked about my wares."
    )

    print(f"✅ Memory added successfully!")
    print(f"   Memory ID: {result.get('memory_id')}")
    print(f"   Stored in: {result.get('stored_in')}")
    print(f"   Eviction: {result.get('evicted_to_buffer')}")

    # =========================================================================
    # Example 2: Add memory with metadata
    # =========================================================================
    print_section("Example 2: Adding Memory with Metadata")

    result = add_memory(
        npc_id=npc_id,
        content="The player purchased a steel sword for 50 gold.",
        metadata={
            "transaction_type": "sale",
            "item": "steel_sword",
            "amount": 50,
            "currency": "gold",
            "timestamp_utc": datetime.utcnow().isoformat()
        }
    )

    print(f"✅ Memory with metadata added!")
    print(f"   Memory ID: {result.get('memory_id')}")
    print(f"   Metadata attached: transaction_type, item, amount, currency")

    # =========================================================================
    # Example 3: Add multiple memories (demonstrate FIFO)
    # =========================================================================
    print_section("Example 3: Adding Multiple Memories (FIFO Queue)")

    memories_to_add = [
        "The player asked about legendary weapons.",
        "I told the player about the Dragon Slayer sword my master once forged.",
        "The player seemed very interested in learning smithing.",
    ]

    for i, content in enumerate(memories_to_add, start=3):
        result = add_memory(npc_id=npc_id, content=content)
        print(f"   {i}. Added: {content[:50]}...")
        time.sleep(0.5)  # Small delay to show sequential adds

    # Get current count
    recent = get_recent_memories(npc_id)
    count = recent.get("count", 0)
    print(f"\n📊 Current recent memory count: {count}/5")

    # =========================================================================
    # Example 4: Trigger FIFO eviction
    # =========================================================================
    print_section("Example 4: Triggering FIFO Eviction")

    print("Adding 6th memory (queue is full at 5)...")
    result = add_memory(
        npc_id=npc_id,
        content="The player left the shop and said they would return tomorrow."
    )

    if result.get("evicted_to_buffer"):
        print("✅ FIFO Eviction triggered!")
        print("   Oldest memory evicted to buffer")
        print("   Recent queue still at 5 items (FIFO behavior)")
    else:
        print("⚠️  No eviction (queue not full yet)")

    # =========================================================================
    # Example 5: View recent memories
    # =========================================================================
    print_section("Example 5: Viewing Recent Memories")

    recent = get_recent_memories(npc_id)

    if recent.get("status") == "success":
        print(f"Recent memories for {npc_id}:")
        print(f"Count: {recent.get('count')}\n")

        for i, memory in enumerate(recent.get("memories", []), start=1):
            print(f"   {i}. [{memory.get('id')}]")
            print(f"      Content: {memory.get('content')}")
            print(f"      Timestamp: {memory.get('timestamp')}")
            if memory.get("metadata"):
                print(f"      Metadata: {memory.get('metadata')}")
            print()

    # =========================================================================
    # Example 6: Add many memories to trigger auto-embed
    # =========================================================================
    print_section("Example 6: Triggering Buffer Auto-Embed")

    print("Adding 10 more memories to fill buffer and trigger auto-embed...")
    print("(Buffer threshold is 10 items)\n")

    batch_memories = [
        "A customer complained about sword prices.",
        "I repaired a damaged shield for a knight.",
        "The player asked if I buy scrap metal.",
        "I explained my apprenticeship story.",
        "A merchant visited selling rare ores.",
        "The player returned with damaged armor.",
        "I offered a discount for bulk purchases.",
        "A guard commissioned a custom helmet.",
        "The player asked about enchanted weapons.",
        "I closed the shop for the day.",
    ]

    auto_embedded = False
    for i, content in enumerate(batch_memories, start=1):
        result = add_memory(npc_id=npc_id, content=content)

        evicted = result.get("evicted_to_buffer", False)
        embedded = result.get("buffer_auto_embedded", False)

        status = "📝 Added"
        if evicted:
            status = "📤 Added (evicted oldest)"
        if embedded:
            status = "🔥 Added (AUTO-EMBED TRIGGERED!)"
            auto_embedded = True

        print(f"   {i:2d}. {status}: {content[:40]}...")

        if embedded:
            print("\n" + "🎉" * 35)
            print("   BUFFER AUTO-EMBED COMPLETE!")
            print("   - 10 memories embedded to ChromaDB")
            print("   - Buffer cleared")
            print("   - Memories now searchable via semantic search")
            print("🎉" * 35 + "\n")
            break

    if not auto_embedded:
        print("\n⚠️  Auto-embed not triggered yet. Add more memories to reach buffer threshold.")

    # =========================================================================
    # Example 7: Final statistics
    # =========================================================================
    print_section("Example 7: Final Statistics")

    # Get admin stats
    url = f"{BASE_URL}/admin/npcs"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # Find our NPC
        npc_stats = None
        for npc in data.get("npcs", []):
            if npc.get("npc_id") == npc_id:
                npc_stats = npc
                break

        if npc_stats:
            print(f"NPC: {npc_id}")
            print(f"  Recent memories: {npc_stats.get('recent_count')}")
            print(f"  Buffer memories: {npc_stats.get('buffer_count')}")
            print(f"  Long-term memories: {npc_stats.get('longterm_count')}")
            print(f"  Total memories: {npc_stats.get('total_count')}")
            print(f"  Last memory at: {npc_stats.get('last_memory_at')}")
        else:
            print("⚠️  NPC stats not available")

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not fetch stats: {e}")

    # =========================================================================
    # Cleanup
    # =========================================================================
    print_section("Cleanup")

    print("Cleaning up test data...")
    result = clear_npc_memories(npc_id)
    if result:
        print(f"✅ Deleted {result.get('total_deleted', 0)} memories")
    else:
        print("⚠️  Manual cleanup may be needed")

    print("\n" + "=" * 70)
    print("  Example Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Try examples/search_memories.py for semantic search")
    print("  2. Try examples/bulk_import.json for bulk data import")
    print("  3. See docs/API.md for full API reference")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Check server health before running
    print("Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/admin/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy and ready\n")
            main()
        else:
            print("❌ Server health check failed")
            print("   Please ensure the server is running on http://localhost:8000")
            print("   Run: python main.py")
    except requests.exceptions.RequestException as e:
        print("❌ Cannot connect to server")
        print(f"   Error: {e}")
        print("   Please ensure the server is running on http://localhost:8000")
        print("   Run: python main.py")

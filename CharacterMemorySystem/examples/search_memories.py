#!/usr/bin/env python3
"""
Example: Semantic Search in NPC Dynamic Memory System

This script demonstrates how to:
1. Add diverse memories to create searchable content
2. Perform semantic searches with natural language queries
3. Use the context endpoint for LLM integration
4. Understand similarity scores
5. Compare recent vs. semantic retrieval

Requirements:
- Server running on http://localhost:8000
- Python 3.10+ with requests library
- Embedding model loaded (auto-loaded on server start)

Usage:
    python examples/search_memories.py
"""

import requests
import time
from typing import Dict, Any, List, Optional


# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def add_memory(npc_id: str, content: str, metadata: Optional[Dict] = None) -> Dict:
    """Add a memory to an NPC."""
    url = f"{BASE_URL}/memory/{npc_id}"
    payload = {"content": content}
    if metadata:
        payload["metadata"] = metadata

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def search_memories(npc_id: str, query: str, top_k: int = 3) -> Dict:
    """
    Search for semantically similar memories.

    Args:
        npc_id: NPC identifier
        query: Natural language search query
        top_k: Number of results to return

    Returns:
        API response with similar memories
    """
    url = f"{BASE_URL}/memory/{npc_id}/search"
    params = {"query": query, "top_k": top_k}

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def get_context(npc_id: str, query: Optional[str] = None, top_k: int = 3) -> Dict:
    """
    Get combined context (recent + relevant memories).

    Args:
        npc_id: NPC identifier
        query: Optional search query
        top_k: Number of relevant results

    Returns:
        API response with recent and relevant memories
    """
    url = f"{BASE_URL}/memory/{npc_id}/context"
    params = {}
    if query:
        params["query"] = query
    params["top_k"] = top_k

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def force_embed(npc_id: str) -> Dict:
    """Force immediate embedding of buffer."""
    url = f"{BASE_URL}/admin/npc/{npc_id}/embed-now"
    try:
        response = requests.post(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def clear_npc(npc_id: str):
    """Clear all memories for an NPC."""
    url = f"{BASE_URL}/memory/{npc_id}"
    try:
        response = requests.delete(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except:
        return None


def setup_test_data(npc_id: str) -> int:
    """
    Create diverse memories for semantic search testing.

    Returns:
        Number of memories created
    """
    print("📝 Creating diverse memories for testing...")

    memories = [
        # Backstory memories
        "I learned smithing from my father, who was a legendary weaponsmith.",
        "My father once forged a sword that slayed a dragon in the northern mountains.",
        "I spent 10 years as an apprentice before opening my own shop.",

        # Trade and commerce
        "Most customers prefer steel weapons for their balance of cost and durability.",
        "I sell iron daggers to beginners for 15 gold pieces.",
        "Enchanted weapons require special materials and cost at least 500 gold.",

        # Recent player interactions
        "The player asked about legendary weapons yesterday.",
        "A customer complained that my prices are too high compared to the market.",
        "I repaired a damaged shield for a knight last week.",

        # Personal preferences
        "I prefer working with steel because it's easier to shape than iron.",
        "I refuse to sell weapons to bandits or criminals.",
        "My favorite commission is crafting custom swords for heroes.",

        # Lore and knowledge
        "Dragon scales can be used to forge nearly indestructible armor.",
        "The ancient elves knew metallurgy secrets that are now lost.",
        "Moonstone ore is rare and only found in deep caves.",

        # Daily routine
        "I open the shop at dawn and close at sunset every day.",
        "Tuesday is my day off when I visit the market for supplies.",
        "I sharpen blades every morning before customers arrive.",
    ]

    count = 0
    for content in memories:
        result = add_memory(npc_id, content)
        if result.get("status") == "success":
            count += 1
            print(f"   ✅ Added memory {count}/{len(memories)}")
        else:
            print(f"   ❌ Failed to add memory: {result.get('message')}")

        time.sleep(0.1)  # Small delay

    return count


def main():
    """Main demonstration function."""
    print_section("NPC Dynamic Memory System - Semantic Search Example")

    # Test NPC
    npc_id = "example_blacksmith_search"

    # Clean start
    print("\n🧹 Cleaning up any existing test data...")
    clear_npc(npc_id)

    # =========================================================================
    # Setup: Create test data
    # =========================================================================
    print_section("Setup: Creating Test Data")

    count = setup_test_data(npc_id)
    print(f"\n✅ Created {count} diverse memories")

    # Force embed buffer to make memories searchable
    print("\n🔥 Force-embedding buffer to make memories searchable...")
    result = force_embed(npc_id)
    if result.get("status") == "success":
        embedded_count = result.get("embedded_count", 0)
        print(f"✅ Embedded {embedded_count} memories to ChromaDB")
    else:
        print("⚠️  Force embed failed (buffer may be empty)")

    # Wait for embedding to complete
    print("⏳ Waiting for embedding to complete...")
    time.sleep(2)

    # =========================================================================
    # Example 1: Basic semantic search
    # =========================================================================
    print_section("Example 1: Basic Semantic Search")

    query = "legendary sword weapon"
    print(f"Query: \"{query}\"")
    print(f"Top-k: 3\n")

    result = search_memories(npc_id, query, top_k=3)

    if result.get("status") == "success":
        print(f"✅ Found {result.get('count')} similar memories:\n")

        for i, item in enumerate(result.get("results", []), start=1):
            memory = item.get("memory", {})
            score = item.get("similarity_score", 0.0)

            print(f"   {i}. Similarity: {score:.2f}")
            print(f"      Content: {memory.get('content')}")
            print(f"      ID: {memory.get('id')}")
            print()
    else:
        print(f"❌ Search failed: {result.get('message')}")

    # =========================================================================
    # Example 2: Different queries, different results
    # =========================================================================
    print_section("Example 2: Multiple Semantic Queries")

    queries = [
        "dragon fighting armor protection",
        "shop opening hours schedule",
        "weapons for beginners cheap prices",
        "apprentice learning training blacksmith"
    ]

    for query in queries:
        print(f"\n🔍 Query: \"{query}\"")
        result = search_memories(npc_id, query, top_k=2)

        if result.get("status") == "success":
            for i, item in enumerate(result.get("results", []), start=1):
                memory = item.get("memory", {})
                score = item.get("similarity_score", 0.0)
                content = memory.get('content', '')[:60]
                print(f"   {i}. [{score:.2f}] {content}...")
        else:
            print(f"   ❌ No results")

    # =========================================================================
    # Example 3: Understanding similarity scores
    # =========================================================================
    print_section("Example 3: Understanding Similarity Scores")

    print("Testing queries with varying relevance:\n")

    test_queries = [
        ("sword", "Highly relevant (exact keyword)"),
        ("blacksmith apprenticeship", "Very relevant (core topic)"),
        ("magic spells wizardry", "Low relevance (unrelated)"),
    ]

    for query, description in test_queries:
        print(f"Query: \"{query}\" ({description})")
        result = search_memories(npc_id, query, top_k=1)

        if result.get("status") == "success" and result.get("count", 0) > 0:
            item = result["results"][0]
            score = item.get("similarity_score", 0.0)
            content = item["memory"]["content"][:50]

            if score > 0.7:
                relevance = "HIGH"
            elif score > 0.5:
                relevance = "MEDIUM"
            else:
                relevance = "LOW"

            print(f"  → Score: {score:.3f} ({relevance})")
            print(f"     Match: {content}...")
        else:
            print(f"  → No results")
        print()

    print("Score interpretation:")
    print("  0.7 - 1.0: Highly relevant (strong semantic match)")
    print("  0.5 - 0.7: Moderately relevant (related concepts)")
    print("  0.0 - 0.5: Low relevance (weak or no connection)")

    # =========================================================================
    # Example 4: Context endpoint (recent + relevant)
    # =========================================================================
    print_section("Example 4: Context Endpoint for LLM Integration")

    # Add a few more recent memories
    print("Adding fresh recent memories...")
    add_memory(npc_id, "The player just entered my shop and is browsing.")
    add_memory(npc_id, "They're looking at the weapon display on the wall.")
    time.sleep(0.5)

    # Get context
    query = "What weapons do you recommend for a beginner adventurer?"
    print(f"\nLLM Query: \"{query}\"")
    print("Getting context (recent + relevant)...\n")

    result = get_context(npc_id, query=query, top_k=3)

    if result.get("status") == "success":
        recent_count = result.get("recent_count", 0)
        relevant_count = result.get("relevant_count", 0)

        print(f"✅ Retrieved context:")
        print(f"   Recent memories: {recent_count}")
        print(f"   Relevant memories: {relevant_count}")

        print("\n📝 Recent memories (chronological):")
        for i, memory in enumerate(result.get("recent", []), start=1):
            content = memory.get("content", "")[:60]
            print(f"   {i}. {content}...")

        print("\n🔍 Relevant memories (semantic match):")
        for i, item in enumerate(result.get("relevant", []), start=1):
            memory = item.get("memory", {})
            score = item.get("similarity_score", 0.0)
            content = memory.get("content", "")[:60]
            print(f"   {i}. [{score:.2f}] {content}...")

        print("\n💡 Use case:")
        print("   Send both 'recent' and 'relevant' to your LLM for:")
        print("   - Recent context: What just happened")
        print("   - Relevant context: Related background knowledge")
        print("   - Combined: Rich, contextual NPC responses")
    else:
        print(f"❌ Context retrieval failed: {result.get('message')}")

    # =========================================================================
    # Example 5: Context without query (recent only)
    # =========================================================================
    print_section("Example 5: Context Without Query (Recent Only)")

    result = get_context(npc_id)  # No query parameter

    if result.get("status") == "success":
        recent_count = result.get("recent_count", 0)
        relevant_count = result.get("relevant_count", 0)

        print(f"Recent memories: {recent_count}")
        print(f"Relevant memories: {relevant_count}")
        print("\nWhen no query is provided:")
        print("  ✅ Returns recent memories (last 5 interactions)")
        print("  ✅ No semantic search performed (faster)")
        print("  ✅ Useful for simple conversation continuity")
    else:
        print(f"❌ Failed: {result.get('message')}")

    # =========================================================================
    # Example 6: Adjusting top_k parameter
    # =========================================================================
    print_section("Example 6: Adjusting top_k Parameter")

    query = "weapons"

    for top_k in [1, 3, 5]:
        print(f"\nQuery: \"{query}\" (top_k={top_k})")
        result = search_memories(npc_id, query, top_k=top_k)

        if result.get("status") == "success":
            count = result.get("count", 0)
            print(f"  → Returned {count} results")

            if count > 0:
                scores = [item.get("similarity_score", 0) for item in result.get("results", [])]
                print(f"     Similarity range: {min(scores):.2f} - {max(scores):.2f}")
        else:
            print(f"  → Failed: {result.get('message')}")

    print("\nRecommendations:")
    print("  • top_k=3: Default, good balance")
    print("  • top_k=1: When you need only the best match")
    print("  • top_k=5-10: For broader context")

    # =========================================================================
    # Cleanup
    # =========================================================================
    print_section("Cleanup")

    print("Cleaning up test data...")
    result = clear_npc(npc_id)
    if result:
        total = result.get("total_deleted", 0)
        print(f"✅ Deleted {total} memories")
    else:
        print("⚠️  Manual cleanup may be needed")

    print("\n" + "=" * 70)
    print("  Example Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Semantic search finds related content, not just keywords")
    print("  2. Similarity scores range from 0.0 (unrelated) to 1.0 (identical)")
    print("  3. Use /context endpoint for LLM integration (recent + relevant)")
    print("  4. Adjust top_k based on how much context you need")
    print("\nNext steps:")
    print("  • See docs/API.md for full endpoint reference")
    print("  • See docs/ARCHITECTURE.md for embedding details")
    print("  • Try examples/bulk_import.json for loading sample data")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Check server health
    print("Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/admin/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            embedding_status = health.get("embedding_service")

            if embedding_status == "loaded":
                print("✅ Server is healthy and ready")
                print("✅ Embedding service loaded\n")
                main()
            else:
                print("❌ Embedding service not loaded")
                print("   Semantic search requires embeddings")
                print("   Check server logs and .env configuration")
        else:
            print("❌ Server health check failed")
    except requests.exceptions.RequestException as e:
        print("❌ Cannot connect to server")
        print(f"   Error: {e}")
        print("   Please ensure the server is running on http://localhost:8000")
        print("   Run: python main.py")

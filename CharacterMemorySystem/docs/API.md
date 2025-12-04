# NPC Dynamic Memory System - API Reference

**Version**: 1.0.0
**Base URL**: `http://localhost:8000`
**Last Updated**: 2025-11-17

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Memory Endpoints](#memory-endpoints)
   - [Add Memory](#post-memorynpc_id)
   - [Get Recent Memories](#get-memorynpc_id)
   - [Search Memories](#get-memorynpc_idsearch)
   - [Get Context](#get-memorynpc_idcontext)
   - [Clear All Memories](#delete-memorynpc_id)
5. [Admin Endpoints](#admin-endpoints)
   - [List All NPCs](#get-adminnpcs)
   - [Get NPC Memories (Paginated)](#get-adminnpcnpc_idmemories)
   - [Update Memory](#put-adminmemorynpc_idmemory_id)
   - [Delete Memory](#delete-adminmemorynpc_idmemory_id)
   - [Force Embed](#post-adminnpcnpc_idembed-now)
   - [Clear NPC](#delete-adminnpcnpc_idclear)
   - [Bulk Import](#post-adminimport)
   - [Export Memories](#get-adminexportnpc_id)
   - [Health Check](#get-adminhealth)
6. [Data Models](#data-models)

---

## Overview

The NPC Dynamic Memory System provides a REST API for managing NPC memories with automatic semantic search capabilities. The system uses a three-tier architecture:

1. **Recent Memory** (FIFO queue, 5 items per NPC) - Fast access to recent interactions
2. **Buffer** (10 items, internal) - Temporary storage before embedding
3. **Long-term Memory** (ChromaDB) - Semantic search on embedded memories

### Key Features

- **Automatic FIFO eviction**: Recent memories auto-evict to buffer when full
- **Auto-embedding**: Buffer automatically embeds to ChromaDB at threshold (10 items)
- **Semantic search**: Find relevant memories using natural language queries
- **Per-NPC isolation**: Each NPC has separate memory storage
- **Persistence**: All data persists across server restarts

---

## Authentication

**Current Version**: No authentication required (development mode)

**Production Recommendation**: Add API key authentication or OAuth 2.0 before deployment.

```python
# Future production usage (not yet implemented)
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}
```

---

## Error Handling

All endpoints return structured error responses with appropriate HTTP status codes.

### Standard Error Response

```json
{
  "status": "error",
  "message": "Human-readable error description",
  "error_code": "ERROR_IDENTIFIER"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/DELETE request |
| 201 | Created | Memory successfully added |
| 400 | Bad Request | Invalid request data (validation failed) |
| 404 | Not Found | NPC or memory not found |
| 422 | Unprocessable Entity | Pydantic validation error |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Embedding service not loaded |

### Example Error Response

```json
{
  "status": "error",
  "message": "Memory not found in any storage location",
  "error_code": "MEMORY_NOT_FOUND"
}
```

---

## Memory Endpoints

These are the primary endpoints used by the LLM agent backend.

### POST /memory/{npc_id}

**Add a new memory for an NPC**

Adds a memory to the NPC's recent memory queue. If the queue is full (>5 items), the oldest memory is automatically evicted to the buffer.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

**Request Body:**
```json
{
  "content": "string (required)",
  "metadata": {
    "key": "value"
  }
}
```

#### Response (201 Created)

```json
{
  "status": "success",
  "message": "Memory added successfully for NPC test_npc",
  "memory_id": "mem_abc123def456",
  "stored_in": "recent",
  "evicted_to_buffer": false,
  "buffer_auto_embedded": false
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `message` | string | Human-readable status message |
| `memory_id` | string | Unique ID of the created memory |
| `stored_in` | string | "recent" (always for new memories) |
| `evicted_to_buffer` | boolean | True if this addition caused FIFO eviction |
| `buffer_auto_embedded` | boolean | True if buffer hit threshold and auto-embedded |

#### Example Request

```bash
curl -X POST "http://localhost:8000/memory/blacksmith_001" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The player asked about legendary swords.",
    "metadata": {
      "category": "quest_inquiry",
      "session_id": "sess_123"
    }
  }'
```

#### Example Response (FIFO Eviction)

```json
{
  "status": "success",
  "message": "Memory added successfully for NPC blacksmith_001",
  "memory_id": "mem_789ghi012jkl",
  "stored_in": "recent",
  "evicted_to_buffer": true,
  "buffer_auto_embedded": false
}
```

#### Example Response (Buffer Auto-Embed)

```json
{
  "status": "success",
  "message": "Memory added successfully for NPC blacksmith_001",
  "memory_id": "mem_345mno678pqr",
  "stored_in": "recent",
  "evicted_to_buffer": true,
  "buffer_auto_embedded": true
}
```

---

### GET /memory/{npc_id}

**Get recent memories for an NPC**

Returns the most recent memories (up to 5) in chronological order (oldest first).

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Retrieved 5 recent memories",
  "npc_id": "blacksmith_001",
  "memories": [
    {
      "id": "mem_abc123",
      "content": "The player greeted me warmly.",
      "timestamp": "2025-11-17T10:30:00.123456",
      "metadata": {
        "category": "greeting"
      }
    },
    {
      "id": "mem_def456",
      "content": "We discussed weapon prices.",
      "timestamp": "2025-11-17T10:32:15.789012",
      "metadata": {
        "category": "conversation"
      }
    }
  ],
  "count": 2
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/memory/blacksmith_001"
```

#### Notes

- Returns empty list if NPC has no recent memories
- Maximum 5 memories (FIFO queue limit)
- Ordered chronologically (oldest first)
- Only includes recent memory queue, not buffer or long-term

---

### GET /memory/{npc_id}/search

**Semantic search for relevant memories**

Searches the NPC's long-term memory (ChromaDB) for semantically similar memories using vector embeddings.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

**Query Parameters:**
- `query` (string, required) - Natural language search query
- `top_k` (integer, optional, default=3) - Number of results to return

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Found 3 similar memories",
  "npc_id": "blacksmith_001",
  "query": "legendary sword weapon",
  "results": [
    {
      "memory": {
        "id": "mem_xyz789",
        "content": "I once forged a legendary dragon-slayer sword.",
        "timestamp": "2025-11-15T14:20:00.000000",
        "metadata": {
          "category": "backstory"
        }
      },
      "similarity_score": 0.87
    },
    {
      "memory": {
        "id": "mem_uvw456",
        "content": "The player asked about enchanted weapons.",
        "timestamp": "2025-11-16T09:15:00.000000",
        "metadata": {
          "category": "quest_inquiry"
        }
      },
      "similarity_score": 0.72
    }
  ],
  "count": 2
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/memory/blacksmith_001/search?query=legendary%20sword&top_k=3"
```

#### Notes

- Searches only long-term memory (embedded memories in ChromaDB)
- Similarity scores range from 0.0 (unrelated) to 1.0 (identical)
- Returns empty list if no memories have been embedded yet
- Query is embedded using the same model (all-MiniLM-L6-v2)

---

### GET /memory/{npc_id}/context

**Get combined context (recent + relevant)**

Returns both recent memories AND semantically relevant memories. This is the recommended endpoint for LLM context retrieval.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

**Query Parameters:**
- `query` (string, optional) - Search query for relevant memories
- `top_k` (integer, optional, default=3) - Number of relevant results

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Retrieved context: 5 recent, 3 relevant",
  "npc_id": "blacksmith_001",
  "recent": [
    {
      "id": "mem_recent1",
      "content": "The player just entered my shop.",
      "timestamp": "2025-11-17T11:00:00.000000",
      "metadata": {}
    }
  ],
  "relevant": [
    {
      "memory": {
        "id": "mem_relevant1",
        "content": "I prefer customers who are polite.",
        "timestamp": "2025-11-10T08:00:00.000000",
        "metadata": {}
      },
      "similarity_score": 0.65
    }
  ],
  "recent_count": 5,
  "relevant_count": 3
}
```

#### Example Request (with query)

```bash
curl -X GET "http://localhost:8000/memory/blacksmith_001/context?query=weapons"
```

#### Example Request (without query, recent only)

```bash
curl -X GET "http://localhost:8000/memory/blacksmith_001/context"
```

#### Notes

- **With query**: Returns recent + semantically relevant memories
- **Without query**: Returns recent memories only
- Combines short-term and long-term memory for optimal LLM context
- Recent memories are always in chronological order
- Relevant memories are ordered by similarity score

---

### DELETE /memory/{npc_id}

**Clear all memories for an NPC**

Deletes all memories (recent, buffer, and long-term) for the specified NPC.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Cleared all memories for NPC blacksmith_001",
  "npc_id": "blacksmith_001",
  "recent_deleted": 5,
  "buffer_deleted": 7,
  "longterm_deleted": 43,
  "total_deleted": 55
}
```

#### Example Request

```bash
curl -X DELETE "http://localhost:8000/memory/blacksmith_001"
```

#### Notes

- Irreversible operation
- Clears all three storage locations (recent, buffer, longterm)
- Returns counts for each location

---

## Admin Endpoints

Administrative endpoints for debugging, monitoring, and bulk operations.

### GET /admin/npcs

**List all NPCs with statistics**

Returns a list of all NPCs in the system with memory counts and timestamps.

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Found 3 NPCs",
  "npcs": [
    {
      "npc_id": "blacksmith_001",
      "recent_count": 5,
      "buffer_count": 8,
      "longterm_count": 127,
      "total_count": 140,
      "last_memory_at": "2025-11-17T11:30:00.123456"
    },
    {
      "npc_id": "merchant_002",
      "recent_count": 3,
      "buffer_count": 0,
      "longterm_count": 45,
      "total_count": 48,
      "last_memory_at": "2025-11-17T09:15:00.789012"
    }
  ],
  "count": 2
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/admin/npcs"
```

---

### GET /admin/npc/{npc_id}/memories

**Get all memories for an NPC (paginated)**

Returns all memories across all storage locations with pagination support.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

**Query Parameters:**
- `page` (integer, optional, default=1) - Page number (1-indexed)
- `limit` (integer, optional, default=20) - Items per page (max 100)

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Retrieved 20 of 127 total memories",
  "npc_id": "blacksmith_001",
  "memories": [
    {
      "memory": {
        "id": "mem_abc123",
        "content": "The player greeted me.",
        "timestamp": "2025-11-17T11:00:00.000000",
        "metadata": {}
      },
      "location": "recent"
    },
    {
      "memory": {
        "id": "mem_def456",
        "content": "I discussed prices.",
        "timestamp": "2025-11-17T10:30:00.000000",
        "metadata": {}
      },
      "location": "buffer"
    },
    {
      "memory": {
        "id": "mem_ghi789",
        "content": "My backstory includes...",
        "timestamp": "2025-11-10T08:00:00.000000",
        "metadata": {}
      },
      "location": "longterm"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 127,
  "count": 20
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/admin/npc/blacksmith_001/memories?page=1&limit=50"
```

#### Notes

- Sorted by timestamp (newest first)
- Includes `location` field ("recent", "buffer", or "longterm")
- Maximum limit: 100 items per page

---

### PUT /admin/memory/{npc_id}/{memory_id}

**Update a specific memory**

Updates the content and/or metadata of an existing memory.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC
- `memory_id` (string, required) - Unique identifier for the memory

**Request Body:**
```json
{
  "content": "Updated memory content (required)",
  "metadata": {
    "new_key": "new_value"
  }
}
```

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Memory updated successfully",
  "npc_id": "blacksmith_001",
  "memory_id": "mem_abc123",
  "updated_in": "recent"
}
```

#### Example Request

```bash
curl -X PUT "http://localhost:8000/admin/memory/blacksmith_001/mem_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated: The player asked about legendary swords.",
    "metadata": {
      "category": "quest_inquiry",
      "priority": "high"
    }
  }'
```

#### Notes

- Searches all storage locations (recent, buffer, longterm)
- Updates in-place (preserves timestamp and ID)
- Returns 404 if memory not found

---

### DELETE /admin/memory/{npc_id}/{memory_id}

**Delete a specific memory**

Removes a single memory from any storage location.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC
- `memory_id` (string, required) - Unique identifier for the memory

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Memory deleted successfully",
  "npc_id": "blacksmith_001",
  "memory_id": "mem_abc123",
  "deleted_from": "longterm"
}
```

#### Example Request

```bash
curl -X DELETE "http://localhost:8000/admin/memory/blacksmith_001/mem_abc123"
```

#### Notes

- Searches all storage locations
- Irreversible operation
- Returns 404 if memory not found

---

### POST /admin/npc/{npc_id}/embed-now

**Force immediate embedding of buffer**

Manually triggers embedding of the NPC's buffer to ChromaDB, regardless of threshold.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Embedded 7 memories to ChromaDB",
  "npc_id": "blacksmith_001",
  "embedded_count": 7
}
```

#### Example Request

```bash
curl -X POST "http://localhost:8000/admin/npc/blacksmith_001/embed-now"
```

#### Notes

- Useful for testing or forcing immediate persistence
- Clears buffer after embedding
- Returns 0 if buffer is empty

---

### DELETE /admin/npc/{npc_id}/clear

**Clear all memories for an NPC (admin version)**

Same as `DELETE /memory/{npc_id}` but returns more detailed breakdown.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Cleared all memories for NPC blacksmith_001",
  "npc_id": "blacksmith_001",
  "recent_deleted": 5,
  "buffer_deleted": 7,
  "longterm_deleted": 43,
  "total_deleted": 55
}
```

#### Example Request

```bash
curl -X DELETE "http://localhost:8000/admin/npc/blacksmith_001/clear"
```

---

### POST /admin/import

**Bulk import memories**

Imports multiple memories for one or more NPCs in a single request.

#### Request Body

```json
{
  "memories": [
    {
      "npc_id": "blacksmith_001",
      "content": "Memory content here",
      "metadata": {
        "source": "import"
      },
      "timestamp": "2025-11-17T10:00:00"
    },
    {
      "npc_id": "merchant_002",
      "content": "Another memory",
      "metadata": {},
      "timestamp": "2025-11-17T11:00:00"
    }
  ]
}
```

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Imported 2 of 2 memories",
  "imported_count": 2,
  "failed_count": 0,
  "failed_memories": []
}
```

#### Response (Partial Failure)

```json
{
  "status": "partial",
  "message": "Imported 1 of 2 memories (1 failed)",
  "imported_count": 1,
  "failed_count": 1,
  "failed_memories": [
    {
      "npc_id": "invalid_npc",
      "content": "This one failed",
      "error": "Content cannot be empty"
    }
  ]
}
```

#### Example Request

```bash
curl -X POST "http://localhost:8000/admin/import" \
  -H "Content-Type: application/json" \
  -d '{
    "memories": [
      {
        "npc_id": "blacksmith_001",
        "content": "I was trained by a master smith.",
        "metadata": {"type": "backstory"}
      },
      {
        "npc_id": "blacksmith_001",
        "content": "I prefer working with steel.",
        "metadata": {"type": "preference"}
      }
    ]
  }'
```

#### Notes

- Timestamp is optional (defaults to current time)
- All memories are added to recent queue (may trigger evictions)
- Partial failures return details of failed imports

---

### GET /admin/export/{npc_id}

**Export all memories for an NPC**

Returns all memories in a format ready for import.

#### Parameters

**Path Parameters:**
- `npc_id` (string, required) - Unique identifier for the NPC

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Exported 55 memories",
  "npc_id": "blacksmith_001",
  "memories": [
    {
      "npc_id": "blacksmith_001",
      "content": "Memory content",
      "timestamp": "2025-11-17T10:00:00.000000",
      "metadata": {},
      "location": "recent"
    }
  ],
  "total": 55,
  "exported_at": "2025-11-17T12:00:00.123456"
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/admin/export/blacksmith_001" > backup.json
```

#### Notes

- Includes all storage locations (recent, buffer, longterm)
- Output format compatible with bulk import
- Includes `exported_at` timestamp

---

### GET /admin/health

**System health check**

Returns the operational status of all system components.

#### Response (200 OK)

```json
{
  "status": "healthy",
  "message": "All systems operational",
  "embedding_service": "loaded",
  "chromadb": "connected",
  "recent_memory": "operational",
  "longterm_memory": "operational"
}
```

#### Response (Degraded)

```json
{
  "status": "degraded",
  "message": "Embedding service not loaded",
  "embedding_service": "not_loaded",
  "chromadb": "connected",
  "recent_memory": "operational",
  "longterm_memory": "operational"
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/admin/health"
```

#### Component Status Values

| Component | Healthy | Unhealthy |
|-----------|---------|-----------|
| `embedding_service` | "loaded" | "not_loaded" |
| `chromadb` | "connected" | "disconnected" |
| `recent_memory` | "operational" | "error" |
| `longterm_memory` | "operational" | "error" |

---

## Data Models

### MemoryEntry

Core memory data structure.

```typescript
{
  id: string;          // Format: "mem_" + 12 random hex chars
  content: string;     // Memory text content
  timestamp: string;   // ISO 8601 format
  metadata: object;    // Optional key-value pairs
}
```

### AddMemoryRequest

```typescript
{
  content: string;     // Required, non-empty
  metadata?: object;   // Optional
}
```

### SearchMemoryRequest

```typescript
{
  query: string;       // Required, search query
  top_k?: number;      // Optional, default 3, max 50
}
```

### UpdateMemoryRequest

```typescript
{
  content: string;     // Required, new content
  metadata?: object;   // Optional, replaces existing metadata
}
```

### BulkImportRequest

```typescript
{
  memories: Array<{
    npc_id: string;
    content: string;
    metadata?: object;
    timestamp?: string;  // ISO 8601, optional
  }>
}
```

---

## Rate Limiting

**Current Version**: No rate limiting

**Production Recommendation**: Implement rate limiting to prevent abuse:

```python
# Recommended limits
- 100 requests/minute per IP for memory endpoints
- 20 requests/minute per IP for admin endpoints
- 10 requests/second global for embedding operations
```

---

## Pagination Best Practices

When using `/admin/npc/{npc_id}/memories`:

1. Start with `page=1, limit=20` for responsive UIs
2. Use `limit=100` for bulk operations
3. Check `total` field to calculate total pages
4. Memories are sorted newest first

Example pagination logic:

```python
page = 1
limit = 50
total_pages = (total + limit - 1) // limit  # Ceiling division

while page <= total_pages:
    response = get_memories(npc_id, page=page, limit=limit)
    process_memories(response["memories"])
    page += 1
```

---

## Performance Characteristics

| Endpoint | Avg Response Time | Notes |
|----------|-------------------|-------|
| `POST /memory/{npc_id}` | < 100ms | Add memory |
| `GET /memory/{npc_id}` | < 50ms | Get recent |
| `GET /memory/{npc_id}/search` | < 150ms | Semantic search (CUDA) |
| `GET /memory/{npc_id}/context` | < 200ms | Recent + search |
| `DELETE /memory/{npc_id}` | < 100ms | Clear all |
| Admin endpoints | < 200ms | Various operations |

**Note**: First embedding may take up to 5 seconds (model loading). Subsequent embeddings are < 30ms.

---

## WebSocket Support

**Current Version**: Not available

**Future Feature**: Real-time memory updates via WebSocket for live monitoring dashboards.

---

## Versioning

**Current Version**: 1.0.0
**API Versioning**: Not yet implemented

Future versions will use path-based versioning:
- `/v1/memory/{npc_id}`
- `/v2/memory/{npc_id}`

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Support

For issues, questions, or contributions:

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines
- **Examples**: See [examples/](../examples/) for usage examples

---

**Last Updated**: 2025-11-17
**API Version**: 1.0.0
**System Status**: Production Ready

# NPC Dynamic Memory System

A FastAPI-based backend system for managing NPC memories in game environments, featuring hierarchical memory architecture with recent (working) memory and long-term semantic memory.

## Features

- **Recent Memory**: Fast FIFO queue for last 5 memories per NPC
- **Long-term Memory**: Vector database with semantic search using ChromaDB
- **Local Embeddings**: sentence-transformers for privacy and low latency
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Admin Tools**: Developer endpoints for memory management

## Architecture

```
Recent Memory (FIFO)  →  Buffer (10 items)  →  Vector DB (ChromaDB)
     ↓ Query                                        ↓ Semantic Search
     └──────────────── Combined Context ────────────┘
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the server
uvicorn main:app --reload
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Comprehensive Documentation**:
- [API Reference](docs/API.md) - All 14 endpoints documented
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and internals
- [Development Guide](docs/DEVELOPMENT.md) - Setup, testing, contributing

## Examples

Check the [examples/](examples/) directory for:
- [add_memories.py](examples/add_memories.py) - Adding memories and FIFO eviction
- [search_memories.py](examples/search_memories.py) - Semantic search examples
- [bulk_import.json](examples/bulk_import.json) - Sample data (35 memories for 5 NPCs)

```bash
# Run examples (server must be running)
python examples/add_memories.py
python examples/search_memories.py
```

## Testing

Run comprehensive tests:
```bash
python tests/test_full_system.py    # All 14 endpoints (17 tests)
python tests/test_persistence.py    # Data persistence validation
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed testing guide.

## Project Status

✅ **Production Ready** - All phases complete, fully tested (100%)

## Tech Stack

- **FastAPI**: Web framework
- **ChromaDB**: Vector database
- **sentence-transformers**: Local embedding generation
- **Pydantic**: Data validation
- **Python 3.10+**: Required

## License

[To be determined]

# NPC Dynamic Memory System - Development Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-17

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Contributing](#contributing)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Git**: For version control
- **pip**: Python package manager
- **venv**: Python virtual environment (included with Python 3.3+)

### Optional (for GPU acceleration)

- **CUDA**: For NVIDIA GPU support (embedding acceleration)
- **MPS**: For Apple Silicon GPU support (automatic on macOS)

---

## Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd npc-dynamic-memory-system
```

### 2. Create Virtual Environment

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements include**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `pydantic-settings` - Configuration management
- `sentence-transformers` - Embedding model
- `chromadb` - Vector database
- `torch` - PyTorch (for embeddings)
- `python-dotenv` - Environment variables

### 4. Configure Environment

```bash
cp .env.example .env
```

**Edit `.env` with your settings**:

```env
# Memory Configuration
RECENT_MEMORY_SIZE=5
LONG_TERM_BUFFER_SIZE=10
SIMILARITY_SEARCH_RESULTS=3

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=auto  # auto, cpu, cuda, or mps
PRELOAD_ON_STARTUP=true
MAX_BATCH_SIZE=50

# Storage Configuration
CHROMA_PERSIST_DIR=./data/chroma_db
BUFFER_DIR=./data/buffers

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 5. Initialize Data Directories

```bash
mkdir -p data/chroma_db data/buffers
```

### 6. Start Development Server

```bash
python main.py
```

Or with hot-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Server will start on**: http://localhost:8000

**API Documentation**: http://localhost:8000/docs

---

## Project Structure

```
npc-dynamic-memory-system/
├── api/
│   ├── __init__.py
│   ├── memory.py           # Memory endpoints (5 routes)
│   └── admin.py            # Admin endpoints (9 routes)
├── models/
│   ├── __init__.py
│   ├── memory.py           # Core data models
│   ├── requests.py         # Request schemas
│   ├── responses.py        # Response schemas
│   └── admin.py            # Admin models
├── services/
│   ├── __init__.py
│   ├── recent_memory.py    # FIFO queue service
│   ├── longterm_memory.py  # Buffer + ChromaDB service
│   └── memory_manager.py   # Orchestration layer
├── utils/
│   ├── __init__.py
│   └── embeddings.py       # Embedding service (singleton)
├── data/                   # Runtime data (gitignored)
│   ├── recent_memory.json  # Recent memory backup
│   ├── buffers/            # Per-NPC buffer files
│   └── chroma_db/          # ChromaDB persistent storage
├── docs/
│   ├── API.md                    # API reference
│   ├── ARCHITECTURE.md           # System architecture
│   ├── DEVELOPMENT.md            # This file
│   ├── WINDOWS_SETUP.md          # Windows-specific setup
│   ├── WINDOWS_COMPATIBILITY.md  # Windows compatibility guide
│   ├── reports/                  # Test execution reports
│   │   └── TEST_EXECUTION_REPORT_2025-11-17.md
│   └── historical/               # Historical documentation
│       └── CORE_SYSTEM_REVIEW_2025-11-16.md
├── examples/
│   ├── add_memories.py     # Example usage
│   ├── search_memories.py  # Example search
│   └── bulk_import.json    # Sample data
├── tests/
│   ├── test_core_system.py     # Core functionality tests
│   ├── test_admin_fixes.py     # Admin operations tests
│   ├── test_full_system.py     # End-to-end tests
│   ├── test_persistence.py     # Manual persistence test
│   └── test_persistence_auto.py # Automated persistence test
├── main.py                 # FastAPI application entry point
├── config.py               # Pydantic settings configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git line ending config
└── README.md               # Project overview
```

### Key Directories

- **`api/`**: FastAPI route handlers (controllers)
- **`models/`**: Pydantic data models (schemas)
- **`services/`**: Business logic (service layer)
- **`utils/`**: Shared utilities (embedding service)
- **`data/`**: Runtime storage (not version controlled)
- **`docs/`**: Documentation files
- **`examples/`**: Usage examples and sample data

---

## Development Workflow

### 1. Feature Development

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Run tests
python tests/test_full_system.py

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to remote
git push origin feature/your-feature-name
```

### 2. Running the Server

**Development Mode** (with auto-reload):
```bash
uvicorn main:app --reload --log-level debug
```

**Production Mode**:
```bash
python main.py
```

**Background Mode** (Linux/macOS):
```bash
nohup python main.py > server.log 2>&1 &
```

### 3. Testing Changes

**Manual API Testing** (using curl):
```bash
# Health check
curl http://localhost:8000/admin/health

# Add memory
curl -X POST http://localhost:8000/memory/test_npc \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory"}'

# Get recent memories
curl http://localhost:8000/memory/test_npc
```

**Interactive API Docs**:
- Visit http://localhost:8000/docs
- Use Swagger UI to test endpoints

### 4. Code Quality

**Run type checking** (if using mypy):
```bash
mypy api/ services/ models/ utils/
```

**Format code** (if using black):
```bash
black api/ services/ models/ utils/
```

**Lint code** (if using ruff):
```bash
ruff check api/ services/ models/ utils/
```

---

## Testing

### Test Suites

#### 1. Full System End-to-End Tests

**File**: `tests/test_full_system.py`

**Coverage**:
- All 14 API endpoints (5 memory + 9 admin)
- FIFO eviction workflow
- Buffer auto-embed workflow
- Semantic search workflow

**Prerequisites**:
- Server must be running on http://localhost:8000
- Fresh state (no leftover test data)

**Run**:
```bash
# Terminal 1: Start server
python main.py

# Terminal 2: Run tests
python tests/test_full_system.py
```

**Expected Output**:
```
============================================================
COMPREHENSIVE SYSTEM TEST
============================================================
All 17/17 tests passed ✅
Production Readiness: 100/100
```

#### 2. Persistence Tests

**Manual Test** (`tests/test_persistence.py`):
```bash
# Requires manual server restart
python tests/test_persistence.py
# Follow on-screen instructions
```

**Automated Test** (`tests/test_persistence_auto.py`):
```bash
# Requires manual server restart between steps
python tests/test_persistence_auto.py
# Press ENTER after restarting server
```

### Writing New Tests

**Template for API endpoint test**:

```python
import requests

BASE_URL = "http://localhost:8000"

def test_your_endpoint():
    # Setup
    npc_id = "test_npc_123"

    # Execute
    response = requests.post(
        f"{BASE_URL}/memory/{npc_id}",
        json={"content": "Test content"},
        timeout=10
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "memory_id" in data

    # Cleanup
    requests.delete(f"{BASE_URL}/memory/{npc_id}", timeout=10)

    print("✅ Test passed: Your endpoint")

if __name__ == "__main__":
    test_your_endpoint()
```

---

## Code Style

### Python Style Guidelines

**Follow PEP 8** with these specifics:

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized (stdlib, third-party, local)
- **Docstrings**: Google style

### Example Code

```python
"""
Module docstring: Brief description.

More details about this module.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models.memory import MemoryEntry
from services.memory_manager import MemoryManager


logger = logging.getLogger(__name__)


class MyModel(BaseModel):
    """Brief description of MyModel.

    Attributes:
        field_one: Description of field_one.
        field_two: Description of field_two.
    """
    field_one: str
    field_two: int


def my_function(param: str, optional_param: Optional[int] = None) -> Dict[str, Any]:
    """Brief description of function.

    Args:
        param: Description of param.
        optional_param: Description of optional_param (default: None).

    Returns:
        Dictionary containing result data.

    Raises:
        ValueError: If param is empty.
    """
    if not param:
        raise ValueError("param cannot be empty")

    result = {
        "status": "success",
        "data": param,
        "count": optional_param or 0
    }

    logger.info(f"Function completed: {param}")
    return result
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | `snake_case` | `memory_count` |
| Functions | `snake_case` | `get_recent_memories()` |
| Classes | `PascalCase` | `MemoryManager` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_BUFFER_SIZE` |
| Private | `_leading_underscore` | `_internal_method()` |
| Files | `snake_case.py` | `memory_manager.py` |

### Logging

**Use structured logging**:

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(f"Added memory {memory_id} for NPC {npc_id}")
logger.warning(f"Buffer nearly full: {count}/{threshold} items")
logger.error(f"Failed to embed memories: {str(e)}", exc_info=True)

# Avoid
print("Debug message")  # Use logger.debug() instead
logger.info("Success")  # Too vague, add details
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic info (verbose)
- `INFO`: Normal operations (memory added, search completed)
- `WARNING`: Unexpected but recoverable (buffer near full, slow query)
- `ERROR`: Errors that prevent operation (embedding failed, DB error)
- `CRITICAL`: System failure (server crash, data corruption)

---

## Contributing

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: Ensure all tests pass
5. **Commit**: Use conventional commits (see below)
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Conventional Commits

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat(api): add memory tagging endpoint"
git commit -m "fix(embeddings): resolve CUDA device detection bug"
git commit -m "docs: update API.md with new endpoint"
git commit -m "refactor(services): simplify buffer management logic"
git commit -m "test: add integration tests for search endpoint"
```

### Pull Request Guidelines

**PR Title**: Use conventional commit format

**PR Description** should include:
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors

**Symptom**:
```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue 2: Embedding Model Not Loading

**Symptom**:
```
EmbeddingService not loaded
Health check shows "not_loaded"
```

**Solution**:
```bash
# Check .env configuration
PRELOAD_ON_STARTUP=true
EMBEDDING_DEVICE=auto  # or cpu, cuda, mps

# Check CUDA availability (if using GPU)
python -c "import torch; print(torch.cuda.is_available())"

# Force CPU mode
EMBEDDING_DEVICE=cpu python main.py
```

#### Issue 3: ChromaDB Permission Errors

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: './data/chroma_db'
```

**Solution**:
```bash
# Create directory with correct permissions
mkdir -p data/chroma_db
chmod 755 data/chroma_db

# Or delete and recreate
rm -rf data/chroma_db
mkdir -p data/chroma_db
```

#### Issue 4: Port Already in Use

**Symptom**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port
PORT=8001 python main.py
```

#### Issue 5: Tests Failing

**Symptom**:
```
Connection refused (server not running)
```

**Solution**:
```bash
# Ensure server is running
python main.py

# In another terminal, run tests
python tests/test_full_system.py

# Check server health
curl http://localhost:8000/admin/health
```

#### Issue 6: Slow First Request

**Symptom**: First API request takes 5+ seconds

**Cause**: Embedding model loading on first use

**Solution**:
```bash
# Enable preload in .env
PRELOAD_ON_STARTUP=true

# Restart server
python main.py

# Verify preload in logs
# Should see: "Embedding model preloaded and ready"
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `RECENT_MEMORY_SIZE` | 5 | Max items in recent queue |
| `LONG_TERM_BUFFER_SIZE` | 10 | Buffer threshold for auto-embed |
| `SIMILARITY_SEARCH_RESULTS` | 3 | Default search results |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence transformer model |
| `EMBEDDING_DEVICE` | auto | Device: auto, cpu, cuda, mps |
| `PRELOAD_ON_STARTUP` | true | Preload embedding model |
| `MAX_BATCH_SIZE` | 50 | Max batch size for embeddings |
| `CHROMA_PERSIST_DIR` | ./data/chroma_db | ChromaDB storage path |
| `BUFFER_DIR` | ./data/buffers | Buffer files directory |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `LOG_LEVEL` | INFO | Logging level |

---

## Debugging Tips

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG

# Or at runtime
LOG_LEVEL=DEBUG python main.py
```

### Inspect Data Files

**Recent memory backup**:
```bash
cat data/recent_memory.json | python -m json.tool
```

**Buffer for specific NPC**:
```bash
cat data/buffers/blacksmith_001.json | python -m json.tool
```

**ChromaDB collections**:
```python
import chromadb
client = chromadb.PersistentClient(path="./data/chroma_db")
collections = client.list_collections()
print([c.name for c in collections])
```

### Monitor Server Logs

**Tail logs in real-time**:
```bash
tail -f server.log  # If running in background
```

**Filter for errors**:
```bash
grep -i error server.log
```

### Profile Performance

**Time API requests**:
```bash
time curl http://localhost:8000/memory/test_npc/search?query=test
```

**Python profiling** (add to code):
```python
import cProfile
import pstats

with cProfile.Profile() as pr:
    # Your code here
    result = expensive_function()

stats = pstats.Stats(pr)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 slowest functions
```

---

## Development Resources

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

### Useful Commands

**Check Python version**:
```bash
python --version
```

**List installed packages**:
```bash
pip list
```

**Generate requirements.txt**:
```bash
pip freeze > requirements.txt
```

**Check disk usage**:
```bash
du -sh data/*
```

**Count lines of code**:
```bash
find . -name '*.py' -not -path './venv/*' | xargs wc -l
```

---

## Release Process

### Version Bumping

1. Update version in `main.py`
2. Update version in all `docs/*.md` files
3. Update `CHANGELOG.md` (if present)
4. Commit: `git commit -m "chore: bump version to X.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. Push: `git push && git push --tags`

### Pre-Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No TODO comments in code
- [ ] Requirements.txt up to date
- [ ] .env.example matches config.py

---

## Getting Help

### Internal Resources

- **Documentation**: See [docs/](../docs/) directory
- **Examples**: See [examples/](../examples/) directory
- **Tests**: See test files for usage patterns

### External Resources

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions in GitHub Discussions
- **Stack Overflow**: Tag questions with relevant frameworks

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
**Maintainers**: See [CONTRIBUTORS.md](../CONTRIBUTORS.md)

# Windows Setup Guide

## Prerequisites

### 1. Python Installation

**Option A: Microsoft Store (Recommended for Windows 11)**
```powershell
# Search "Python 3.12" in Microsoft Store and install
# Automatically adds Python to PATH
```

**Option B: python.org**
- Download from https://www.python.org/downloads/
- ✅ **IMPORTANT**: Check "Add Python to PATH" during installation

Verify installation:
```powershell
python --version
# Should output: Python 3.10.x or higher
```

### 2. Git (Optional but recommended)
- Download from https://git-scm.com/download/win
- Use default settings (Git Bash + Git from command line)

## Installation

### 1. Clone/Download Project
```powershell
# If using Git:
git clone <repository-url>
cd npc-memory-system

# Or download ZIP and extract
```

### 2. Create Virtual Environment (Recommended)
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# You should see (venv) in your prompt
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

**First-time installation notes:**
- PyTorch may take 5-10 minutes (large download)
- sentence-transformers will download ~90MB model on first use
- ChromaDB installs sqlite dependencies automatically

### 4. Configure Environment
```powershell
# Copy example configuration
copy .env.example .env

# Edit .env in Notepad or your preferred editor
notepad .env
```

## GPU Acceleration (Optional)

### If you have an NVIDIA GPU:

1. **Check GPU compatibility**:
```powershell
nvidia-smi
# Should show your GPU details
```

2. **Install CUDA Toolkit** (if not already installed):
- Download from https://developer.nvidia.com/cuda-downloads
- Version 11.8 or 12.1 recommended
- Requires ~3GB disk space

3. **Update .env**:
```
EMBEDDING_DEVICE=cuda
```

### If no GPU or non-NVIDIA:
```
EMBEDDING_DEVICE=cpu
```
Performance is still good for NPC use case (<50ms per embedding).

## Running the Application

### Development Server
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Run the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: http://localhost:8000

API docs at: http://localhost:8000/docs

### Run Tests
```powershell
python test_recent_memory.py
```

## Common Issues

### Issue: "python: command not found"
**Solution**: Python not in PATH
```powershell
# Use full path:
C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe --version

# Or reinstall Python and check "Add to PATH"
```

### Issue: "No module named 'pydantic'"
**Solution**: Dependencies not installed
```powershell
# Make sure venv is activated
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Issue: ChromaDB errors about sqlite
**Solution**: Python version issue
- ChromaDB requires Python 3.10+
- Check: `python --version`
- If < 3.10, update Python

### Issue: Slow embedding (no GPU)
**Solution**: Expected behavior on CPU
- CPU embedding: ~50-100ms per memory
- GPU (CUDA): ~20-30ms per memory
- Both are acceptable for NPC interactions

## File Paths on Windows

The system automatically handles Windows paths:
- Config uses forward slashes: `./data/chroma_db`
- Python converts to: `.\data\chroma_db` on Windows
- No manual changes needed

**Spaces in paths work fine:**
```
C:\Users\Your Name\Documents\npc-memory-system\
```

## Development Workflow

### 1. Daily Start
```powershell
cd path\to\npc-memory-system
.\venv\Scripts\activate
python -m uvicorn main:app --reload
```

### 2. Code Changes
- Edit files in VSCode, PyCharm, or any editor
- Server auto-reloads (--reload flag)
- Test at http://localhost:8000/docs

### 3. Git Workflow
```powershell
git status
git add .
git commit -m "Your message"
git push
```

**Note**: Line endings are auto-converted to LF (Unix style) by Git.
This ensures consistency with WSL teammates.

## Docker Alternative (Advanced)

If you have Docker Desktop on Windows:

```powershell
# Build image
docker build -t npc-memory-system .

# Run container
docker run -p 8000:8000 npc-memory-system
```

Eliminates all dependency/environment issues.

## Performance Tips

1. **Use SSD**: ChromaDB performs better on SSD vs HDD
2. **Antivirus**: Add project folder to exclusions (faster file I/O)
3. **RAM**: 8GB minimum, 16GB recommended (model uses ~300MB)

## Questions?

- Check main README.md for architecture
- See docs/API.md for endpoint documentation
- File issues on GitHub

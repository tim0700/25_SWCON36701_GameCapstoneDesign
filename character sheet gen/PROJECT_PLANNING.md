# Character Sheet Generator - Project Planning Document

## 1. Windows Compatibility Requirements

### 1.1 Critical Windows Considerations

#### Path Handling
- **Use `pathlib.Path`** for all file operations (cross-platform compatible)
- Avoid hardcoded forward slashes or backslashes
- Use `Path.joinpath()` or `/` operator for path construction
- Use `.resolve()` for absolute paths

```python
# ✅ Good (Windows compatible)
from pathlib import Path
template_path = Path("templates") / "system_prompt.txt"
output_path = Path("data") / "npcs" / f"{character_id}.json"

# ❌ Bad (Unix-specific)
template_path = "templates/system_prompt.txt"
```

#### Environment Variables
- Use `python-dotenv` for `.env` file management
- Windows environment variables set via System Properties or `.env` file
- Service account path: use absolute paths or relative to project root

```python
# Windows-compatible environment variable loading
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file automatically

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# Can be: C:\Users\username\project\service-account.json
```

#### Line Endings
- Configure Git to handle line endings automatically
- Create `.gitattributes` file:
```
* text=auto
*.py text eol=lf
*.json text eol=lf
*.txt text eol=lf
*.md text eol=lf
```

#### Virtual Environment
```bash
# Windows command prompt
python -m venv venv
venv\Scripts\activate

# Windows PowerShell
python -m venv venv
venv\Scripts\Activate.ps1

# May need to enable script execution:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Development Server
- Uvicorn works identically on Windows
- No changes needed for FastAPI server
- Use `uvicorn.run()` programmatically or CLI

---

## 2. Module Architecture Design

### 2.1 Core Modules Overview

```
character_sheet_generator/
│
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── character.py      # Character generation endpoints
│   │   ├── dependencies.py       # FastAPI dependencies (auth, etc.)
│   │   └── middleware.py         # Custom middleware
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── template_manager.py   # Template loading and caching
│   │   ├── vertex_client.py      # Vertex AI integration
│   │   ├── prompt_builder.py     # Dynamic prompt assembly
│   │   ├── validator.py          # Secondary validation logic
│   │   └── storage_service.py    # File storage operations
│   │
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── schemas.py            # Pydantic models (API)
│   │   └── character_sheet.py    # Character sheet domain model
│   │
│   ├── core/                     # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── logger.py             # Logging configuration
│   │   └── utils.py              # Utility functions
│   │
│   └── templates/                # Prompt templates
│       ├── system_prompt.txt
│       └── character_sheet_schema.json
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── test_template_manager.py
│   │   ├── test_prompt_builder.py
│   │   ├── test_validator.py
│   │   └── test_storage_service.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   └── test_vertex_client.py
│   └── fixtures/
│       └── sample_responses.json
│
├── data/                         # Generated data storage
│   └── npcs/                     # Character sheets
│
├── docs/                         # Documentation
│   ├── api_reference.md
│   └── deployment_guide.md
│
├── scripts/                      # Utility scripts
│   ├── setup_env.py              # Environment setup helper
│   └── validate_templates.py    # Template validation
│
├── .env.example                  # Environment variable template
├── .gitignore
├── .gitattributes                # Line ending configuration
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml                # Python project configuration
├── README.md
└── TECHNICAL_REFERENCE.md
```

### 2.2 Module Responsibilities

#### `app/main.py` - Application Entry Point
**Responsibility**: Initialize FastAPI app, configure middleware, register routes
```python
from fastapi import FastAPI
from app.api.routes import character
from app.core.logger import setup_logging
from app.config import settings

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Character Sheet Generator",
        version="1.0.0",
        description="AI-powered NPC character sheet generator"
    )

    # Register routers
    app.include_router(character.router, prefix="/api/v1", tags=["characters"])

    return app

app = create_app()
```

#### `app/config.py` - Configuration Management
**Responsibility**: Centralized configuration using Pydantic BaseSettings
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Google Cloud
    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    google_application_credentials: Path | None = None

    # Model settings
    gemini_model: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_output_tokens: int = 8192

    # Paths (Windows compatible)
    templates_dir: Path = Path("app/templates")
    output_dir: Path = Path("data/npcs")

    # API settings
    api_timeout: int = 60
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

#### `app/services/template_manager.py` - Template Management
**Responsibility**: Load, cache, and provide access to templates
```python
from pathlib import Path
from typing import Dict, Any
import json
from functools import lru_cache

class TemplateManager:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    @lru_cache(maxsize=1)
    def load_system_prompt(self) -> str:
        """Load and cache system prompt"""
        prompt_path = self.templates_dir / "system_prompt.txt"
        return prompt_path.read_text(encoding="utf-8")

    @lru_cache(maxsize=1)
    def load_character_schema(self) -> Dict[str, Any]:
        """Load and cache character sheet schema"""
        schema_path = self.templates_dir / "character_sheet_schema.json"
        with schema_path.open(encoding="utf-8") as f:
            return json.load(f)

    def reload_templates(self):
        """Clear cache and reload templates"""
        self.load_system_prompt.cache_clear()
        self.load_character_schema.cache_clear()
```

#### `app/services/vertex_client.py` - Vertex AI Integration
**Responsibility**: Manage Vertex AI connections and API calls
```python
from vertexai.generative_models import GenerativeModel
import vertexai
from app.config import settings
from app.core.exceptions import LLMGenerationError

class VertexAIClient:
    def __init__(self):
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location
        )
        self.model = GenerativeModel(settings.gemini_model)

    async def generate_character_sheet(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate character sheet using Gemini API"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": settings.temperature,
                    "max_output_tokens": settings.max_output_tokens
                }
            )
            return json.loads(response.text)
        except Exception as e:
            raise LLMGenerationError(f"Failed to generate: {str(e)}")
```

#### `app/services/prompt_builder.py` - Prompt Assembly
**Responsibility**: Construct prompts from templates and user input
```python
class PromptBuilder:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager

    def build_character_prompt(
        self,
        character_id: str,
        seed_description: str
    ) -> str:
        """Assemble final prompt for character generation"""
        system_prompt = self.template_manager.load_system_prompt()

        return f"""{system_prompt}

Generate an NPC character sheet JSON that fully complies with the 'Output Schema'
based on the 'Seed Information' below.

<Seed Information>
- ID: {character_id}
- Description: {seed_description}
</Seed Information>

Ensure all required fields are filled with creative, coherent, and internally
consistent content that brings this character to life."""
```

#### `app/services/storage_service.py` - File Storage
**Responsibility**: Save and retrieve character sheets (Windows compatible)
```python
from pathlib import Path
import json
from datetime import datetime
from app.core.exceptions import StorageError

class StorageService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_character_sheet(
        self,
        character_id: str,
        data: Dict[str, Any]
    ) -> Path:
        """Save character sheet to JSON file"""
        try:
            # Windows-safe filename
            safe_id = self._sanitize_filename(character_id)
            file_path = self.output_dir / f"{safe_id}.json"

            # Add metadata
            data["_metadata"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "version": "2.2"
            }

            # Write with proper encoding
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return file_path
        except Exception as e:
            raise StorageError(f"Failed to save: {str(e)}")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove Windows-invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename
```

#### `app/services/validator.py` - Business Logic Validation
**Responsibility**: Secondary validation beyond Pydantic schema
```python
from app.models.character_sheet import CharacterSheet
from app.core.exceptions import ValidationError

class CharacterValidator:
    @staticmethod
    def validate_character_sheet(sheet: CharacterSheet) -> None:
        """Perform business logic validation"""
        errors = []

        # Check for empty critical fields
        if not sheet.long_term_goal:
            errors.append("Character must have a long-term goal")

        if not sheet.personality_traits:
            errors.append("Character must have personality traits")

        # Check age consistency
        if sheet.age and sheet.age < 0:
            errors.append("Age cannot be negative")

        # Check relationship consistency
        if sheet.relationships:
            for rel in sheet.relationships:
                if not rel.get("character_name"):
                    errors.append("All relationships must have a character name")

        if errors:
            raise ValidationError("; ".join(errors))
```

#### `app/models/schemas.py` - API Request/Response Models
**Responsibility**: Define FastAPI request and response schemas
```python
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

class CharacterRequest(BaseModel):
    """Request model for character generation"""
    character_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the character",
        examples=["npc_wandering_mage_elara"]
    )
    seed_description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Brief description to seed character generation",
        examples=[
            "A wandering mage seeking forgotten knowledge. "
            "Prickly but warm-hearted. Chasing ancient artifact clues."
        ]
    )

class CharacterResponse(BaseModel):
    """Response model for successful character generation"""
    success: bool = True
    character_id: str
    file_path: str
    generated_at: datetime
    message: str = "Character sheet generated successfully"

class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = False
    error_type: str
    error_message: str
    details: dict | None = None
```

#### `app/models/character_sheet.py` - Domain Model
**Responsibility**: Full Pydantic model matching character sheet v2.2 spec
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Relationship(BaseModel):
    character_name: str
    relationship_type: str
    description: str

class CharacterSheet(BaseModel):
    """Complete character sheet model (v2.2)"""
    character_id: str
    name: str
    age: int | None = None
    gender: str | None = None
    occupation: str

    # Background
    background_summary: str
    origin: str

    # Personality
    personality_traits: List[str]
    values: List[str]
    fears: List[str]

    # Goals and motivations
    long_term_goal: str
    short_term_goals: List[str]
    motivations: List[str]

    # Relationships
    relationships: List[Relationship] = []

    # Skills and abilities
    skills: List[str]
    special_abilities: List[str] = []

    # Additional
    notable_possessions: List[str] = []
    secrets: List[str] = []

    # Dialogue
    speech_pattern: str | None = None
    sample_dialogue: List[str] = []

    model_config = {
        "json_schema_extra": {
            "description": "NPC Character Sheet v2.2 for Aetheria World"
        }
    }
```

---

## 3. Configuration Management Strategy

### 3.1 Environment Configuration

#### `.env` File Structure
```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json

# Model Configuration
GEMINI_MODEL=gemini-2.5-flash-lite
TEMPERATURE=0.7
MAX_OUTPUT_TOKENS=8192

# Application Settings
TEMPLATES_DIR=app/templates
OUTPUT_DIR=data/npcs
API_TIMEOUT=60
MAX_RETRIES=3

# Development
DEBUG=true
LOG_LEVEL=INFO
```

#### `.env.example` Template
```env
# Copy this file to .env and fill in your values

# Google Cloud Configuration (REQUIRED)
GOOGLE_CLOUD_PROJECT=your-project-id-here
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Model Configuration (Optional - defaults provided)
GEMINI_MODEL=gemini-2.5-flash-lite
TEMPERATURE=0.7
MAX_OUTPUT_TOKENS=8192

# Application Settings (Optional - defaults provided)
TEMPLATES_DIR=app/templates
OUTPUT_DIR=data/npcs
API_TIMEOUT=60
MAX_RETRIES=3

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### 3.2 Configuration Loading Priority
1. Environment variables (highest priority)
2. `.env` file
3. Default values in `Settings` class

---

## 4. Error Handling Strategy

### 4.1 Custom Exception Hierarchy
```python
# app/core/exceptions.py

class CharacterGeneratorError(Exception):
    """Base exception for all custom errors"""
    pass

class ConfigurationError(CharacterGeneratorError):
    """Configuration or environment setup errors"""
    pass

class TemplateError(CharacterGeneratorError):
    """Template loading or parsing errors"""
    pass

class LLMGenerationError(CharacterGeneratorError):
    """Vertex AI API call failures"""
    pass

class ValidationError(CharacterGeneratorError):
    """Character sheet validation failures"""
    pass

class StorageError(CharacterGeneratorError):
    """File storage operation failures"""
    pass
```

### 4.2 FastAPI Error Handlers
```python
# app/api/middleware.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import *

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "validation_error",
            "error_message": str(exc)
        }
    )

@app.exception_handler(LLMGenerationError)
async def llm_error_handler(request: Request, exc: LLMGenerationError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error_type": "llm_generation_error",
            "error_message": "Failed to generate character sheet",
            "details": {"reason": str(exc)}
        }
    )
```

### 4.3 Logging Strategy
```python
# app/core/logger.py

import logging
from pathlib import Path
from app.config import settings

def setup_logging():
    """Configure application-wide logging"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File handler
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

---

## 5. Data Models and Validation

### 5.1 Validation Layers

**Layer 1: Pydantic Request Validation**
- Validates incoming API requests
- Type checking, length constraints
- Automatic error messages

**Layer 2: Gemini Response Schema**
- Ensures LLM output matches structure
- Prevents malformed JSON
- Enforces required fields

**Layer 3: Pydantic Model Validation**
- Parses LLM output into CharacterSheet model
- Type coercion and validation
- Catches schema mismatches

**Layer 4: Business Logic Validation**
- Custom validation rules
- Content quality checks
- Relationship consistency

### 5.2 Schema Version Management

```python
# Future-proofing for schema updates

class CharacterSheetV2_2(BaseModel):
    """Version 2.2 schema"""
    schema_version: str = "2.2"
    # ... fields ...

class CharacterSheetV2_3(BaseModel):
    """Version 2.3 schema (future)"""
    schema_version: str = "2.3"
    # ... updated fields ...

# Factory pattern for version handling
def get_character_schema(version: str) -> type[BaseModel]:
    schemas = {
        "2.2": CharacterSheetV2_2,
        "2.3": CharacterSheetV2_3,
    }
    return schemas.get(version, CharacterSheetV2_2)
```

---

## 6. Testing Strategy

### 6.1 Test Structure

**Unit Tests** (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies (Vertex AI, file system)
- Fast execution, no network calls

**Integration Tests** (`tests/integration/`)
- Test component interactions
- Use test Vertex AI project or mocks
- Test full API workflow

**Fixture-based Tests** (`tests/fixtures/`)
- Pre-generated sample responses
- Known good/bad character sheets
- Edge cases and error scenarios

### 6.2 Testing Tools

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0  # For TestClient
faker>=19.0.0  # Generate test data
```

### 6.3 Test Examples

```python
# tests/unit/test_template_manager.py

import pytest
from pathlib import Path
from app.services.template_manager import TemplateManager

def test_load_system_prompt(tmp_path):
    """Test system prompt loading"""
    # Create temporary template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    prompt_file = template_dir / "system_prompt.txt"
    prompt_file.write_text("Test prompt")

    # Test loading
    manager = TemplateManager(template_dir)
    prompt = manager.load_system_prompt()

    assert prompt == "Test prompt"

# tests/integration/test_api_endpoints.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_character_success():
    """Test successful character generation"""
    response = client.post(
        "/api/v1/generate-character-sheet",
        json={
            "character_id": "test_character",
            "seed_description": "A brave warrior seeking redemption"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "file_path" in data
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure
- [ ] Configure Windows-compatible paths and environment
- [ ] Implement configuration management (config.py)
- [ ] Set up logging system
- [ ] Define custom exceptions
- [ ] Create basic FastAPI app structure

### Phase 2: Core Services (Week 1-2)
- [ ] Implement TemplateManager
- [ ] Implement PromptBuilder
- [ ] Implement StorageService
- [ ] Create Pydantic models (schemas.py, character_sheet.py)
- [ ] Write unit tests for each service

### Phase 3: Vertex AI Integration (Week 2)
- [ ] Implement VertexAIClient
- [ ] Test authentication (local and service account)
- [ ] Test structured output generation
- [ ] Create mock responses for testing
- [ ] Write integration tests

### Phase 4: API Layer (Week 2-3)
- [ ] Implement character generation endpoint
- [ ] Add error handlers
- [ ] Implement request/response models
- [ ] Add API documentation
- [ ] Write API integration tests

### Phase 5: Validation & Quality (Week 3)
- [ ] Implement CharacterValidator
- [ ] Add business logic validation rules
- [ ] Test validation edge cases
- [ ] Implement retry logic for API failures

### Phase 6: Templates & Configuration (Week 3)
- [ ] Create system_prompt.txt
- [ ] Create character_sheet_schema.json (OpenAPI 3.0)
- [ ] Write template validation script
- [ ] Test template variations

### Phase 7: Testing & Documentation (Week 4)
- [ ] Achieve 80%+ test coverage
- [ ] Write API documentation
- [ ] Create deployment guide
- [ ] Create Windows setup guide
- [ ] Performance testing

### Phase 8: Polish & Deployment Prep (Week 4)
- [ ] Code review and refactoring
- [ ] Security audit (API keys, input validation)
- [ ] Create Docker configuration (optional)
- [ ] Production configuration
- [ ] Monitoring and logging enhancement

---

## 8. Development Environment Setup (Windows)

### 8.1 Prerequisites
```powershell
# Install Python 3.11+
# Download from python.org

# Verify installation
python --version

# Install Git
# Download from git-scm.com
```

### 8.2 Project Setup Steps
```powershell
# Clone or create project directory
mkdir character_sheet_generator
cd character_sheet_generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
copy .env.example .env

# Edit .env with your configuration
notepad .env

# Create necessary directories
mkdir data\npcs
mkdir logs

# Run tests
pytest

# Start development server
uvicorn app.main:app --reload
```

### 8.3 Google Cloud Setup
```powershell
# Install Google Cloud SDK for Windows
# Download from cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Or download service account key
# Store at: C:\path\to\service-account.json
# Update GOOGLE_APPLICATION_CREDENTIALS in .env
```

---

## 9. Key Design Decisions Summary

### 9.1 Architecture Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | FastAPI | Async support, automatic docs, Pydantic integration |
| **Path Handling** | pathlib.Path | Cross-platform compatibility, cleaner API |
| **Config Management** | Pydantic Settings | Type-safe, environment variable support |
| **Template Storage** | File-based | Easy to edit, version control friendly |
| **Character Storage** | JSON files | Human-readable, easy to inspect/debug |
| **Validation** | Multi-layer | Defense in depth, catch errors early |
| **Testing** | Pytest | Rich ecosystem, async support |
| **Logging** | Python logging | Standard library, flexible configuration |

### 9.2 Windows-Specific Adaptations

- All file paths use `pathlib.Path`
- Explicit UTF-8 encoding for all file operations
- Filename sanitization for Windows invalid characters
- Git line ending configuration
- Virtual environment activation scripts
- PowerShell-compatible setup instructions

---

## 10. Next Steps

After reviewing this planning document:

1. **Approval**: Confirm the architecture and module design
2. **Customization**: Identify any specific requirements or modifications
3. **Template Creation**: Define the exact system prompt and character sheet schema
4. **Implementation**: Begin Phase 1 development
5. **Iteration**: Adjust based on testing and feedback

---

**Document Status**: Draft for Review
**Target Platform**: Windows (cross-platform compatible)
**Last Updated**: 2025-11-02

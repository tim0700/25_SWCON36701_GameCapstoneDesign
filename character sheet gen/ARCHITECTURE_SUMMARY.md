# Character Sheet Generator - Architecture Summary

## Quick Reference Guide

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Developer)                          │
│                    (Postman / Web UI / CLI)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ POST /api/v1/generate-character-sheet
                                 │ { character_id, seed_description }
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FASTAPI SERVER                             │
│                        (app/main.py)                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                   │
│                 (app/api/routes/character.py)                       │
│                                                                     │
│  • Request validation (Pydantic)                                    │
│  • Input sanitization                                               │
│  • Route to service layer                                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                                 │
│                     (app/services/*)                                │
└─────────────────────────────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
    ┌───────────────┐    ┌──────────────┐    ┌─────────────┐
    │   Template    │    │   Prompt     │    │  Vertex AI  │
    │   Manager     │───▶│   Builder    │───▶│   Client    │
    │               │    │              │    │             │
    │ • Load prompt │    │ • Assemble   │    │ • API call  │
    │ • Load schema │    │   final      │    │ • Gemini    │
    │ • Cache       │    │   prompt     │    │   2.5       │
    └───────────────┘    └──────────────┘    └──────┬──────┘
                                                     │
                                                     │ Structured JSON
                                                     │
                                                     ▼
                                         ┌─────────────────────┐
                                         │  GEMINI 2.5 FLASH   │
                                         │                     │
                                         │  • Generate JSON    │
                                         │  • Follow schema    │
                                         │  • Return result    │
                                         └──────────┬──────────┘
                                                     │
                                                     │ JSON Response
                                                     │
            ┌────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────┐
    │   Validator     │
    │                 │
    │ • Pydantic      │
    │   parse         │
    │ • Business      │
    │   logic check   │
    └────────┬────────┘
             │
             │ Valid CharacterSheet
             │
             ▼
    ┌─────────────────┐
    │   Storage       │
    │   Service       │
    │                 │
    │ • Save to       │
    │   data/npcs/    │
    │ • Return path   │
    └────────┬────────┘
             │
             │ File path
             │
             ▼
    ┌─────────────────────────────────────┐
    │  Response to Developer               │
    │                                      │
    │  {                                   │
    │    "success": true,                  │
    │    "character_id": "...",            │
    │    "file_path": "data/npcs/...json", │
    │    "generated_at": "..."             │
    │  }                                   │
    └──────────────────────────────────────┘
```

---

## Module Interaction Map

```
app/
│
├── main.py ─────────────────┐
│                            │
├── config.py ◄──────────────┼───────── (Used by all modules)
│                            │
├── api/                     │
│   ├── routes/              │
│   │   └── character.py ◄───┤
│   │            │           │
│   │            └───────────┼──────► services/
│   │                        │              │
│   └── middleware.py ◄──────┤              ├── template_manager.py
│                            │              ├── prompt_builder.py
├── services/                │              ├── vertex_client.py
│   ├── template_manager.py  │              ├── validator.py
│   ├── prompt_builder.py    │              └── storage_service.py
│   ├── vertex_client.py     │                       │
│   ├── validator.py          │                       │
│   └── storage_service.py    │                       │
│            │                │                       │
│            └────────────────┼───────► data/npcs/   │
│                             │                       │
├── models/                   │                       │
│   ├── schemas.py ◄──────────┼───────────────────────┤
│   └── character_sheet.py ◄──┤                       │
│                             │                       │
├── core/                     │                       │
│   ├── exceptions.py ◄───────┼───────────────────────┘
│   ├── logger.py ◄───────────┤
│   └── utils.py ◄────────────┘
│
└── templates/
    ├── system_prompt.txt ◄─── (Loaded by template_manager)
    └── character_sheet_schema.json
```

---

## Data Flow (Step by Step)

### 1️⃣ Request Input
```json
POST /api/v1/generate-character-sheet
{
  "character_id": "npc_wandering_mage_elara",
  "seed_description": "A wandering mage seeking forgotten knowledge..."
}
```
**Validation**: Pydantic `CharacterRequest` model

---

### 2️⃣ Template Loading
```python
TemplateManager.load_system_prompt()
→ "You are a professional scenario writer for Aetheria..."

TemplateManager.load_character_schema()
→ { "type": "object", "properties": {...} }
```
**Caching**: LRU cache prevents repeated file reads

---

### 3️⃣ Prompt Assembly
```python
PromptBuilder.build_character_prompt()
→ Combined prompt with system instructions + seed info
```

---

### 4️⃣ Vertex AI Call
```python
VertexAIClient.generate_character_sheet(
    prompt=assembled_prompt,
    schema=character_schema
)
→ Gemini 2.5 Flash generates structured JSON
```
**Parameters**:
- `response_mime_type`: "application/json"
- `response_schema`: OpenAPI 3.0 schema
- `temperature`: 0.7
- `max_output_tokens`: 8192

---

### 5️⃣ Validation
```python
# Layer 1: Pydantic parsing
CharacterSheet.model_validate_json(response.text)

# Layer 2: Business logic
CharacterValidator.validate_character_sheet(sheet)
```
**Checks**:
- Required fields present
- Age > 0
- No empty critical fields
- Relationship consistency

---

### 6️⃣ Storage
```python
StorageService.save_character_sheet(character_id, data)
→ data/npcs/npc_wandering_mage_elara.json
```
**Features**:
- Windows-safe filename sanitization
- UTF-8 encoding
- Metadata injection (timestamp, version)

---

### 7️⃣ Response
```json
{
  "success": true,
  "character_id": "npc_wandering_mage_elara",
  "file_path": "data/npcs/npc_wandering_mage_elara.json",
  "generated_at": "2025-11-02T12:34:56.789Z",
  "message": "Character sheet generated successfully"
}
```

---

## Key Design Patterns

### 1. **Dependency Injection**
```python
# Services receive dependencies via constructor
class PromptBuilder:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager

# Easy to test with mocks
def test_prompt_builder():
    mock_manager = Mock(TemplateManager)
    builder = PromptBuilder(mock_manager)
```

### 2. **Single Responsibility Principle**
Each module has one clear purpose:
- `TemplateManager`: Only manages templates
- `PromptBuilder`: Only builds prompts
- `StorageService`: Only handles file I/O
- `Validator`: Only validates business logic

### 3. **Configuration Centralization**
```python
# Single source of truth
from app.config import settings

# Used everywhere
model = GenerativeModel(settings.gemini_model)
output_dir = settings.output_dir
```

### 4. **Error Handling Chain**
```
Exception Raised
     │
     ├─► Custom Exception (ConfigurationError, LLMGenerationError, etc.)
     │
     ├─► Caught by Service Layer
     │
     ├─► Re-raised or logged
     │
     ├─► Caught by FastAPI Exception Handler
     │
     └─► Converted to HTTP Response
```

### 5. **Multi-Layer Validation**
```
Input → Request Validation (Pydantic)
      → Schema Validation (Gemini response_schema)
      → Model Validation (CharacterSheet Pydantic model)
      → Business Validation (CharacterValidator)
      → Output
```

---

## Windows-Specific Implementations

### Path Handling
```python
# ✅ Cross-platform
from pathlib import Path
template_path = Path("app") / "templates" / "system_prompt.txt"

# ❌ Unix-only
template_path = "app/templates/system_prompt.txt"
```

### File Operations
```python
# Always specify encoding
with file_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
```

### Filename Sanitization
```python
# Remove Windows-invalid characters: < > : " / \ | ? *
def _sanitize_filename(filename: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename
```

### Environment Variables
```python
# Works on both Windows and Unix
from dotenv import load_dotenv
load_dotenv()  # Loads from .env automatically

# Handles Windows paths
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# C:\Users\username\project\service-account.json
```

---

## Error Handling Matrix

| Error Type | HTTP Status | Recovery Strategy |
|------------|-------------|-------------------|
| Invalid Request | 400 Bad Request | Return validation errors to user |
| Validation Failed | 422 Unprocessable | Return specific field errors |
| Template Not Found | 500 Internal Server | Log error, check configuration |
| LLM API Failure | 503 Service Unavailable | Retry up to 3 times with backoff |
| Storage Failure | 500 Internal Server | Log error, alert administrator |
| Authentication Error | 500 Internal Server | Check credentials configuration |

---

## Testing Strategy Overview

### Unit Tests (Isolated)
```python
tests/unit/
├── test_template_manager.py    # Mock file system
├── test_prompt_builder.py       # Mock template manager
├── test_validator.py            # Test business logic rules
└── test_storage_service.py      # Mock file operations
```

### Integration Tests (Component Interaction)
```python
tests/integration/
├── test_api_endpoints.py        # Full API workflow
├── test_vertex_client.py        # Real or mocked Vertex AI
└── test_end_to_end.py           # Complete generation flow
```

### Fixtures
```python
tests/fixtures/
├── sample_responses.json        # Known good LLM outputs
├── invalid_responses.json       # Edge cases
└── test_characters.json         # Test seed data
```

---

## Performance Considerations

### Caching
- **Template Manager**: LRU cache for prompt and schema files
- **Gemini API**: No caching (each generation is unique)
- **Results**: Optional result caching by character_id (future enhancement)

### Async Operations
```python
# API endpoint is async
@router.post("/generate-character-sheet")
async def generate_character_sheet(request: CharacterRequest):
    # Vertex AI call can be async
    result = await vertex_client.generate_character_sheet(...)
```

### Timeouts
- API timeout: 60 seconds (configurable)
- Gemini API call: Built-in timeout
- Retry strategy: 3 attempts with exponential backoff

---

## Security Checklist

- [ ] **API Keys**: Never hardcoded, always in environment variables
- [ ] **Input Validation**: All user input validated by Pydantic
- [ ] **File Paths**: Sanitized to prevent directory traversal
- [ ] **Error Messages**: Don't expose sensitive information
- [ ] **HTTPS**: Required in production
- [ ] **CORS**: Configured appropriately for frontend access
- [ ] **Rate Limiting**: Consider implementing for production

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Google Cloud credentials set up
- [ ] Templates created and validated
- [ ] Logging configured
- [ ] Error handling tested

### Production Configuration
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=WARNING`
- [ ] Service account (not user credentials)
- [ ] HTTPS enabled
- [ ] Monitoring set up
- [ ] Backup strategy for generated files

### Windows Server Deployment
```powershell
# Install Python 3.11+
# Install dependencies
pip install -r requirements.txt

# Set up service account
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\app\service-account.json"

# Run with Gunicorn (Windows alternative: waitress)
pip install waitress
waitress-serve --port=8000 app.main:app
```

---

## Quick Start Commands (Windows)

```powershell
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your settings

# Development
uvicorn app.main:app --reload

# Testing
pytest
pytest --cov=app tests/

# Production
waitress-serve --port=8000 app.main:app
```

---

## Next Steps

1. **Review** this architecture summary
2. **Approve** or request modifications
3. **Create** system prompt and character sheet schema
4. **Begin** Phase 1 implementation
5. **Iterate** based on testing feedback

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Status**: Ready for Implementation

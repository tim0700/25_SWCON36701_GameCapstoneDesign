# Character Sheet Generator - Technical Reference Document

## Architecture Analysis

### System Overview
The Character Sheet Generator is an automated pipeline that transforms minimal developer input (keywords/seed descriptions) into complete NPC character sheets in JSON format using Google's Gemini LLM via Vertex AI.

### Core Components

1. **Web API (FastAPI)**
   - Role: Primary interface for character creation requests
   - Handles HTTP POST requests with character_id and seed_description
   - Returns generated character sheets or error responses

2. **Prompt Template Manager**
   - Role: Manages system prompts and character sheet templates
   - Loads and manages configuration files (system_prompt.txt, character_sheet_schema.json)
   - Enables flexible updates without code changes

3. **Vertex AI Client**
   - Role: Interface to Gemini API
   - Handles LLM inference requests with structured output constraints
   - Manages API authentication and error handling

4. **Character Sheet Storage**
   - Role: Persists generated character sheets
   - File-based storage system using character_id as filename
   - Stores JSON files in organized directory structure

---

## Technology Stack Research (January 2025)

### 1. Vertex AI Gemini API - Structured Output

#### Key Findings
- **Latest Models**: Gemini 1.0 and 1.5 are retired; must use Gemini 2.5 models (e.g., gemini-2.5-flash-lite)
- **Structured Output Support**: Native JSON mode ensures schema compliance
- **Documentation Last Updated**: 2025-10-30 UTC

#### Implementation Details

**Response Schema Parameters:**
```python
{
    "response_mime_type": "application/json",
    "response_schema": {
        # OpenAPI 3.0 compatible schema
    }
}
```

**Schema Format:**
- Based on OpenAPI 3.0 schema definition
- Supports complex nested structures
- Guarantees valid JSON output when properly configured

**Key Benefits:**
- Eliminates output variability issues
- Automatic schema validation at generation time
- Predictable, parseable results

**Code Pattern:**
```python
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=[{"role": "user", "parts": [{"text": prompt}]}],
    config={
        "response_mime_type": "application/json",
        "response_schema": schema_dict
    }
)
```

#### Important Notes
- JSON Schema preview available for Gemini 2.5+ using `responseJsonSchema` field
- Schema acts as a strict template enforcing structure and data types
- Controlled generation available on both Pro and Flash variants

---

### 2. FastAPI Best Practices (2025)

#### Core Architecture Principles

**Project Structure:**
- Recommended: Feature-based organization (inspired by Netflix Dispatch)
- Avoid: Simple file-type based structure for larger projects
- Separate concerns: routers, models, services, schemas

**Async Programming:**
- FastAPI handles both async and sync operations efficiently
- Async routes called via `await`
- Sync routes run in threadpool automatically
- Use async for I/O-bound operations (database, API calls)

**Type Safety & Validation:**
- Built on Pydantic for automatic data validation
- Full type hints throughout codebase
- Catches errors at development time
- Automatic OpenAPI documentation generation

#### Security Best Practices
- OAuth2 or Bearer tokens for authentication
- CORS middleware for cross-origin requests
- Input sanitization and validation via Pydantic
- HTTPS enforcement in production

#### Performance Optimization
- FastAPI is one of the fastest Python frameworks
- Built on Starlette (async foundation)
- Use Gunicorn with Uvicorn workers for production
- Docker containerization recommended

#### Deployment
```bash
# Development
uvicorn main:app --reload

# Production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

### 3. Google Cloud Vertex AI Authentication

#### Authentication Methods

**Option 1: Application Default Credentials (ADC) - Local Development**
```bash
# Set up ADC using gcloud CLI
gcloud auth application-default login
```
- Credentials stored locally
- Automatic credential discovery
- Best for local development

**Option 2: Service Account - Production/Server**
```bash
# Set environment variable pointing to service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```
- Service account key file (JSON format)
- Download from Google Cloud Console
- Best for production deployments

**Option 3: Direct Credential Object**
```python
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account-key.json'
)
# Pass credentials during SDK initialization
```

#### SDK Installation & Initialization
```bash
pip install google-cloud-aiplatform
```

```python
import vertexai

vertexai.init(
    project="your-project-id",
    location="us-central1",
    credentials=credentials  # Optional, uses ADC if not provided
)
```

#### Environment-Specific Notes
- **Cloud Shell**: No additional setup required (pre-authenticated)
- **Local Development**: Use gcloud CLI authentication
- **Production**: Use service account with minimal required permissions

---

### 4. Pydantic v2 Integration with FastAPI

#### Performance Improvements
- **5-50x faster** than Pydantic v1
- Model instantiation: ~17x faster
- Validation: ~5x faster
- Serialization: ~10x faster
- Rust-powered core for performance

#### FastAPI Integration Benefits
- Automatic request/response validation
- OpenAPI schema generation
- Comprehensive error handling
- Type-safe throughout the stack

#### Schema Customization (Pydantic v2)
```python
from pydantic import BaseModel, Field

class CharacterSheet(BaseModel):
    character_id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., description="Character's full name")
    age: int | None = Field(None, description="Character's age")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "character_id": "npc_wandering_mage_elara",
                "name": "Elara Moonwhisper",
                "age": 127
            }]
        }
    }
```

#### JSON Schema Generation
```python
# Automatic schema generation
schema = CharacterSheet.model_json_schema()

# Schema automatically included in OpenAPI docs
# Used for validation in FastAPI routes
```

#### Validation Features
- Field-level validation with `Field()`
- Custom validators with `@field_validator`
- Model-level validation with `@model_validator`
- Automatic type coercion
- Rich error messages

---

## Workflow Implementation Details

### Step 1: API Request Handling
```python
@app.post("/generate-character-sheet")
async def generate_character_sheet(request: CharacterRequest):
    # Request model with Pydantic validation
    # Returns: CharacterSheetResponse or error
```

### Step 2: Template Loading
```python
def load_templates():
    system_prompt = Path("templates/system_prompt.txt").read_text()
    schema = json.loads(Path("templates/character_sheet_schema.json").read_text())
    return system_prompt, schema
```

### Step 3: Dynamic Prompt Assembly
```python
def assemble_prompt(system_prompt: str, character_id: str, seed_description: str) -> str:
    return f"""
{system_prompt}

Generate an NPC character sheet JSON based on:

<Seed Information>
- ID: {character_id}
- Description: {seed_description}
</Seed Information>
"""
```

### Step 4: LLM API Call
```python
from vertexai.generative_models import GenerativeModel

model = GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content(
    prompt,
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": character_sheet_schema
    }
)
```

### Step 5: Output Validation
```python
# Primary validation (Pydantic)
try:
    character_sheet = CharacterSheet.model_validate_json(response.text)
except ValidationError as e:
    # Handle validation errors
    raise HTTPException(status_code=422, detail=str(e))

# Secondary validation (optional business logic)
if not character_sheet.long_term_goal:
    raise ValueError("Character must have a long-term goal")
```

### Step 6: File Storage
```python
def save_character_sheet(character_id: str, data: dict):
    output_path = Path(f"data/npcs/{character_id}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))
    return output_path
```

---

## Key Technical Decisions

### 1. Model Selection
- **Recommended**: `gemini-2.5-flash-lite` or `gemini-2.5-flash`
- **Reason**: Latest models with structured output support, good balance of speed and quality
- **Note**: Gemini 1.5 and earlier are deprecated

### 2. Schema Format
- **Format**: OpenAPI 3.0 compatible JSON schema
- **Validation**: Double-layer (Gemini response_schema + Pydantic model)
- **Flexibility**: File-based templates for easy updates

### 3. Storage Strategy
- **Method**: File-based JSON storage
- **Structure**: `/data/npcs/{character_id}.json`
- **Rationale**: Simple, version-controllable, easy to inspect and debug

### 4. Error Handling Strategy
- Schema validation errors → 422 Unprocessable Entity
- API errors → 503 Service Unavailable
- File I/O errors → 500 Internal Server Error
- Business logic errors → 400 Bad Request

---

## Development Requirements

### Python Dependencies
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
google-cloud-aiplatform>=1.38.0
python-dotenv>=1.0.0
```

### Environment Variables
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
TEMPLATES_DIR=./templates
OUTPUT_DIR=./data/npcs
```

### Directory Structure
```
project/
├── main.py                    # FastAPI application entry point
├── routers/
│   └── character.py           # Character generation endpoints
├── services/
│   ├── template_manager.py    # Template loading logic
│   ├── vertex_client.py       # Vertex AI integration
│   └── storage.py             # File storage logic
├── models/
│   └── schemas.py             # Pydantic models
├── templates/
│   ├── system_prompt.txt      # System prompt template
│   └── character_sheet_schema.json  # OpenAPI schema
├── data/
│   └── npcs/                  # Generated character sheets
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

---

## Next Steps for Implementation

1. **Environment Setup**
   - Install Python dependencies
   - Configure Google Cloud authentication
   - Set up project structure

2. **Core Development**
   - Implement FastAPI application structure
   - Create Pydantic models for character sheets
   - Build template manager service
   - Integrate Vertex AI client

3. **Testing**
   - Unit tests for each component
   - Integration tests for full workflow
   - Test with various seed descriptions

4. **Deployment Preparation**
   - Docker containerization
   - Environment-specific configurations
   - Production security hardening

---

## References

- [Vertex AI Structured Output Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Vertex AI Python SDK Reference](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk)
- [Google Cloud Authentication Guide](https://cloud.google.com/vertex-ai/docs/authentication)

---

**Document Created**: 2025-11-02
**Last Updated**: 2025-11-02
**Status**: Ready for implementation

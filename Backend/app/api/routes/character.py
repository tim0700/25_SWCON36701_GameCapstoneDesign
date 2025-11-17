"""Character generation API routes.

This module defines the FastAPI endpoints for character sheet generation.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import ValidationError as PydanticValidationError

from app.config import settings
from app.core.logger import get_logger
from app.models.character_sheet import CharacterSheet
from app.models.schemas import CharacterRequest, CharacterResponse, HealthResponse
from app.services.prompt_builder import PromptBuilder
from app.services.storage_service import StorageService
from app.services.template_manager import TemplateManager
from app.services.validator import CharacterValidator
from app.services.vertex_client import VertexAIClient

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Initialize services (these will be created once when the module is imported)
template_manager = TemplateManager(settings.templates_dir)
prompt_builder = PromptBuilder(template_manager)
storage_service = StorageService(settings.output_dir)
vertex_client = VertexAIClient()
character_validator = CharacterValidator()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Service health status and version information

    Example:
        GET /api/v1/health
    """
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@router.post("/generate-character-sheet", response_model=CharacterResponse)
async def generate_character_sheet(request: CharacterRequest):
    """Generate a complete NPC character sheet from a seed description.

    This endpoint orchestrates the complete character generation workflow:
    1. Load templates
    2. Build prompt from seed description
    3. Call Vertex AI to generate character data
    4. Validate output against schema and business rules
    5. Save to file storage
    6. Return success response

    Args:
        request: Character generation request containing character_id and seed_description

    Returns:
        CharacterResponse with file path and generation timestamp

    Raises:
        Various exceptions handled by middleware (ValidationError, LLMGenerationError, etc.)

    Example:
        POST /api/v1/generate-character-sheet
        {
            "character_id": "npc_wandering_mage_elara",
            "seed_description": "A wandering mage seeking forgotten knowledge..."
        }
    """
    logger.info(f"Character generation requested: {request.character_id}")
    logger.debug(f"Seed description: {request.seed_description}")

    # Step 1: Build prompt
    logger.info("Building generation prompt")
    prompt = prompt_builder.build_character_prompt(
        character_id=request.character_id,
        seed_description=request.seed_description
    )

    # Step 2: Load schema
    logger.info("Loading character sheet schema")
    schema = template_manager.load_character_schema()

    # Step 3: Generate character sheet via Vertex AI
    logger.info("Calling Vertex AI for character generation")
    character_data = vertex_client.generate_character_sheet(
        prompt=prompt,
        schema=schema
    )
    
    print(character_data)

    # Step 3.5: Insert Charactere Sheet into Database
    from app.database import InsertCharacterSheetinDatabase
    InsertCharacterSheetinDatabase(character_data)


    # Step 4: Validate with Pydantic model
    logger.info("Validating generated character sheet")
    try:
        character_sheet = CharacterSheet.model_validate(character_data)
    except PydanticValidationError as e:
        logger.error(f"Pydantic validation failed: {str(e)}")
        raise

    # Step 5: Business logic validation
    logger.info("Performing business logic validation")
    character_validator.validate_character_sheet(character_sheet)

    # Step 6: Save to storage
    logger.info("Saving character sheet to storage")
    file_path = storage_service.save_character_sheet(
        character_id=request.character_id,
        data=character_data
    )

    # Step 7: Return success response
    logger.info(f"Character sheet generated successfully: {file_path}")

    return CharacterResponse(
        character_id=request.character_id,
        file_path=str(file_path),
        generated_at=datetime.utcnow(),
        message="Character sheet generated successfully"
    )


@router.get("/character/{character_id}")
async def get_character(character_id: str):
    """Retrieve an existing character sheet.

    Args:
        character_id: Unique character identifier

    Returns:
        Character sheet data

    Example:
        GET /api/v1/character/npc_wandering_mage_elara
    """
    logger.info(f"Character retrieval requested: {character_id}")

    character_data = storage_service.load_character_sheet(character_id)

    if character_data is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character '{character_id}' not found"
        )

    logger.info(f"Character retrieved: {character_id}")
    return character_data


@router.get("/characters")
async def list_characters():
    """List all available character sheets.

    Returns:
        List of character IDs

    Example:
        GET /api/v1/characters
    """
    logger.info("Character list requested")

    character_ids = storage_service.list_all_characters()

    logger.info(f"Found {len(character_ids)} characters")
    return {
        "total": len(character_ids),
        "characters": character_ids
    }


@router.delete("/character/{character_id}")
async def delete_character(character_id: str):
    """Delete a character sheet.

    Args:
        character_id: Unique character identifier

    Returns:
        Deletion confirmation

    Example:
        DELETE /api/v1/character/npc_wandering_mage_elara
    """
    logger.info(f"Character deletion requested: {character_id}")

    deleted = storage_service.delete_character_sheet(character_id)

    if not deleted:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character '{character_id}' not found"
        )

    logger.info(f"Character deleted: {character_id}")
    return {
        "success": True,
        "message": f"Character '{character_id}' deleted successfully"
    }

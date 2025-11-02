"""Template management service.

This module handles loading and caching of prompt templates and JSON schemas.
All file operations use Windows-compatible path handling and UTF-8 encoding.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from app.core.exceptions import TemplateError
from app.core.logger import get_logger

logger = get_logger(__name__)


class TemplateManager:
    """Manages loading and caching of templates for character generation.

    This service loads system prompts and character sheet schemas from the
    file system and caches them for performance. Templates can be reloaded
    if needed.
    """

    def __init__(self, templates_dir: Path):
        """Initialize template manager.

        Args:
            templates_dir: Directory containing template files (Windows-compatible Path)
        """
        self.templates_dir = templates_dir
        logger.info(f"TemplateManager initialized with directory: {templates_dir}")

        # Validate templates directory exists
        if not self.templates_dir.exists():
            raise TemplateError(
                f"Templates directory not found: {self.templates_dir}. "
                f"Please create it and add your template files."
            )

    @lru_cache(maxsize=1)
    def load_system_prompt(self) -> str:
        """Load and cache the system prompt template.

        Returns:
            System prompt text as a string

        Raises:
            TemplateError: If the template file cannot be loaded

        Example:
            >>> manager = TemplateManager(Path("app/templates"))
            >>> prompt = manager.load_system_prompt()
        """
        prompt_path = self.templates_dir / "system_prompt.txt"

        try:
            logger.debug(f"Loading system prompt from: {prompt_path}")
            # Use UTF-8 encoding for Windows compatibility
            prompt_text = prompt_path.read_text(encoding="utf-8")

            if not prompt_text.strip():
                raise TemplateError("System prompt file is empty")

            logger.info("System prompt loaded successfully")
            return prompt_text

        except FileNotFoundError:
            raise TemplateError(
                f"System prompt file not found: {prompt_path}. "
                f"Please create 'system_prompt.txt' in the templates directory."
            )
        except Exception as e:
            raise TemplateError(f"Failed to load system prompt: {str(e)}")

    @lru_cache(maxsize=1)
    def load_character_schema(self) -> Dict[str, Any]:
        """Load and cache the character sheet JSON schema.

        Returns:
            Character sheet schema as a dictionary (OpenAPI 3.0 format)

        Raises:
            TemplateError: If the schema file cannot be loaded or parsed

        Example:
            >>> manager = TemplateManager(Path("app/templates"))
            >>> schema = manager.load_character_schema()
        """
        schema_path = self.templates_dir / "character_sheet_schema.json"

        try:
            logger.debug(f"Loading character schema from: {schema_path}")
            # Use UTF-8 encoding for Windows compatibility
            with schema_path.open(encoding="utf-8") as f:
                schema = json.load(f)

            if not schema:
                raise TemplateError("Character schema file is empty")

            # Basic validation - should be a dict with 'type' field
            if not isinstance(schema, dict):
                raise TemplateError("Character schema must be a JSON object")

            logger.info("Character schema loaded successfully")
            return schema

        except FileNotFoundError:
            raise TemplateError(
                f"Character schema file not found: {schema_path}. "
                f"Please create 'character_sheet_schema.json' in the templates directory."
            )
        except json.JSONDecodeError as e:
            raise TemplateError(f"Invalid JSON in character schema: {str(e)}")
        except Exception as e:
            raise TemplateError(f"Failed to load character schema: {str(e)}")

    def reload_templates(self) -> None:
        """Clear cache and reload templates.

        This method clears the LRU cache, forcing templates to be reloaded
        from disk on the next access. Useful during development when templates
        are being modified.

        Example:
            >>> manager.reload_templates()
            >>> # Next call to load_system_prompt() will read from disk
        """
        logger.info("Clearing template cache")
        self.load_system_prompt.cache_clear()
        self.load_character_schema.cache_clear()
        logger.info("Template cache cleared successfully")

    def validate_templates(self) -> bool:
        """Validate that all required templates exist and can be loaded.

        Returns:
            True if all templates are valid

        Raises:
            TemplateError: If any template is missing or invalid

        Example:
            >>> manager = TemplateManager(Path("app/templates"))
            >>> if manager.validate_templates():
            ...     print("All templates valid")
        """
        try:
            self.load_system_prompt()
            self.load_character_schema()
            logger.info("All templates validated successfully")
            return True
        except TemplateError as e:
            logger.error(f"Template validation failed: {str(e)}")
            raise

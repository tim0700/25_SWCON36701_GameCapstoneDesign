"""File storage service for character sheets.

This module handles saving and retrieving character sheet JSON files with
Windows-compatible path handling and filename sanitization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.exceptions import StorageError
from app.core.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """Manages file-based storage of character sheets.

    This service handles saving character sheets to JSON files with proper
    Windows filename sanitization, UTF-8 encoding, and metadata injection.
    """

    # Windows-invalid filename characters
    INVALID_CHARS = '<>:"/\\|?*'

    def __init__(self, output_dir: Path):
        """Initialize storage service.

        Args:
            output_dir: Directory for storing character sheet files (Windows-compatible Path)
        """
        self.output_dir = output_dir
        # Ensure output directory exists (Windows compatible)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StorageService initialized with directory: {output_dir}")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove Windows-invalid characters from filename.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for Windows file systems

        Example:
            >>> StorageService._sanitize_filename('char:name?')
            'char_name_'
        """
        sanitized = filename
        for char in StorageService.INVALID_CHARS:
            sanitized = sanitized.replace(char, "_")
        return sanitized

    def save_character_sheet(
        self,
        character_id: str,
        data: Dict[str, Any],
        overwrite: bool = True
    ) -> Path:
        """Save character sheet to JSON file.

        Args:
            character_id: Unique character identifier (used as filename)
            data: Character sheet data as dictionary
            overwrite: Whether to overwrite existing file (default: True)

        Returns:
            Path to the saved JSON file

        Raises:
            StorageError: If file cannot be saved

        Example:
            >>> service = StorageService(Path("data/npcs"))
            >>> path = service.save_character_sheet("npc_mage", {...})
        """
        try:
            # Sanitize filename for Windows compatibility
            safe_id = self._sanitize_filename(character_id)
            file_path = self.output_dir / f"{safe_id}.json"

            # Check if file exists and overwrite is False
            if file_path.exists() and not overwrite:
                raise StorageError(
                    f"Character file already exists: {file_path}. "
                    f"Set overwrite=True to replace it."
                )

            # Add metadata
            data_with_metadata = data.copy()
            data_with_metadata["_metadata"] = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "schema_version": "2.2",
                "file_path": str(file_path)
            }

            logger.debug(f"Saving character sheet to: {file_path}")

            # Write to file with UTF-8 encoding (Windows compatible)
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(
                    data_with_metadata,
                    f,
                    indent=2,
                    ensure_ascii=False  # Allow Unicode characters
                )

            logger.info(f"Character sheet saved successfully: {file_path}")
            return file_path

        except PermissionError:
            raise StorageError(
                f"Permission denied writing to: {file_path}. "
                f"Check file permissions."
            )
        except OSError as e:
            raise StorageError(f"Failed to save character sheet: {str(e)}")
        except Exception as e:
            raise StorageError(f"Unexpected error saving character sheet: {str(e)}")

    def load_character_sheet(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character sheet from JSON file.

        Args:
            character_id: Unique character identifier

        Returns:
            Character sheet data as dictionary, or None if not found

        Raises:
            StorageError: If file exists but cannot be loaded

        Example:
            >>> service = StorageService(Path("data/npcs"))
            >>> data = service.load_character_sheet("npc_mage")
        """
        try:
            # Sanitize filename
            safe_id = self._sanitize_filename(character_id)
            file_path = self.output_dir / f"{safe_id}.json"

            if not file_path.exists():
                logger.warning(f"Character sheet not found: {file_path}")
                return None

            logger.debug(f"Loading character sheet from: {file_path}")

            # Read from file with UTF-8 encoding
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Character sheet loaded successfully: {file_path}")
            return data

        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in character sheet: {str(e)}")
        except Exception as e:
            raise StorageError(f"Failed to load character sheet: {str(e)}")

    def character_exists(self, character_id: str) -> bool:
        """Check if character sheet file exists.

        Args:
            character_id: Unique character identifier

        Returns:
            True if file exists, False otherwise

        Example:
            >>> service = StorageService(Path("data/npcs"))
            >>> if service.character_exists("npc_mage"):
            ...     print("Character found")
        """
        safe_id = self._sanitize_filename(character_id)
        file_path = self.output_dir / f"{safe_id}.json"
        return file_path.exists()

    def delete_character_sheet(self, character_id: str) -> bool:
        """Delete character sheet file.

        Args:
            character_id: Unique character identifier

        Returns:
            True if file was deleted, False if it didn't exist

        Raises:
            StorageError: If file exists but cannot be deleted

        Example:
            >>> service = StorageService(Path("data/npcs"))
            >>> service.delete_character_sheet("npc_mage")
        """
        try:
            safe_id = self._sanitize_filename(character_id)
            file_path = self.output_dir / f"{safe_id}.json"

            if not file_path.exists():
                logger.warning(f"Character sheet not found for deletion: {file_path}")
                return False

            file_path.unlink()
            logger.info(f"Character sheet deleted: {file_path}")
            return True

        except PermissionError:
            raise StorageError(
                f"Permission denied deleting: {file_path}. "
                f"Check file permissions."
            )
        except Exception as e:
            raise StorageError(f"Failed to delete character sheet: {str(e)}")

    def list_all_characters(self) -> list[str]:
        """List all character IDs that have saved sheets.

        Returns:
            List of character IDs

        Example:
            >>> service = StorageService(Path("data/npcs"))
            >>> characters = service.list_all_characters()
            >>> print(f"Found {len(characters)} characters")
        """
        try:
            json_files = self.output_dir.glob("*.json")
            # Extract character IDs from filenames (remove .json extension)
            character_ids = [f.stem for f in json_files]
            logger.debug(f"Found {len(character_ids)} character sheets")
            return sorted(character_ids)

        except Exception as e:
            logger.error(f"Error listing character sheets: {str(e)}")
            return []

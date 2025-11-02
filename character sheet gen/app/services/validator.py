"""Character sheet validation service.

This module provides business logic validation beyond basic Pydantic schema validation.
It checks for content quality, consistency, and completeness.
"""

from typing import List

from app.core.exceptions import ValidationError
from app.core.logger import get_logger
from app.models.character_sheet import CharacterSheet

logger = get_logger(__name__)


class CharacterValidator:
    """Validates character sheets for business logic and content quality.

    This validator performs secondary validation after Pydantic schema validation
    to ensure character sheets meet quality standards and business rules.
    """

    @staticmethod
    def validate_character_sheet(sheet: CharacterSheet) -> None:
        """Perform comprehensive business logic validation.

        Args:
            sheet: CharacterSheet instance to validate

        Raises:
            ValidationError: If validation fails with detailed error messages

        Example:
            >>> validator = CharacterValidator()
            >>> validator.validate_character_sheet(character_sheet)
        """
        logger.debug(f"Validating character sheet: {sheet.character_id}")

        errors: List[str] = []

        # Validate critical fields are not empty
        errors.extend(CharacterValidator._validate_critical_fields(sheet))

        # Validate age consistency
        errors.extend(CharacterValidator._validate_age(sheet))

        # Validate lists are not empty where required
        errors.extend(CharacterValidator._validate_required_lists(sheet))

        # Validate relationships
        errors.extend(CharacterValidator._validate_relationships(sheet))

        # If any errors found, raise ValidationError
        if errors:
            error_message = "; ".join(errors)
            logger.error(f"Validation failed for {sheet.character_id}: {error_message}")
            raise ValidationError(error_message)

        logger.info(f"Character sheet validation passed: {sheet.character_id}")

    @staticmethod
    def _validate_critical_fields(sheet: CharacterSheet) -> List[str]:
        """Validate that critical fields are not empty.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []

        # Check required string fields are not empty
        if not sheet.long_term_goal or not sheet.long_term_goal.strip():
            errors.append("Character must have a non-empty long-term goal")

        if not sheet.background_summary or not sheet.background_summary.strip():
            errors.append("Character must have a non-empty background summary")

        if not sheet.origin or not sheet.origin.strip():
            errors.append("Character must have a non-empty origin")

        if not sheet.occupation or not sheet.occupation.strip():
            errors.append("Character must have a non-empty occupation")

        return errors

    @staticmethod
    def _validate_age(sheet: CharacterSheet) -> List[str]:
        """Validate age field consistency.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []

        if sheet.age is not None:
            if sheet.age < 0:
                errors.append("Age cannot be negative")
            if sheet.age > 1000:
                logger.warning(
                    f"Character {sheet.character_id} has unusually high age: {sheet.age}"
                )

        return errors

    @staticmethod
    def _validate_required_lists(sheet: CharacterSheet) -> List[str]:
        """Validate that required list fields are not empty.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []

        # These lists should have at least one item
        required_lists = {
            "personality_traits": sheet.personality_traits,
            "values": sheet.values,
            "skills": sheet.skills,
        }

        for field_name, field_value in required_lists.items():
            if not field_value or len(field_value) == 0:
                errors.append(f"Character must have at least one {field_name.replace('_', ' ')}")

        # Check for empty strings in lists
        all_lists = {
            "personality_traits": sheet.personality_traits,
            "values": sheet.values,
            "fears": sheet.fears,
            "short_term_goals": sheet.short_term_goals,
            "motivations": sheet.motivations,
            "skills": sheet.skills,
            "special_abilities": sheet.special_abilities,
            "notable_possessions": sheet.notable_possessions,
            "secrets": sheet.secrets,
            "sample_dialogue": sheet.sample_dialogue,
        }

        for field_name, field_value in all_lists.items():
            if field_value:
                empty_items = [item for item in field_value if not item or not item.strip()]
                if empty_items:
                    errors.append(f"Field '{field_name}' contains empty items")

        return errors

    @staticmethod
    def _validate_relationships(sheet: CharacterSheet) -> List[str]:
        """Validate relationship data consistency.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []

        for i, rel in enumerate(sheet.relationships):
            # Check character_name is not empty
            if not rel.character_name or not rel.character_name.strip():
                errors.append(f"Relationship {i+1} must have a non-empty character name")

            # Check relationship_type is not empty
            if not rel.relationship_type or not rel.relationship_type.strip():
                errors.append(f"Relationship {i+1} must have a non-empty relationship type")

            # Check description is not empty
            if not rel.description or not rel.description.strip():
                errors.append(f"Relationship {i+1} must have a non-empty description")

        return errors

    @staticmethod
    def validate_and_warn(sheet: CharacterSheet) -> List[str]:
        """Validate character sheet and return warnings without raising errors.

        This method performs the same checks as validate_character_sheet but
        returns warnings instead of raising exceptions. Useful for soft validation.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of warning messages (empty if no issues found)

        Example:
            >>> warnings = CharacterValidator.validate_and_warn(character_sheet)
            >>> for warning in warnings:
            ...     print(f"Warning: {warning}")
        """
        logger.debug(f"Performing soft validation: {sheet.character_id}")

        warnings: List[str] = []

        # Collect all validation errors as warnings
        warnings.extend(CharacterValidator._validate_critical_fields(sheet))
        warnings.extend(CharacterValidator._validate_age(sheet))
        warnings.extend(CharacterValidator._validate_required_lists(sheet))
        warnings.extend(CharacterValidator._validate_relationships(sheet))

        if warnings:
            logger.warning(f"Validation warnings for {sheet.character_id}: {warnings}")
        else:
            logger.info(f"No validation warnings for {sheet.character_id}")

        return warnings

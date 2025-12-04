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
        logger.debug(f"Validating character sheet: {sheet.npc_id}")

        errors: List[str] = []

        # Validate critical fields are not empty
        errors.extend(CharacterValidator._validate_critical_fields(sheet))

        # Validate psychological profile
        errors.extend(CharacterValidator._validate_psychological_profile(sheet))

        # Validate goals and motivations
        errors.extend(CharacterValidator._validate_goals(sheet))

        # Validate relationships and knowledge
        errors.extend(CharacterValidator._validate_relationships_and_knowledge(sheet))

        # If any errors found, raise ValidationError
        if errors:
            error_message = "; ".join(errors)
            logger.error(f"Validation failed for {sheet.npc_id}: {error_message}")
            raise ValidationError(error_message)

        logger.info(f"Character sheet validation passed: {sheet.npc_id}")

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
        if not sheet.npc_id or not sheet.npc_id.strip():
            errors.append("Character must have a non-empty NPC ID")

        if not sheet.name or not sheet.name.strip():
            errors.append("Character must have a non-empty name")

        if not sheet.role_title or not sheet.role_title.strip():
            errors.append("Character must have a non-empty role title")

        if not sheet.faction or not sheet.faction.strip():
            errors.append("Character must have a non-empty faction")

        if not sheet.primary_location or not sheet.primary_location.strip():
            errors.append("Character must have a non-empty primary location")

        return errors

    @staticmethod
    def _validate_psychological_profile(sheet: CharacterSheet) -> List[str]:
        """Validate psychological profile content.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []
        profile = sheet.psychological_profile

        # Check personality keywords
        if not profile.personality_keywords or len(profile.personality_keywords) == 0:
            errors.append("Character must have at least one personality keyword")
        else:
            empty_keywords = [k for k in profile.personality_keywords if not k or not k.strip()]
            if empty_keywords:
                errors.append("Personality keywords cannot be empty")

        # Check speaking style
        if not profile.speaking_style or not profile.speaking_style.strip():
            errors.append("Character must have a non-empty speaking style")

        # Check core values
        if not profile.core_values or len(profile.core_values) == 0:
            errors.append("Character must have at least one core value")
        else:
            empty_values = [v for v in profile.core_values if not v or not v.strip()]
            if empty_values:
                errors.append("Core values cannot be empty")

        # Check example lines (optional, but if present shouldn't be empty)
        if profile.example_lines:
            empty_lines = [line for line in profile.example_lines if not line or not line.strip()]
            if empty_lines:
                errors.append("Example dialogue lines cannot be empty")

        return errors

    @staticmethod
    def _validate_goals(sheet: CharacterSheet) -> List[str]:
        """Validate goals and motivations content.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []
        goals = sheet.goals_and_motivations

        # Check long-term goal
        if not goals.long_term_goal or not goals.long_term_goal.strip():
            errors.append("Character must have a non-empty long-term goal")

        # Check short-term goal
        if not goals.short_term_goal or not goals.short_term_goal.strip():
            errors.append("Character must have a non-empty short-term goal")

        return errors

    @staticmethod
    def _validate_relationships_and_knowledge(sheet: CharacterSheet) -> List[str]:
        """Validate relationships and knowledge base content.

        Args:
            sheet: CharacterSheet instance

        Returns:
            List of error messages (empty if validation passes)
        """
        errors = []
        data = sheet.relationships_and_knowledge

        # Validate relationships (can be empty, but if present must be valid)
        for i, rel in enumerate(data.relationships):
            # Check target_id is not empty
            if not rel.target_id or not rel.target_id.strip():
                errors.append(f"Relationship {i+1} must have a non-empty target_id")

            # Check type is not empty
            if not rel.type or not rel.type.strip():
                errors.append(f"Relationship {i+1} must have a non-empty type")

            # Check reason is not empty
            if not rel.reason or not rel.reason.strip():
                errors.append(f"Relationship {i+1} must have a non-empty reason")

        # Validate knowledge base
        kb = data.knowledge_base

        # Check facts (should have at least one)
        if not kb.facts or len(kb.facts) == 0:
            errors.append("Character must have at least one fact in knowledge base")
        else:
            empty_facts = [f for f in kb.facts if not f or not f.strip()]
            if empty_facts:
                errors.append("Knowledge base facts cannot be empty")

        # Check rumors (should have at least one)
        if not kb.rumors or len(kb.rumors) == 0:
            errors.append("Character must have at least one rumor in knowledge base")
        else:
            empty_rumors = [r for r in kb.rumors if not r or not r.strip()]
            if empty_rumors:
                errors.append("Knowledge base rumors cannot be empty")

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
        logger.debug(f"Performing soft validation: {sheet.npc_id}")

        warnings: List[str] = []

        # Collect all validation errors as warnings
        warnings.extend(CharacterValidator._validate_critical_fields(sheet))
        warnings.extend(CharacterValidator._validate_psychological_profile(sheet))
        warnings.extend(CharacterValidator._validate_goals(sheet))
        warnings.extend(CharacterValidator._validate_relationships_and_knowledge(sheet))

        if warnings:
            logger.warning(f"Validation warnings for {sheet.npc_id}: {warnings}")
        else:
            logger.info(f"No validation warnings for {sheet.npc_id}")

        return warnings

"""Prompt assembly service.

This module handles dynamic prompt construction by combining templates
with user input to create the final prompt sent to the LLM.
"""

from app.core.logger import get_logger
from app.services.template_manager import TemplateManager

logger = get_logger(__name__)


class PromptBuilder:
    """Builds prompts for character generation by combining templates with user input.

    This service takes the system prompt template and user-provided seed information
    to construct the final prompt sent to the Vertex AI LLM.
    """

    def __init__(self, template_manager: TemplateManager):
        """Initialize prompt builder with template manager.

        Args:
            template_manager: Template manager instance for loading templates
        """
        self.template_manager = template_manager
        logger.info("PromptBuilder initialized")

    def build_character_prompt(
        self,
        character_id: str,
        seed_description: str
    ) -> str:
        """Assemble final prompt for character sheet generation.

        This method combines the system prompt template with the user's seed
        information to create a complete prompt that instructs the LLM to
        generate a character sheet.

        Args:
            character_id: Unique identifier for the character
            seed_description: Brief description to seed character generation

        Returns:
            Complete prompt string ready for LLM submission

        Example:
            >>> builder = PromptBuilder(template_manager)
            >>> prompt = builder.build_character_prompt(
            ...     "npc_mage_elara",
            ...     "A wandering mage seeking forgotten knowledge"
            ... )
        """
        logger.debug(f"Building prompt for character: {character_id}")

        # Load system prompt template
        system_prompt = self.template_manager.load_system_prompt()

        # Construct the final prompt
        full_prompt = f"""{system_prompt}

Generate an NPC character sheet JSON that fully complies with the 'Output Schema'
based on the 'Seed Information' below.

<Seed Information>
- ID: {character_id}
- Description: {seed_description}
</Seed Information>

IMPORTANT INSTRUCTIONS:
1. Ensure all required fields are filled with creative, coherent, and internally consistent content.
2. The character should feel authentic and believable within the game world.
3. All personality traits, goals, and relationships should align with the seed description.
4. Generate rich, detailed content that brings this character to life.
5. Use the character_id exactly as provided in the 'character_id' field of the output.

Generate the character sheet now."""

        logger.info(f"Prompt built successfully for character: {character_id}")
        logger.debug(f"Prompt length: {len(full_prompt)} characters")

        return full_prompt

    def build_revision_prompt(
        self,
        character_id: str,
        seed_description: str,
        revision_instructions: str
    ) -> str:
        """Build a prompt for revising an existing character.

        This method can be used to generate a prompt that asks the LLM to
        revise or refine an existing character based on feedback.

        Args:
            character_id: Unique identifier for the character
            seed_description: Original seed description
            revision_instructions: Specific instructions for revision

        Returns:
            Prompt for character revision

        Example:
            >>> prompt = builder.build_revision_prompt(
            ...     "npc_mage_elara",
            ...     "A wandering mage",
            ...     "Make the character more mysterious and add a tragic backstory"
            ... )
        """
        logger.debug(f"Building revision prompt for character: {character_id}")

        system_prompt = self.template_manager.load_system_prompt()

        full_prompt = f"""{system_prompt}

You are revising an existing character based on new instructions.

<Original Seed Information>
- ID: {character_id}
- Description: {seed_description}
</Original Seed Information>

<Revision Instructions>
{revision_instructions}
</Revision Instructions>

Generate a REVISED character sheet that incorporates the revision instructions
while maintaining consistency with the original concept. Ensure all required
fields are filled and the output complies with the schema."""

        logger.info(f"Revision prompt built for character: {character_id}")

        return full_prompt

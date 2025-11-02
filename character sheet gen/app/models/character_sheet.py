"""Character sheet domain model.

This module defines the Pydantic model representing the complete NPC character sheet
structure. This model is used for validation of LLM-generated JSON output.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Relationship(BaseModel):
    """Character relationship model."""

    character_name: str = Field(
        ...,
        description="Name of the related character"
    )
    relationship_type: str = Field(
        ...,
        description="Type of relationship (friend, enemy, family, etc.)"
    )
    description: str = Field(
        ...,
        description="Description of the relationship"
    )


class CharacterSheet(BaseModel):
    """Complete NPC character sheet model (v2.2).

    This model represents the full structure of a character sheet and is used
    to validate JSON output from the LLM to ensure all required fields are present
    and properly formatted.
    """

    # Basic Information
    character_id: str = Field(
        ...,
        description="Unique identifier for the character"
    )
    name: str = Field(
        ...,
        description="Character's full name"
    )
    age: Optional[int] = Field(
        default=None,
        ge=0,
        description="Character's age in years"
    )
    gender: Optional[str] = Field(
        default=None,
        description="Character's gender"
    )
    occupation: str = Field(
        ...,
        description="Character's primary occupation or role"
    )

    # Background
    background_summary: str = Field(
        ...,
        description="Brief summary of character's background and history"
    )
    origin: str = Field(
        ...,
        description="Character's place of origin or homeland"
    )

    # Personality
    personality_traits: List[str] = Field(
        default_factory=list,
        description="List of key personality traits"
    )
    values: List[str] = Field(
        default_factory=list,
        description="Character's core values and beliefs"
    )
    fears: List[str] = Field(
        default_factory=list,
        description="Character's fears and anxieties"
    )

    # Goals and Motivations
    long_term_goal: str = Field(
        ...,
        description="Character's primary long-term goal"
    )
    short_term_goals: List[str] = Field(
        default_factory=list,
        description="Character's immediate short-term goals"
    )
    motivations: List[str] = Field(
        default_factory=list,
        description="What drives and motivates the character"
    )

    # Relationships
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Character's relationships with other characters"
    )

    # Skills and Abilities
    skills: List[str] = Field(
        default_factory=list,
        description="Character's skills and proficiencies"
    )
    special_abilities: List[str] = Field(
        default_factory=list,
        description="Character's special abilities or powers"
    )

    # Additional Details
    notable_possessions: List[str] = Field(
        default_factory=list,
        description="Important items or possessions"
    )
    secrets: List[str] = Field(
        default_factory=list,
        description="Character's hidden secrets"
    )

    # Dialogue
    speech_pattern: Optional[str] = Field(
        default=None,
        description="Character's distinctive way of speaking"
    )
    sample_dialogue: List[str] = Field(
        default_factory=list,
        description="Example dialogue lines for the character"
    )

    model_config = {
        "json_schema_extra": {
            "description": "NPC Character Sheet v2.2 for Aetheria World",
            "examples": [
                {
                    "character_id": "npc_wandering_mage_elara",
                    "name": "Elara Moonwhisper",
                    "age": 127,
                    "gender": "Female",
                    "occupation": "Wandering Mage and Artifact Scholar",
                    "background_summary": "Elara has spent over a century traveling the world in search of forgotten magical knowledge and ancient artifacts.",
                    "origin": "The Ethereal Towers, a floating city of mages",
                    "personality_traits": ["Curious", "Prickly", "Warm-hearted", "Determined"],
                    "values": ["Knowledge", "Preservation of history", "Independence"],
                    "fears": ["Knowledge being lost forever", "Becoming irrelevant"],
                    "long_term_goal": "Uncover the location of the legendary Codex of Eternal Wisdom",
                    "short_term_goals": ["Decipher ancient runes in the Northern Wastes", "Find a reliable research partner"],
                    "motivations": ["Desire to preserve forgotten knowledge", "Personal quest for understanding"],
                    "relationships": [
                        {
                            "character_name": "Theron the Blacksmith",
                            "relationship_type": "Friend",
                            "description": "An old friend who provides her with enchanted equipment"
                        }
                    ],
                    "skills": ["Arcane magic", "Ancient languages", "Artifact identification"],
                    "special_abilities": ["Teleportation", "Time perception manipulation"],
                    "notable_possessions": ["Crystal compass that points to magical anomalies", "Weathered journal"],
                    "secrets": ["She was exiled from the Ethereal Towers for stealing a forbidden tome"],
                    "speech_pattern": "Speaks in a formal, slightly archaic manner with occasional scholarly tangents",
                    "sample_dialogue": [
                        "The past holds answers the present has forgotten.",
                        "I've no time for idle chatter. Either help me or step aside."
                    ]
                }
            ]
        }
    }

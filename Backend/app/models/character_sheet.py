"""Character sheet domain model.

This module defines the Pydantic model representing the complete NPC character sheet
structure. This model is used for validation of LLM-generated JSON output.
"""

from typing import List

from pydantic import BaseModel, Field


class PsychologicalProfile(BaseModel):
    """Psychological profile nested model."""

    personality_keywords: List[str] = Field(
        ...,
        description="List of personality trait keywords"
    )
    speaking_style: str = Field(
        ...,
        description="Description of how the character speaks"
    )
    example_lines: List[str] = Field(
        default_factory=list,
        description="Example dialogue lines"
    )
    core_values: List[str] = Field(
        ...,
        description="Character's core values and beliefs"
    )


class GoalsAndMotivations(BaseModel):
    """Goals and motivations nested model."""

    long_term_goal: str = Field(
        ...,
        description="Character's primary long-term goal"
    )
    short_term_goal: str = Field(
        ...,
        description="Character's immediate short-term goal"
    )


class Relationship(BaseModel):
    """Character relationship model."""

    target_id: str = Field(
        ...,
        description="ID of the related character"
    )
    type: str = Field(
        ...,
        description="Type of relationship (friend, enemy, ally, rival, etc.)"
    )
    reason: str = Field(
        ...,
        description="Reason or description of the relationship"
    )


class KnowledgeBase(BaseModel):
    """Knowledge base nested model."""

    facts: List[str] = Field(
        ...,
        description="Facts the character knows"
    )
    rumors: List[str] = Field(
        ...,
        description="Rumors the character has heard"
    )


class RelationshipsAndKnowledge(BaseModel):
    """Relationships and knowledge nested model."""

    relationships: List[Relationship] = Field(
        ...,
        description="Character's relationships with other characters"
    )
    knowledge_base: KnowledgeBase = Field(
        ...,
        description="Character's knowledge of facts and rumors"
    )


class CharacterSheet(BaseModel):
    """Complete NPC character sheet model (Custom Medieval Fantasy RPG).

    This model represents the full structure of a character sheet and is used
    to validate JSON output from the LLM to ensure all required fields are present
    and properly formatted.
    """

    # Basic Information
    npc_id: str = Field(
        ...,
        description="Unique identifier for the NPC"
    )
    name: str = Field(
        ...,
        description="Character's name"
    )
    age: str = Field(
        ...,
        description="Character's age"
    )
    gender: str = Field(
        ...,
        description="Character's gender"
    )
    role_title: str = Field(
        ...,
        description="Character's role or title"
    )
    faction: str = Field(
        ...,
        description="Character's faction or allegiance"
    )
    primary_location: str = Field(
        ...,
        description="Character's primary location"
    )

    # Nested Complex Structures
    psychological_profile: PsychologicalProfile = Field(
        ...,
        description="Character's psychological profile"
    )
    goals_and_motivations: GoalsAndMotivations = Field(
        ...,
        description="Character's goals and motivations"
    )
    relationships_and_knowledge: RelationshipsAndKnowledge = Field(
        ...,
        description="Character's relationships and knowledge"
    )

    model_config = {
        "json_schema_extra": {
            "description": "NPC Character Sheet for Medieval Fantasy RPG",
            "examples": [
                {
                    "npc_id": "npc_wandering_mage_elara",
                    "name": "Elara",
                    "age": "32",
                    "gender": "Female",
                    "role_title": "Wandering Mage",
                    "faction": "Unaffiliated",
                    "primary_location": "The Great Library",
                    "psychological_profile": {
                        "personality_keywords": ["Prickly", "Scholarly", "Guarded"],
                        "speaking_style": "Curt and dismissive initially, but engages thoughtfully if interested",
                        "example_lines": [
                            "Unless you have a pre-Cataclysmic tome to discuss, I'm quite busy.",
                            "That marking... it's from the Sunken City of Aeridor. Where did you see it?"
                        ],
                        "core_values": [
                            "Knowledge is the only treasure that cannot be stolen.",
                            "The past must be preserved to prevent its mistakes from being repeated."
                        ]
                    },
                    "goals_and_motivations": {
                        "long_term_goal": "To discover the location of the lost Library of Ashurban",
                        "short_term_goal": "To acquire the 'Star-Chart of the Navigator King'"
                    },
                    "relationships_and_knowledge": {
                        "relationships": [
                            {
                                "target_id": "npc_rival_cassian",
                                "type": "rival",
                                "reason": "Both seeking the same ancient artifacts"
                            }
                        ],
                        "knowledge_base": {
                            "facts": [
                                "The magical ley lines around Dragon's Tooth Mountains are unusually potent"
                            ],
                            "rumors": [
                                "A rival seeker has found a map piece and is heading towards the Coastal Village"
                            ]
                        }
                    }
                }
            ]
        }
    }

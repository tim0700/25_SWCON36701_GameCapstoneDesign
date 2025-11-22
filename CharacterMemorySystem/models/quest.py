"""
Quest-related data models for quest generation.

This module defines Pydantic models for quest generation requests and responses.
"""
from pydantic import BaseModel, Field


class QuestContext(BaseModel):
    """
    Context information for quest generation.
    
    Contains NPC, location, dungeon, and monster information used by
    the quest generation system to create contextually appropriate quests.
    """
    
    npc1_id: str = Field(
        ...,
        description="Quest giver NPC ID",
        min_length=1
    )
    npc1_name: str = Field(
        ...,
        description="Quest giver NPC name",
        min_length=1
    )
    npc1_desc: str = Field(
        ...,
        description="Quest giver NPC description",
        min_length=1
    )
    npc2_id: str = Field(
        ...,
        description="Target/companion NPC ID",
        min_length=1
    )
    npc2_name: str = Field(
        ...,
        description="Target/companion NPC name",
        min_length=1
    )
    npc2_desc: str = Field(
        ...,
        description="Target/companion NPC description",
        min_length=1
    )
    location_id: str = Field(
        ...,
        description="Quest location ID",
        min_length=1
    )
    location_name: str = Field(
        ...,
        description="Quest location name",
        min_length=1
    )
    dungeon_id: str = Field(
        default="",
        description="Optional dungeon ID for dungeon objectives"
    )
    monster_id: str = Field(
        default="",
        description="Optional monster ID for kill objectives"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc1_id": "elder_marcus",
                "npc1_name": "Elder Marcus",
                "npc1_desc": "Wise village elder",
                "npc2_id": "merchant_sarah",
                "npc2_name": "Merchant Sarah",
                "npc2_desc": "Traveling merchant",
                "location_id": "forest_ruins",
                "location_name": "Ancient Forest Ruins",
                "dungeon_id": "crypt_001",
                "monster_id": "goblin_boss"
            }
        }


class QuestGenerationResponse(BaseModel):
    """
    Response from quest generation endpoint.
    
    Contains the generated quest data as a JSON string that Unity
    can parse and use in the game.
    """
    
    quest_json: str = Field(
        ...,
        description="Generated quest data as JSON string"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quest_json": '{"quest_title": "Clear the Ancient Ruins", "quest_giver_npc_id": "elder_marcus", ...}'
            }
        }

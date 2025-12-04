using System.Collections.Generic;
using Newtonsoft.Json;

public class QuestData
{
    [JsonProperty("quest_title")]
    public string QuestTitle { get; set; }

    [JsonProperty("quest_giver_npc_id")]
    public string QuestGiverNpcId { get; set; }

    [JsonProperty("quest_steps")]
    public List<QuestStep> QuestSteps { get; set; }
}

public class QuestStep
{
    [JsonProperty("objective_type")]
    public string ObjectiveType { get; set; } 

    [JsonProperty("description_for_player")]
    public string DescriptionForPlayer { get; set; }

    [JsonProperty("dialogues")]
    public StepDialogues Dialogues { get; set; }

    [JsonProperty("details")]
    public StepDetails Details { get; set; } 
}

public class StepDialogues
{
    [JsonProperty("on_start")]
    public List<DialogueLine> OnStart { get; set; } 

    [JsonProperty("on_complete")]
    public List<DialogueLine> OnComplete { get; set; } 
}

public class DialogueLine
{
    [JsonProperty("speaker_id")]
    public string SpeakerId { get; set; }

    [JsonProperty("line")]
    public string Line { get; set; }
}

public class StepDetails
{
    // TALK 타입용
    [JsonProperty("target_npc_id")]
    public string TargetNpcId { get; set; }

    // GOTO 타입용
    [JsonProperty("target_location_id")]
    public string TargetLocationId { get; set; }

    // (추가) KILL 타입용
    [JsonProperty("target_monster_id")]
    public string TargetMonsterId { get; set; }

    // (추가) DUNGEON 타입용
    [JsonProperty("target_dungeon_id")]
    public string TargetDungeonId { get; set; }
}

// ============================================================================
// CharacterMemorySystem API Response Models
// ============================================================================

[System.Serializable]
public class MemoryEntry
{
    public string id;
    public string content;
    public string timestamp;
}

[System.Serializable]
public class RecentMemoryResponse
{
    public string status;
    public MemoryEntry[] memories;
    public int count;
}

[System.Serializable]
public class SearchResult
{
    public MemoryEntry memory;
    public float similarity_score;
}

[System.Serializable]
public class SearchMemoryResponse
{
    public string status;
    public SearchResult[] results;
    public int count;
}
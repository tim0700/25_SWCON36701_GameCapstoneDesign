using System.Collections.Generic;

/// <summary>
/// NPC 캐릭터 시트 JSON 파싱을 위한 모델 클래스들
/// Backend에서 생성된 JSON 파일 구조와 동일하게 매핑됨
/// </summary>

[System.Serializable]
public class NPCCharacterSheet
{
    public string npc_id;
    public string name;
    public string age;
    public string gender;
    public string role_title;
    public string faction;
    public string primary_location;
    public PsychologicalProfile psychological_profile;
    public GoalsAndMotivations goals_and_motivations;
    public RelationshipsAndKnowledge relationships_and_knowledge;
    public NPCMetadata _metadata;
}

[System.Serializable]
public class PsychologicalProfile
{
    public List<string> personality_keywords;
    public string speaking_style;
    public List<string> example_lines;
    public List<string> core_values;
}

[System.Serializable]
public class GoalsAndMotivations
{
    public string long_term_goal;
    public string short_term_goal;
}

[System.Serializable]
public class RelationshipsAndKnowledge
{
    public List<NPCRelationship> relationships;
    public KnowledgeBase knowledge_base;
}

[System.Serializable]
public class NPCRelationship
{
    public string target_id;
    public string type;
    public string reason;
}

[System.Serializable]
public class KnowledgeBase
{
    public List<string> facts;
    public List<string> rumors;
}

[System.Serializable]
public class NPCMetadata
{
    public string generated_at;
    public string schema_version;
    public string file_path;
}

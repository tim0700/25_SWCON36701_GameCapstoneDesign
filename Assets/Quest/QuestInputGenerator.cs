// QuestInputGenerator.cs (����)
using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using System.Collections.Generic;

[System.Serializable]
public class QuestContextData
{
    public string quest_giver_npc_id;
    public string quest_giver_npc_name;
    public string quest_giver_npc_role;
    public string quest_giver_npc_personality;
    public string quest_giver_npc_speaking_style;
    public string[] inLocation_npc_ids;
    public string[] inLocation_npc_names;
    public string[] inLocation_npc_roles;
    public string[] inLocation_npc_personalities;
    public string[] inLocation_npc_speaking_styles;
    public string location_id;
    public string location_name;
    public string[] dungeon_ids; 
    public string[] dungeon_names;
    public string[] monster_ids;
    public string[] monster_names;
}

public class QuestInputGenerator : MonoBehaviour
{
    
    public QuestContextData GatherContextData(string questGiverNpcId)
    {
        Debug.Log($"DB에서 {questGiverNpcId}의 컨텍스트 데이터 수집 중...");
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;
        
        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            QuestContextData contextData = new QuestContextData();
            
            dbConnection.Open();

            // 1. 퀘스트 제공자의 LOCID 찾기
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT LOCID FROM NPC WHERE NPCID = '{questGiverNpcId}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read()) 
                        contextData.location_id = reader.GetString(0);
                }
            }

            if (string.IsNullOrEmpty(contextData.location_id))
            {
                Debug.LogError($"DB에서 NPCID '{questGiverNpcId}'을 찾을 수 없거나 LOCID가 없습니다.");
                return null;
            }

            // 위치 이름 조회
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT NAME FROM LOC WHERE LOCID = '{contextData.location_id}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read()) 
                        contextData.location_name = reader.GetString(0);
                }
            }

            // 2. 던전 정보 조회 (List 사용)
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                List<string> dungeonIDsList = new List<string>();
                List<string> dungeonNamesList = new List<string>();

                cmd.CommandText = $"SELECT DUNID, NAME FROM DUNGEON WHERE LOCID = '{contextData.location_id}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        dungeonIDsList.Add(reader.GetString(0));
                        dungeonNamesList.Add(reader.GetString(1));
                    }
                }

                // List를 배열로 변환
                contextData.dungeon_ids = dungeonIDsList.ToArray();
                contextData.dungeon_names = dungeonNamesList.ToArray();
            }

            // 3. 몬스터 정보 조회 (List 사용)
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                List<string> monsterIDsList = new List<string>();
                List<string> monsterNamesList = new List<string>();

                cmd.CommandText = $"SELECT MONID, NAME FROM MONSTER WHERE LOCID = '{contextData.location_id}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        monsterIDsList.Add(reader.GetString(0));
                        monsterNamesList.Add(reader.GetString(1));
                    }
                }

                contextData.monster_ids = monsterIDsList.ToArray();
                contextData.monster_names = monsterNamesList.ToArray();
            }

            // 4. 퀘스트 제공자 정보 조회
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT NPCID, NAME, ROLE, PERSONALITY, SPEAKING_STYLE FROM NPC WHERE NPCID = '{questGiverNpcId}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        contextData.quest_giver_npc_id = reader.GetString(0);
                        contextData.quest_giver_npc_name = reader.GetString(1);
                        contextData.quest_giver_npc_role = reader.GetString(2);
                        contextData.quest_giver_npc_personality = reader.GetString(3);
                        contextData.quest_giver_npc_speaking_style = reader.GetString(4);
                    }
                }
            }

            // 5. 같은 위치의 다른 NPC 정보 조회 (List 사용)
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                List<string> npcIDsList = new List<string>();
                List<string> npcNamesList = new List<string>();
                List<string> npcRolesList = new List<string>();
                List<string> npcPersonalitiesList = new List<string>();
                List<string> npcSpeakingStylesList = new List<string>();

                cmd.CommandText = $"SELECT NPCID, NAME, ROLE, PERSONALITY, SPEAKING_STYLE FROM NPC WHERE LOCID = '{contextData.location_id}' AND NPCID != '{questGiverNpcId}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        npcIDsList.Add(reader.GetString(0));
                        npcNamesList.Add(reader.GetString(1));
                        npcRolesList.Add(reader.GetString(2));
                        npcPersonalitiesList.Add(reader.GetString(3));
                        npcSpeakingStylesList.Add(reader.GetString(4));
                    }
                }

                // List를 배열로 변환
                contextData.inLocation_npc_ids = npcIDsList.ToArray();
                contextData.inLocation_npc_names = npcNamesList.ToArray();
                contextData.inLocation_npc_roles = npcRolesList.ToArray();
                contextData.inLocation_npc_personalities = npcPersonalitiesList.ToArray();
                contextData.inLocation_npc_speaking_styles = npcSpeakingStylesList.ToArray();
            }

            Debug.Log("contextData is: " + JsonUtility.ToJson(contextData));
            
            return contextData;
        }
    }
}
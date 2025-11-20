// QuestInputGenerator.cs (수정)
using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using System.Collections.Generic;

public class QuestInputGenerator : MonoBehaviour
{
    private class NpcData
    {
        public string id;
        public string name;
        public string desc;
    }

    public string GatherContextData(string questGiverNpcId)
    {
        Debug.Log($"DB에서 {questGiverNpcId}를 기준으로 컨텍스트 수집 시작...");
        string dbname = "/TestDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;

        string npcLocationID = "";
        string locationName = "";
        string dungeonID = "";
        string objectID = "";  

        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            // 1. 퀘스트 제공자의 LOCID 찾기
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT LOCID FROM TB_NPC WHERE NPCID = '{questGiverNpcId}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read()) npcLocationID = reader.GetString(0);
                }
            }

            if (string.IsNullOrEmpty(npcLocationID))
            {
                Debug.LogError($"DB에서 NPCID '{questGiverNpcId}'를 찾을 수 없거나 LOCID가 없습니다.");
                return null;
            }

            // 2.LOCID로 장소 정보 (이름, 던전, 오브젝트) 찾기
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // TB_GC에서 3개 컬럼 조회
                cmd.CommandText = $"SELECT LOCNAME, DUNGEON, OBJECT FROM TB_GC WHERE LOCID = '{npcLocationID}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        locationName = reader.GetString(0);

                        // DB에서 NULL 값일 수 있으므로 IsDBNull로 안전하게 확인
                        dungeonID = !reader.IsDBNull(1) ? reader.GetString(1) : "";
                        objectID = !reader.IsDBNull(2) ? reader.GetString(2) : "";
                    }
                }
            }

            // 3. 같은 장소(LOCID)에 있는 모든 NPC 정보 수집
            List<NpcData> npcsInLocation = new List<NpcData>();
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT NPCID, NAME, DESC FROM TB_NPC WHERE LOCID = '{npcLocationID}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        npcsInLocation.Add(new NpcData
                        {
                            id = reader.GetString(0),
                            name = reader.GetString(1),
                            desc = reader.GetString(2)
                        });
                    }
                }
            }

            // 4. 퀘스트 제공자(NPC1)와 타겟(NPC2) 분리
            NpcData questGiver = null;
            NpcData targetNpc = null;

            foreach (var npc in npcsInLocation)
            {
                if (npc.id == questGiverNpcId) questGiver = npc;
                else if (targetNpc == null) targetNpc = npc;
            }

            // 5. 안전 검사
            if (questGiver == null)
            {
                Debug.LogError($"DB 조회 오류: {questGiverNpcId} 데이터를 찾지 못했습니다.");
                return null;
            }
            if (targetNpc == null)
            {
                Debug.LogWarning($"퀘스트 생성 경고: {questGiverNpcId}와 같은 위치에 다른 NPC가 없습니다.");
                return null;
            }

            // 6.10개 항목의 문자열 반환
            // (순서: NPC1(3), NPC2(3), LOC(2), DUNGEON(1), OBJECT(1))
            Debug.Log($"DB 조회 완료: DungeonID={dungeonID}, MonsterID(Object)={objectID}");
            return $"{questGiver.id}, {questGiver.name}, {questGiver.desc}, {targetNpc.id}, {targetNpc.name}, {targetNpc.desc}, {npcLocationID}, {locationName}, {dungeonID}, {objectID}";
        }
    }
}
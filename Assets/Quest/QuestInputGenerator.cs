// QuestInputGenerator.cs (����)
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
        Debug.Log($"DB���� {questGiverNpcId}�� �������� ���ؽ�Ʈ ���� ����...");
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;

        string npcLocationID = "";
        string locationName = "";
        string dungeonID = "";
        string objectID = "";  

        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            // 1. ����Ʈ �������� LOCID ã��
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                cmd.CommandText = $"SELECT LOCID FROM NPC WHERE NPCID = '{questGiverNpcId}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read()) npcLocationID = reader.GetString(0);
                }
            }

            if (string.IsNullOrEmpty(npcLocationID))
            {
                Debug.LogError($"DB���� NPCID '{questGiverNpcId}'�� ã�� �� ���ų� LOCID�� �����ϴ�.");
                return null;
            }

            // 2.LOCID�� ��� ���� (�̸�, ����, ������Ʈ) ã��
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // LOC���� 3�� �÷� ��ȸ
                cmd.CommandText = $"SELECT DUNID, NAME FROM DUNGEON WHERE LOCID = '{npcLocationID}'";
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        locationName = reader.GetString(0);

                        // DB���� NULL ���� �� �����Ƿ� IsDBNull�� �����ϰ� Ȯ��
                        dungeonID = !reader.IsDBNull(1) ? reader.GetString(1) : "";
                        objectID = !reader.IsDBNull(2) ? reader.GetString(2) : "";
                    }
                }
            }

            // 3. ���� ���(LOCID)�� �ִ� ��� NPC ���� ����
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

            // 4. ����Ʈ ������(NPC1)�� Ÿ��(NPC2) �и�
            NpcData questGiver = null;
            NpcData targetNpc = null;

            foreach (var npc in npcsInLocation)
            {
                if (npc.id == questGiverNpcId) questGiver = npc;
                else if (targetNpc == null) targetNpc = npc;
            }

            // 5. ���� �˻�
            if (questGiver == null)
            {
                Debug.LogError($"DB ��ȸ ����: {questGiverNpcId} �����͸� ã�� ���߽��ϴ�.");
                return null;
            }
            if (targetNpc == null)
            {
                Debug.LogWarning($"����Ʈ ���� ���: {questGiverNpcId}�� ���� ��ġ�� �ٸ� NPC�� �����ϴ�.");
                return null;
            }

            // 6.10�� �׸��� ���ڿ� ��ȯ
            // (����: NPC1(3), NPC2(3), LOC(2), DUNGEON(1), OBJECT(1))
            Debug.Log($"DB ��ȸ �Ϸ�: DungeonID={dungeonID}, MonsterID(Object)={objectID}");
            return $"{questGiver.id}, {questGiver.name}, {questGiver.desc}, {targetNpc.id}, {targetNpc.name}, {targetNpc.desc}, {npcLocationID}, {locationName}, {dungeonID}, {objectID}";
        }
    }
}
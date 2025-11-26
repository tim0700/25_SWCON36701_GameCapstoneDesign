// NPC.cs
using JetBrains.Annotations;
using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;

// using TMPro; // TextMeshPro�� QuestStartTester�� ���� �����ϹǷ� �ʿ� ����

public class NPC : MonoBehaviour
{
    // 1. �ν����Ϳ��� ������ NPC�� ���� ID
    public string npcId;
    public float interactionOffset = 1.5f; // �÷��̾ �� ��ġ (NPC ��)

    // 2. (Say �Լ��� QuestStartTester�� ���� UI�� �����ϹǷ� ����)

    // 3. Ŭ�� ������ ���� BoxCollider2D �ڵ� �߰�
    void Awake()
    {
        if (GetComponent<BoxCollider2D>() == null)
        {
            gameObject.AddComponent<BoxCollider2D>();
        }
    }

    void Start()
    {
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;
        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // NPC ID ����
                cmd.CommandText = $"SELECT NPCID FROM NPC WHERE NAME = '{gameObject.name}'";

                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        npcId = reader.GetString(0);
                    }
                }
            }
            dbConnection.Close();
        }
    }
}
using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;

[RequireComponent(typeof(BoxCollider2D))]
public class QuestLocation : MonoBehaviour
{
    public string entityId;

    public enum QuestEventType { GOTO, KILL, DUNGEON }
    public QuestEventType eventType = QuestEventType.GOTO;

    void Start()
    {
        // Open DB to get entityId
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;

        // Get game object tag to determine entity type
        string tag = gameObject.tag;

        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                if(tag == "Location")
                {
                    cmd.CommandText = $"SELECT LOCID FROM LOC WHERE NAME = '{gameObject.name}'";
                }
                else if(tag == "Dungeon")
                {
                    cmd.CommandText = $"SELECT DUNID FROM DUNGEON WHERE NAME = '{gameObject.name}'";
                }
                else if(tag == "Monster")
                {
                    cmd.CommandText = $"SELECT MONID FROM MONSTER WHERE NAME = '{gameObject.name}'";
                }

                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        entityId = reader.GetString(0);
                        Debug.Log($"[QuestLocation] {gameObject.name} - ID: {entityId}, Type: {eventType}");
                    }
                    else
                    {
                        Debug.LogWarning($"[QuestLocation] DB에서 '{gameObject.name}'을 찾을 수 없습니다!");
                    }
                }

                dbConnection.Close();
            }
        }

        // Collider를 Trigger로 설정
        BoxCollider2D collider = GetComponent<BoxCollider2D>();
        if (collider != null)
        {
            collider.isTrigger = true;
        }
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        // 플레이어와 충돌했는지 확인
        if (other.CompareTag("Player"))
        {
            Debug.Log($"[QuestLocation] {gameObject.name}과 상호작용! Type: {eventType}, ID: {entityId}");

            // QuestStartTester에 이벤트 알림
            if (QuestStartTester.Instance != null && !string.IsNullOrEmpty(entityId))
            {
                QuestStartTester.Instance.NotifyEvent(eventType.ToString(), entityId);
            }
            else
            {
                Debug.LogWarning("[QuestLocation] QuestStartTester Instance가 없거나 entityId가 비어있습니다!");
            }
        }
    }
}
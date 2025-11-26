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
                    }
                }

                dbConnection.Close();
            }
        }
    }
}
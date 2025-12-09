using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using System.Collections.Generic;

public class QuestInteractionUnavailable : MonoBehaviour
{
    public string entityId = "";
    public string description = "";
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
                if(tag == "Landmark")
                {
                    cmd.CommandText = $"SELECT LANDID FROM LANDMARK WHERE NAME = '{gameObject.name}'";
                    using (IDataReader reader = cmd.ExecuteReader())
                    {
                        if (reader.Read())
                        {
                            entityId = reader.GetString(0);
                        }
                    }
                }

                // Set description
                if (tag == "Landmark")
                {
                    cmd.CommandText = $"UPDATE LANDMARK SET DESCRIPTION = @desc WHERE LANDID = @id";
                    cmd.Parameters.Add(new SqliteParameter("@desc", description));
                    cmd.Parameters.Add(new SqliteParameter("@id", entityId));
                    cmd.ExecuteNonQuery();
                    Debug.Log($"Updated Landmark {entityId} with description: {description}");
                }
                dbConnection.Close();
            }
        }
    }
}

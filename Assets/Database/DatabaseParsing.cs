using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;

public class DatabaseParsing : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        string dbname = "/TestDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname; //Path to database
        IDbConnection dbConnection = new SqliteConnection(connectionString);
        dbConnection.Open(); //Open connection to the database

        string tablename = "TB_NPC";

        IDbCommand dbCommand = dbConnection.CreateCommand();
        string sqlQuery = "SELECT * " + "FROM " + tablename;
        dbCommand.CommandText = sqlQuery;
        IDataReader reader = dbCommand.ExecuteReader();

        while (reader.Read())
        {
            string npcID = reader.GetString(0);
            string location = reader.GetString(1);
            string npcName = reader.GetString(2);
            Debug.Log("NPC ID: " + npcID + ", Location: " + location + ", Name: " + npcName);
        }
    }
}

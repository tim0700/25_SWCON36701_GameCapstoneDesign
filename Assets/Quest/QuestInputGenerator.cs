using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;

public class QuestInputGenerator : MonoBehaviour
{

    // 1. When triggered(e.g. talk to an NPC), gather context data from database)
    public string GatherContextData(string NPCID)
    {
        // Placeholder for context data gathering logic
        Debug.Log("Gathering quest context data from database...");
        
        string dbname = "/TestDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname; //Path to database
        IDbConnection dbConnection = new SqliteConnection(connectionString);
        dbConnection.Open(); //Open connection to the database

        // get NPC location info
        string tablename = "TB_NPC";
        
        IDbCommand dbCommandLocation = dbConnection.CreateCommand();
        string locationQuery = "SELECT LOCID FROM TB_NPC WHERE NPCID = '" + NPCID + "'";
        dbCommandLocation.CommandText = locationQuery;
        IDataReader locationReader = dbCommandLocation.ExecuteReader();

        string npcLocationID = "";
        while (locationReader.Read())
        {
            npcLocationID = locationReader.GetString(0);
        }
        locationReader.Close();
        dbCommandLocation.Dispose();
        
        //// get location name
        tablename = "TB_GC";

        IDbCommand dbCommandGC = dbConnection.CreateCommand();
        string sqlQueryGC = "SELECT LOCNAME FROM " + tablename + " WHERE LOCID = '" + npcLocationID + "'";
        dbCommandGC.CommandText = sqlQueryGC;
        IDataReader readerGC = dbCommandGC.ExecuteReader();
        
        string locationName = "";
        if (readerGC.Read())
        {
            locationName = readerGC.GetString(0);
        }
        readerGC.Close();
        dbCommandGC.Dispose();

        // get NPC info that in the same location(NPCID, Name, Desc)

        tablename = "TB_NPC";
        IDbCommand dbCommandNPC = dbConnection.CreateCommand();
        string sqlQueryNPC = "SELECT NPCID, NAME, DESC " +
        "FROM " + tablename +
        " WHERE LOCID = '" + npcLocationID + "'";

        dbCommandNPC.CommandText = sqlQueryNPC;
        IDataReader readerNPC = dbCommandNPC.ExecuteReader();

        // assign npcID, npcName, npcDesc to two-dimensional array [3, *]

        string[,] npcInfo = new string[3, 10];
        
        int index = 0;
        while (readerNPC.Read())
        {
            npcInfo[0, index] = readerNPC.GetString(0);
            npcInfo[1, index] = readerNPC.GetString(1);
            npcInfo[2, index] = readerNPC.GetString(2);
            index++;
        }

        readerNPC.Close();
        dbCommandNPC.Dispose();
        dbConnection.Close(); //Close connection to the database

        // quest giver NPC info should be the first return NPC info
        int questgiverNPCIDindex = -1;
        for (int i = 0; i < index; i++)
        {
            if (npcInfo[0, i] == NPCID)
            {
                questgiverNPCIDindex = i;
                break;
            }
        }

        // if there are target NPCs in the same location we should return all of them
        // For simplicity, we only return the first target NPC info along with quest giver NPC info and location info 
        // target NPC info should be the second return NPC info
        int targetNPCIDindex = -1;
        for (int i = 0; i < index; i++)
        {
            if (npcInfo[0, i] != NPCID)
            {
                targetNPCIDindex = i;
                break;
            }
        }

        return $"{npcInfo[0,questgiverNPCIDindex]}, {npcInfo[1,questgiverNPCIDindex]}, {npcInfo[2,questgiverNPCIDindex]}, {npcInfo[0,targetNPCIDindex]}, {npcInfo[1,targetNPCIDindex]}, {npcInfo[2,targetNPCIDindex]}, {npcLocationID}, {locationName}";
    }
}

using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using System.Collections.Generic;

public class DatabaseInitializer : MonoBehaviour
{
    void Start()
    {
        InitializeDatabase();
    }

    private void InitializeDatabase()
    {
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;

        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            // DB 초기화
            // 먼저 DB 내의 (사용자) 테이블을 모두 삭제
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // 외래키 제약 처리 비활성화 (삭제 충돌 방지)
                cmd.CommandText = "PRAGMA foreign_keys = OFF;";
                cmd.ExecuteNonQuery();

                // sqlite_master에서 모든 테이블 이름 수집 (sqlite_ 로 시작하는 내부 테이블 제외)
                cmd.CommandText = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';";
                List<string> tableNames = new List<string>();
                using (IDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        string name = reader.GetString(0);
                        tableNames.Add(name);
                    }
                    reader.Close();
                }

                // 수집한 테이블 모두 삭제
                foreach (string t in tableNames)
                {
                    cmd.CommandText = $"DROP TABLE IF EXISTS \"{t}\";";
                    cmd.ExecuteNonQuery();
                }

                // 외래키 제약 다시 활성화
                cmd.CommandText = "PRAGMA foreign_keys = ON;";
                cmd.ExecuteNonQuery();
            }

            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // NPC 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS NPC (
                    NPCID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    AGE	TEXT,
                    GENDER	TEXT,
                    ROLE	TEXT,
                    FACTION	TEXT,
                    PERSONALITY	TEXT,
                    SPEAKING_STYLE	TEXT,
                    LOCID	TEXT,
                    PRIMARY KEY(NPCID),
                    FOREIGN KEY(LOCID) REFERENCES LOC(LOCID)
                )";
                cmd.ExecuteNonQuery();

                // LOCATION 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS LOC (
                    LOCID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    PRIMARY KEY(LOCID)
                )";
                cmd.ExecuteNonQuery();

                // DUNGEON 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS DUNGEON (
                    DUNID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    PRIMARY KEY(DUNID)
                )";
                cmd.ExecuteNonQuery();

                // MONSTER 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS MONSTER (
                    MONID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    PRIMARY KEY(MONID)
                )";
                cmd.ExecuteNonQuery();

                // NPC_RELATION 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE NPC_RELATION (
                    NPC1ID	TEXT NOT NULL,
                    NPC2ID	TEXT NOT NULL,
                    RELATION	TEXT,
                    PRIMARY KEY(NPC1ID,NPC2ID),
                    FOREIGN KEY(NPC1ID) REFERENCES NPC(NPCID),
                    FOREIGN KEY(NPC2ID) REFERENCES NPC(NPCID)
                )";
                cmd.ExecuteNonQuery();
            }

            // LOCATION 데이터 삽입
            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // Scene 내에 있는 Location 데이터 삽입
                GameObject[] locations = GameObject.FindGameObjectsWithTag("Location");
                int counter = 1;
                foreach (var loc in locations)
                {
                    string name = loc.name;
                    string locId = $"LOC{counter:000}_{name}";

                    cmd.CommandText = "INSERT OR REPLACE INTO LOC (LOCID, NAME) VALUES (@id, @name);";
                    cmd.Parameters.Clear();

                    var pId = cmd.CreateParameter();
                    pId.ParameterName = "@id";
                    pId.Value = locId;
                    cmd.Parameters.Add(pId);

                    var pName = cmd.CreateParameter();
                    pName.ParameterName = "@name";
                    pName.Value = name;
                    cmd.Parameters.Add(pName);

                    cmd.ExecuteNonQuery();
                    counter++;
                }
            }
        }

        Debug.Log("Database initialized successfully.");
    }
}

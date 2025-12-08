using UnityEngine;
using System.Data;
using System.IO;
using Mono.Data.Sqlite;
using System.Collections.Generic;

public class DatabaseInitializer : MonoBehaviour
{
    void Awake()
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
                // NPC 테이블도 제외
                cmd.CommandText = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'NPC';";
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
                    LOCID	TEXT,
                    PRIMARY KEY(DUNID),
                    FOREIGN KEY(LOCID) REFERENCES LOC(LOCID)
                )";
                cmd.ExecuteNonQuery();

                // MONSTER 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS MONSTER (
                    MONID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    LOCID	TEXT,
                    PRIMARY KEY(MONID),
                    FOREIGN KEY(LOCID) REFERENCES LOC(LOCID)
                )";
                cmd.ExecuteNonQuery();

                // LANDMAARK 테이블 생성
                cmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS LANDMARK (
                    LANDID	TEXT NOT NULL UNIQUE,
                    NAME	TEXT,
                    DESCRIPTION TEXT,
                    LOCID	TEXT,
                    PRIMARY KEY(LANDID),
                    FOREIGN KEY(LOCID) REFERENCES LOC(LOCID)
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

                // NPC 데이터는 JSON 파일에서 로드
                // (LoadNPCsFromJson 메서드에서 처리)

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

                    // 한 Location에 속한 Dungeon과 Monster도 함께 삽입
                    int duncounter = 1;
                    int moncounter = 1;
                    int landcounter = 1;
                    for(int i = 0; i < loc.transform.childCount; i++)
                    {
                        GameObject gameObjectInLoc = loc.transform.GetChild(i).gameObject;

                        // DUNGEON 삽입
                        if (gameObjectInLoc.CompareTag("Dungeon"))
                        {
                            string dunName = gameObjectInLoc.name;
                            string dunId = $"DUN{duncounter:000}_{dunName}";

                            cmd.CommandText = "INSERT OR REPLACE INTO DUNGEON (DUNID, NAME, LOCID) VALUES (@dunId, @dunName, @locId);";
                            cmd.Parameters.Clear();

                            var pdunId = cmd.CreateParameter();
                            pdunId.ParameterName = "@dunId";
                            pdunId.Value = dunId;
                            cmd.Parameters.Add(pdunId);

                            var pdunName = cmd.CreateParameter();
                            pdunName.ParameterName = "@dunName";
                            pdunName.Value = dunName;
                            cmd.Parameters.Add(pdunName);

                            var plocId = cmd.CreateParameter();
                            plocId.ParameterName = "@locId";
                            plocId.Value = locId;
                            cmd.Parameters.Add(plocId);

                            cmd.ExecuteNonQuery();
                            duncounter++;
                        }
                        else if (gameObjectInLoc.CompareTag("Monster"))
                        {
                            // MONSTER 삽입
                            string monName = gameObjectInLoc.name;
                            string monId = $"MON{moncounter:000}_{monName}";

                            cmd.CommandText = "INSERT OR REPLACE INTO MONSTER (MONID, NAME, LOCID) VALUES (@monId, @monName, @locId);";
                            cmd.Parameters.Clear();

                            var pmonId = cmd.CreateParameter();
                            pmonId.ParameterName = "@monId";
                            pmonId.Value = monId;
                            cmd.Parameters.Add(pmonId);

                            var pmonName = cmd.CreateParameter();
                            pmonName.ParameterName = "@monName";
                            pmonName.Value = monName;
                            cmd.Parameters.Add(pmonName);

                            var plocId2 = cmd.CreateParameter();
                            plocId2.ParameterName = "@locId";
                            plocId2.Value = locId;
                            cmd.Parameters.Add(plocId2);

                            cmd.ExecuteNonQuery();
                            moncounter++;
                        }
                        else if (gameObjectInLoc.CompareTag("Landmark"))
                        {
                            // LANDMARK 삽입
                            string landName = gameObjectInLoc.name;
                            string landId = $"LAND{landcounter:000}_{landName}";

                            cmd.CommandText = "INSERT OR REPLACE INTO LANDMARK (LANDID, NAME, DESCRIPTION, LOCID) VALUES (@landId, @landName, @landDesc, @locId);";
                            cmd.Parameters.Clear();

                            var plandId = cmd.CreateParameter();
                            plandId.ParameterName = "@landId";
                            plandId.Value = landId;
                            cmd.Parameters.Add(plandId);

                            var plandName = cmd.CreateParameter();
                            plandName.ParameterName = "@landName";
                            plandName.Value = landName;
                            cmd.Parameters.Add(plandName);

                            var plandDesc = cmd.CreateParameter();
                            plandDesc.ParameterName = "@landDesc";
                            plandDesc.Value = "";
                            cmd.Parameters.Add(plandDesc);

                            var plocId3 = cmd.CreateParameter();
                            plocId3.ParameterName = "@locId";
                            plocId3.Value = locId;
                            cmd.Parameters.Add(plocId3);

                            cmd.ExecuteNonQuery();
                            landcounter++;
                        }
                        
                    }
                }


            }

            // NPC 및 NPC_RELATION 데이터를 JSON에서 로드
            LoadNPCsFromJson(dbConnection);
        }

        Debug.Log("Database initialized successfully.");
    }

    /// <summary>
    /// StreamingAssets/npcs/ 폴더의 JSON 파일들을 파싱하여 NPC 및 NPC_RELATION 테이블에 삽입
    /// </summary>
    private void LoadNPCsFromJson(IDbConnection dbConnection)
    {
        string npcsPath = Path.Combine(Application.streamingAssetsPath, "npcs");
        
        if (!Directory.Exists(npcsPath))
        {
            Debug.LogWarning($"NPC JSON folder not found: {npcsPath}");
            return;
        }

        string[] jsonFiles = Directory.GetFiles(npcsPath, "*.json");
        int npcCount = 0;
        int relationCount = 0;

        using (IDbCommand cmd = dbConnection.CreateCommand())
        {
            foreach (string filePath in jsonFiles)
            {
                try
                {
                    string jsonContent = File.ReadAllText(filePath);
                    NPCCharacterSheet npc = JsonUtility.FromJson<NPCCharacterSheet>(jsonContent);

                    if (npc == null || string.IsNullOrEmpty(npc.npc_id))
                    {
                        Debug.LogWarning($"Invalid NPC JSON: {filePath}");
                        continue;
                    }

                    // 외래키 오류 방지: LOCID가 LOC 테이블에 있는지 확인
                    string locId = npc.primary_location;
                    if (!string.IsNullOrEmpty(locId)) 
                    {
                        cmd.CommandText = $"SELECT COUNT(*) FROM LOC WHERE LOCID = '{locId}'";
                        long count = (long)cmd.ExecuteScalar();
                        
                        // 없다면 임시로 생성 (또는 경고 로그)
                        if (count == 0)
                        {
                            Debug.LogWarning($"[DB] Location '{locId}' not found for NPC '{npc.name}'. Creating placeholder location.");
                            cmd.CommandText = "INSERT OR REPLACE INTO LOC (LOCID, NAME) VALUES (@locId, @locName)";
                            cmd.Parameters.Clear();
                            AddParameter(cmd, "@locId", locId);
                            AddParameter(cmd, "@locName", locId); // 이름도 ID로 임시 설정
                            cmd.ExecuteNonQuery();
                        }
                    }

                    // NPC 테이블에 삽입
                    cmd.CommandText = @"INSERT OR REPLACE INTO NPC 
                        (NPCID, NAME, AGE, GENDER, ROLE, FACTION, PERSONALITY, SPEAKING_STYLE, LOCID) 
                        VALUES (@npcId, @name, @age, @gender, @role, @faction, @personality, @speakingStyle, @locId);";
                    cmd.Parameters.Clear();

                    AddParameter(cmd, "@npcId", npc.npc_id);
                    AddParameter(cmd, "@name", npc.name);
                    AddParameter(cmd, "@age", npc.age);
                    AddParameter(cmd, "@gender", npc.gender);
                    AddParameter(cmd, "@role", npc.role_title);
                    AddParameter(cmd, "@faction", npc.faction);
                    
                    // personality_keywords를 쉼표로 연결
                    string personality = npc.psychological_profile?.personality_keywords != null 
                        ? string.Join(", ", npc.psychological_profile.personality_keywords) 
                        : "";
                    AddParameter(cmd, "@personality", personality);
                    
                    AddParameter(cmd, "@speakingStyle", npc.psychological_profile?.speaking_style ?? "");
                    AddParameter(cmd, "@locId", npc.primary_location);

                    cmd.ExecuteNonQuery();
                    npcCount++;

                    // NPC_RELATION 테이블에 관계 삽입
                    if (npc.relationships_and_knowledge?.relationships != null)
                    {
                        foreach (var relation in npc.relationships_and_knowledge.relationships)
                        {
                            if (string.IsNullOrEmpty(relation.target_id)) continue;

                            cmd.CommandText = @"INSERT OR REPLACE INTO NPC_RELATION 
                                (NPC1ID, NPC2ID, RELATION) VALUES (@npc1, @npc2, @relation);";
                            cmd.Parameters.Clear();

                            AddParameter(cmd, "@npc1", npc.npc_id);
                            AddParameter(cmd, "@npc2", relation.target_id);
                            AddParameter(cmd, "@relation", relation.type);

                            cmd.ExecuteNonQuery();
                            relationCount++;
                        }
                    }
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"Error loading NPC from {filePath}: {e.Message}");
                }
            }
        }

        Debug.Log($"Loaded {npcCount} NPCs and {relationCount} relationships from JSON files.");
    }

    /// <summary>
    /// IDbCommand에 파라미터를 추가하는 헬퍼 메서드
    /// </summary>
    private void AddParameter(IDbCommand cmd, string name, string value)
    {
        var param = cmd.CreateParameter();
        param.ParameterName = name;
        param.Value = value ?? "";
        cmd.Parameters.Add(param);
    }
}

// QuestRequester.cs (Updated with CharacterMemorySystem integration)
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using TMPro;

public class QuestRequester : MonoBehaviour
{
    [Header("Core Components")]
    public QuestStartTester questStartTester;
    public QuestInputGenerator questInputGenerator;

    [Header("Quest Template")]
    public string questGiverNpcId = "npc_amber";

    [Header("Server")]
    private string serverUrl = "http://127.0.0.1:8123/quest/generate";
    private string memoryServerUrl = "http://127.0.0.1:8123/memory";
    public TextMeshProUGUI buttonText;

    [System.Serializable]
    private class QuestContextData
    {
        public string npc1_id;
        public string npc1_name;
        public string npc1_desc;
        public string npc2_id;
        public string npc2_name;
        public string npc2_desc;
        public string location_id;
        public string location_name;
        public string dungeon_id;
        public string monster_id;
        public string player_dialogue;
    }

    [System.Serializable]
    private class FastAPIResponse { public string quest_json; }

    // =================================================================================
    // Public Quest Generation Method
    // =================================================================================

    public void OnCreateQuestButtonPressed(string questGiverNpcId, string playerDialogue = "")
    {
        if (questInputGenerator == null)
        {
            Debug.LogError("[QuestRequester] questInputGenerator가 할당되지 않았습니다!");
            if (buttonText != null) buttonText.text = "Setup Error!";
            return;
        }

        string contextString = questInputGenerator.GatherContextData(questGiverNpcId);

        if (string.IsNullOrEmpty(contextString))
        {
            Debug.LogError("[QuestRequester] DB에서 컨텍스트 데이터를 가져올 수 없습니다!");
            if (buttonText != null) buttonText.text = "Data Error!";
            return;
        }

        string[] parts = contextString.Split(',');
        if (parts.Length < 10)
        {
            Debug.LogError($"[QuestRequester] 잘못된 데이터 형식! (10개 필요, {parts.Length}개 받음)");
            if (buttonText != null) buttonText.text = "Parse Error!";
            return;
        }

        QuestContextData dataToSend = new QuestContextData
        {
            npc1_id = parts[0].Trim(),
            npc1_name = parts[1].Trim(),
            npc1_desc = parts[2].Trim(),
            npc2_id = parts[3].Trim(),
            npc2_name = parts[4].Trim(),
            npc2_desc = parts[5].Trim(),
            location_id = parts[6].Trim(),
            location_name = parts[7].Trim(),
            dungeon_id = parts[8].Trim(),
            monster_id = parts[9].Trim(),
            player_dialogue = playerDialogue
        };

        Debug.Log($"[QuestRequester] 퀘스트 생성 요청 시작 (NPC: {questGiverNpcId}, 대화: {(string.IsNullOrEmpty(playerDialogue) ? "(없음)" : playerDialogue)})");
        StartCoroutine(FetchQuestFromServer(dataToSend));
    }

    private IEnumerator FetchQuestFromServer(QuestContextData dataToSend)
    {
        string contextJson = JsonUtility.ToJson(dataToSend);
        Debug.Log($"[QuestRequester] 서버로 전송할 JSON: {contextJson}");

        using (UnityWebRequest webRequest = new UnityWebRequest(serverUrl, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(contextJson);
            webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
            webRequest.downloadHandler = new DownloadHandlerBuffer();
            webRequest.SetRequestHeader("Content-Type", "application/json");

            if (buttonText != null) buttonText.text = "Generating...";

            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                string responseJson = webRequest.downloadHandler.text;
                Debug.Log($"[QuestRequester] 서버 응답: {responseJson}");

                FastAPIResponse response = JsonUtility.FromJson<FastAPIResponse>(responseJson);
                string generatedQuestJson = response.quest_json;

                if (string.IsNullOrEmpty(generatedQuestJson))
                {
                    Debug.LogError("[QuestRequester] 퀘스트 JSON이 비어있습니다.");
                    if (buttonText != null) buttonText.text = "Error!";
                    yield break;
                }

                Debug.Log("[QuestRequester] 퀘스트 생성 성공! QuestStartTester로 전달합니다.");
                questStartTester.StartQuestFromJson(generatedQuestJson);
                if (buttonText != null) buttonText.text = "Quest Created!";
            }
            else
            {
                Debug.LogError($"[QuestRequester] 서버 요청 실패: {webRequest.error}");
                Debug.LogError($"[QuestRequester] 응답 코드: {webRequest.responseCode}");
                if (buttonText != null) buttonText.text = "Connection Failed";
            }
        }
    }

    // =================================================================================
    // CharacterMemorySystem Integration
    // =================================================================================

    public IEnumerator FetchMemoriesAndCreateQuest(string npcId, string playerInput)
    {
        RecentMemoryResponse recentMemories = null;
        SearchMemoryResponse searchResults = null;

        yield return FetchRecentMemories(npcId, (response) => { recentMemories = response; });
        yield return SearchMemories(npcId, playerInput, (response) => { searchResults = response; });

        LogMemories(recentMemories, searchResults);

        OnCreateQuestButtonPressed(npcId, playerInput);
    }

    private IEnumerator FetchRecentMemories(string npcId, System.Action<RecentMemoryResponse> callback)
    {
        string url = $"{memoryServerUrl}/{npcId}";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 5;
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    RecentMemoryResponse response = JsonUtility.FromJson<RecentMemoryResponse>(request.downloadHandler.text);
                    callback?.Invoke(response);
                }
                catch (System.Exception e)
                {
                    Debug.LogWarning($"[QuestRequester] Recent Memory 파싱 실패: {e.Message}");
                    callback?.Invoke(null);
                }
            }
            else
            {
                callback?.Invoke(null);
            }
        }
    }

    private IEnumerator SearchMemories(string npcId, string query, System.Action<SearchMemoryResponse> callback)
    {
        if (string.IsNullOrEmpty(query))
        {
            Debug.Log("[QuestRequester] 검색 쿼리 없음 - 검색 건너뜀");
            callback?.Invoke(null);
            yield break;
        }

        string escapedQuery = UnityWebRequest.EscapeURL(query);
        // top_k 제거 - 서버의 config.py 설정(similarity_search_results)을 따름
        string url = $"{memoryServerUrl}/{npcId}/search?query={escapedQuery}";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 5; // 유저 요청대로 5초 유지
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    SearchMemoryResponse response = JsonUtility.FromJson<SearchMemoryResponse>(request.downloadHandler.text);
                    callback?.Invoke(response);
                }
                catch (System.Exception e)
                {
                    Debug.LogWarning($"[QuestRequester] Memory Search 파싱 실패: {e.Message}");
                    callback?.Invoke(null);
                }
            }
            else
            {
                Debug.LogWarning($"[QuestRequester] Memory Search 실패: {request.error}");
                callback?.Invoke(null);
            }
        }
    }

    private void LogMemories(RecentMemoryResponse recent, SearchMemoryResponse search)
    {
        if (recent != null && recent.count > 0)
        {
            Debug.Log($"[QuestRequester] ========== 단기 기억 {recent.count}개 ==========");
            foreach (var m in recent.memories)
            {
                Debug.Log($"  [{m.timestamp}] {m.content}");
            }
        }
        else
        {
            Debug.Log("[QuestRequester] 단기 기억 없음");
        }

        if (search != null && search.count > 0)
        {
            Debug.Log($"[QuestRequester] ========== 검색 결과 {search.count}개 ==========");
            foreach (var r in search.results)
            {
                Debug.Log($"  [유사도: {r.similarity_score:F2}] {r.memory.content}");
            }
        }
        else
        {
            Debug.Log("[QuestRequester] 검색 결과 없음");
        }
    }
}
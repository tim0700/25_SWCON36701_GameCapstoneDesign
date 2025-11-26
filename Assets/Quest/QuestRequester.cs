// QuestRequester.cs (Updated with CharacterMemorySystem integration)
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using TMPro;
using System; // for nullable handling

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

    private class FastAPIResponse { public string quest_json; }

    // ======================================================
    // 전송용 페이로드 정의 (context + memories 함께 전송)
    // ======================================================
    private class QuestRequestPayload : QuestContextData
    {
        public string recent_memories_json;
        public string search_results_json;
    }

    // =================================================================================
    // Public Quest Generation Method
    // =================================================================================

    public void OnCreateQuestButtonPressed(string questGiverNpcId, string playerDialogue = "", RecentMemoryResponse recentMemories = null, SearchMemoryResponse searchResults = null)
    {
        if (questInputGenerator == null)
        {
            Debug.LogError("[QuestRequester] questInputGenerator가 할당되지 않았습니다!");
            if (buttonText != null) buttonText.text = "Setup Error!";
            return;
        }

        QuestContextData contextData = questInputGenerator.GatherContextData(questGiverNpcId);
        if (contextData == null)
        {
            Debug.LogError("[QuestRequester] 퀘스트 재료 데이터를 가져오지 못했습니다.");
            if (buttonText != null) buttonText.text = "Data Error!";
            return;
        }

        // 페이로드 생성: memories는 JSON 문자열로 포함 (서버에서 JSON.parse 필요)
        QuestRequestPayload payload = new QuestRequestPayload
        {
            quest_giver_npc_id = contextData.quest_giver_npc_id,
            quest_giver_npc_name = contextData.quest_giver_npc_name,
            quest_giver_npc_role = contextData.quest_giver_npc_role,
            quest_giver_npc_personality = contextData.quest_giver_npc_personality,
            quest_giver_npc_speaking_style = contextData.quest_giver_npc_speaking_style,
            inLocation_npc_ids = contextData.inLocation_npc_ids,
            inLocation_npc_names = contextData.inLocation_npc_names,
            inLocation_npc_roles = contextData.inLocation_npc_roles,
            inLocation_npc_personalities = contextData.inLocation_npc_personalities,
            inLocation_npc_speaking_styles = contextData.inLocation_npc_speaking_styles,
            location_id = contextData.location_id,
            location_name = contextData.location_name,
            dungeon_ids = contextData.dungeon_ids,
            dungeon_names = contextData.dungeon_names,
            monster_ids = contextData.monster_ids,
            monster_names = contextData.monster_names,
            recent_memories_json = recentMemories != null ? JsonUtility.ToJson(recentMemories) : null,
            search_results_json = searchResults != null ? JsonUtility.ToJson(searchResults) : null
        };
        
        Debug.Log($"[QuestRequester] 퀘스트 생성 요청 시작 (NPC: {questGiverNpcId}, 대화: {(string.IsNullOrEmpty(playerDialogue) ? "(없음)" : playerDialogue)})");
        Debug.Log($"[QuestRequester] 컨텍스트 데이터: {JsonUtility.ToJson(contextData, true)}");
        Debug.Log($"[QuestRequester] 페이로드 내용: {JsonUtility.ToJson(payload, true)}");
        // FetchQuestFromServer 시 페이로드 전달
        StartCoroutine(FetchQuestFromServer(payload));
    }

    // 코루틴은 이제 페이로드 객체를 받음
    private IEnumerator FetchQuestFromServer(QuestRequestPayload payloadToSend)
    {
        string contextJson = JsonUtility.ToJson(payloadToSend);
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

        OnCreateQuestButtonPressed(npcId, playerInput, recentMemories, searchResults);
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
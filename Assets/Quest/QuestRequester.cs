// QuestRequester.cs (Updated with player dialogue support)
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using TMPro;

public class QuestRequester : MonoBehaviour
{
    [Header("Core Components")]
    public QuestStartTester questStartTester;
    public QuestInputGenerator questInputGenerator; // 새로 추가 (DB 읽기 담당)

    [Header("Quest Template")]
    public string questGiverNpcId = "npc_amber"; // "Amber"의 ID

    [Header("Server")]
    private string serverUrl = "http://127.0.0.1:8001/generate-quest";  // Fixed: Changed from 8000 to 8001
    public TextMeshProUGUI buttonText;

    // FastAPI가 받을 데이터 구조 (player_dialogue 필드 추가)
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
        public string player_dialogue;  // NEW: Player's dialogue input
    }

    [System.Serializable]
    private class FastAPIResponse { public string quest_json; }

    // 버튼 클릭 시 호출될 함수 (수정: playerDialogue 파라미터 추가)
    public void OnCreateQuestButtonPressed(string questGiverNpcId, string playerDialogue = "")
    {
        if (questInputGenerator == null)
        {
            Debug.LogError("[QuestRequester] questInputGenerator가 할당되지 않았습니다!");
            if (buttonText != null) buttonText.text = "Setup Error!";
            return;
        }

        // 1. PlayerController에서 받은 ID로 DB 재료를 가져옴
        string contextString = questInputGenerator.GatherContextData(questGiverNpcId);

        if (string.IsNullOrEmpty(contextString))
        {
            Debug.LogError("[QuestRequester] DB에서 컨텍스트 데이터를 가져올 수 없습니다!");
            if (buttonText != null) buttonText.text = "Data Error!";
            return;
        }

        // 2. 재료 문자열 파싱
        string[] parts = contextString.Split(',');
        if (parts.Length < 10)
        {
            Debug.LogError($"[QuestRequester] 잘못된 데이터 형식! (10개 필요, {parts.Length}개 받음)");
            if (buttonText != null) buttonText.text = "Parse Error!";
            return;
        }

        // 3. 서버로 보낼 객체 생성 (player_dialogue 포함)
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
            player_dialogue = playerDialogue  // NEW: Include player's dialogue
        };

        Debug.Log($"[QuestRequester] 퀘스트 생성 요청 시작 (NPC: {questGiverNpcId}, 대화: {(string.IsNullOrEmpty(playerDialogue) ? "(없음)" : playerDialogue)})");

        // 4. 서버에 전송
        StartCoroutine(FetchQuestFromServer(dataToSend));
    }

    // 코루틴은 이제 문자열이 아닌 QuestContextData 객체를 받음
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
}
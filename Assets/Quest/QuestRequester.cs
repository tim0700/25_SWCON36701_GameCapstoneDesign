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
    private string serverUrl = "http://127.0.0.1:8123/quest/generate";  // Fixed: Changed from 8000 to 8001 and chage domain
    public TextMeshProUGUI buttonText;

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
        QuestInputGenerator.QuestContextData contextString = questInputGenerator.GatherContextData(questGiverNpcId);
        if (contextString == null)
        {
            Debug.LogError("[QuestRequester] 퀘스트 재료 데이터를 가져오지 못했습니다.");
            if (buttonText != null) buttonText.text = "Data Error!";
            return;
        }

        Debug.Log($"[QuestRequester] 퀘스트 생성 요청 시작 (NPC: {questGiverNpcId}, 대화: {(string.IsNullOrEmpty(playerDialogue) ? "(없음)" : playerDialogue)})");

        // 4. 서버에 전송
        StartCoroutine(FetchQuestFromServer(contextString));
    }

    // 코루틴은 이제 문자열이 아닌 QuestContextData 객체를 받음
    private IEnumerator FetchQuestFromServer(QuestInputGenerator.QuestContextData dataToSend)
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
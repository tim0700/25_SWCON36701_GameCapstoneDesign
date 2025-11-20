// QuestRequester.cs
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using TMPro;

public class QuestRequester : MonoBehaviour
{
    public QuestStartTester questStartTester;
    private string serverUrl = "http://127.0.0.1:8000/generate-quest";

    // --- 퀘스트 재료를 Inspector에서 입력 ---
    [Header("Quest Giver (NPC 1)")]
    public string npc1Id = "npc_amber";
    public string npc1Name = "Amber";
    public string npc1Desc = "A cheerful outrider from Mondstadt.";

    [Header("Target NPC (NPC 2)")]
    public string npc2Id = "npc_aura";
    public string npc2Name = "Aura";
    public string npc2Desc = "A mysterious and quiet person."; // NPC 2의 설명 추가

    [Header("Target Location")]
    public string locationId = "loc_woods";
    public string locationName = "Whispering Woods"; // 장소 이름 추가

    public TextMeshProUGUI buttonText;

    // ---  FastAPI로 보낼 데이터 구조 (QuestContextData) ---
    [System.Serializable]
    private class QuestContextData
    {
        // NPC 1 (퀘스트 제공자)
        public string npc1_id;
        public string npc1_name;
        public string npc1_desc;

        // NPC 2 (대상)
        public string npc2_id;
        public string npc2_name;
        public string npc2_desc;

        // Location (대상)
        public string location_id;
        public string location_name;
    }

    [System.Serializable]
    private class FastAPIResponse
    {
        public string quest_json;
    }

    public void OnCreateQuestButtonPressed()
    {
        Debug.Log("퀘스트 생성 요청 시작...");
        if (buttonText != null) buttonText.text = "Generating...";
        StartCoroutine(FetchQuestFromServer());
    }

    private IEnumerator FetchQuestFromServer()
    {

        QuestContextData dataToSend = new QuestContextData
        {
            npc1_id = this.npc1Id,
            npc1_name = this.npc1Name,
            npc1_desc = this.npc1Desc,

            npc2_id = this.npc2Id,
            npc2_name = this.npc2Name,
            npc2_desc = this.npc2Desc,

            location_id = this.locationId,
            location_name = this.locationName
        };
        string contextJson = JsonUtility.ToJson(dataToSend);

        using (UnityWebRequest webRequest = new UnityWebRequest(serverUrl, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(contextJson);
            webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
            webRequest.downloadHandler = new DownloadHandlerBuffer();
            webRequest.SetRequestHeader("Content-Type", "application/json");

            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                string responseJson = webRequest.downloadHandler.text;
                FastAPIResponse response = JsonUtility.FromJson<FastAPIResponse>(responseJson);
                string generatedQuestJson = response.quest_json;

                if (string.IsNullOrEmpty(generatedQuestJson))
                {
                    Debug.LogError("퀘스트 JSON이 비어있습니다.");
                    if (buttonText != null) buttonText.text = "Error!";
                    yield break;
                }

                questStartTester.StartQuestFromJson(generatedQuestJson);
                if (buttonText != null) buttonText.text = "Quest Created!";
            }
            else
            {
                Debug.LogError("서버 요청 실패: " + webRequest.error);
                if (buttonText != null) buttonText.text = "Connection Failed";
            }
        }
    }
}
// QuestRequester.cs (B안 적용)
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
    private string serverUrl = "http://127.0.0.1:8000/generate-quest";
    public TextMeshProUGUI buttonText;

    // FastAPI가 받을 데이터 구조 (이전과 동일)
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
    }

    [System.Serializable]
    private class FastAPIResponse { public string quest_json; }

    // 버튼 클릭 시 호출될 함수 
    public void OnCreateQuestButtonPressed(string questGiverNpcId)
    {
        if (questInputGenerator == null) { /* ... 오류 ... */ return; }

        // 1. PlayerController에서 받은 ID로 DB 재료를 가져옴
        string contextString = questInputGenerator.GatherContextData(questGiverNpcId);

        if (string.IsNullOrEmpty(contextString)) { /* ... 오류 ... */ return; }

        // 2. 재료 문자열 파싱
        string[] parts = contextString.Split(',');
        if (parts.Length < 10) { /* ... 오류 ... */ return; }

        // 3. 서버로 보낼 객체 생성
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
            monster_id = parts[9].Trim()  
        };

        // 4. 서버에 전송
        StartCoroutine(FetchQuestFromServer(dataToSend));
    }
    // 코루틴은 이제 문자열이 아닌 QuestContextData 객체를 받음
    private IEnumerator FetchQuestFromServer(QuestContextData dataToSend)
    {
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
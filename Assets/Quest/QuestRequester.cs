// QuestRequester.cs
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using TMPro;
using Unity.VisualScripting;

public class QuestRequester : MonoBehaviour
{
    public QuestStartTester questStartTester;
    private string serverUrl = "http://127.0.0.1:8000/generate-quest";

    // --- ����Ʈ ��Ḧ Inspector���� �Է� ---
    [Header("Quest Giver (NPC 1)")]
    public string npc1Id = "npc_amber";
    public string npc1Name = "Amber";
    public string npc1Desc = "A cheerful outrider from Mondstadt.";

    [Header("Target NPC (NPC 2)")]
    public string npc2Id = "npc_aura";
    public string npc2Name = "Aura";
    public string npc2Desc = "A mysterious and quiet person."; // NPC 2�� ���� �߰�

    [Header("Target Location")]
    public string locationId = "loc_woods";
    public string locationName = "Whispering Woods"; // ��� �̸� �߰�

    public TextMeshProUGUI buttonText;

    // ---  FastAPI�� ���� ������ ���� (QuestContextData) ---
    [System.Serializable]
    private class QuestContextData
    {
        // NPC 1 (����Ʈ ������)
        public string npc1_id;
        public string npc1_name;
        public string npc1_desc;

        // NPC 2 (���)
        public string npc2_id;
        public string npc2_name;
        public string npc2_desc;

        // Location (���)
        public string location_id;
        public string location_name;
    }

    [System.Serializable]
    private class FastAPIResponse
    {
        public string quest_json;
    }

    public void OnCreateQuestButtonPressed(string contextData)
    {
        Debug.Log("����Ʈ ���� ��û ����...");
        if (buttonText != null) buttonText.text = "Generating...";
        StartCoroutine(FetchQuestFromServer(contextData));
    }

    private IEnumerator FetchQuestFromServer(string contextData)
    {
        // Prepare context data to send
        // contextData is a comma-separated string: "npcId, npcName, npcDesc, locationId, locationName"
        string[] dataParts = contextData.Split(',');

        QuestContextData dataToSend = new QuestContextData
        {
            npc1_id = dataParts[0].Trim(),
            npc1_name = dataParts[1].Trim(),
            npc1_desc = dataParts[2].Trim(),

            // For simplicity, NPC 2 data is left null
            npc2_id = null,
            npc2_name = null,
            npc2_desc = null,

            location_id = dataParts[3].Trim(),
            location_name = dataParts[4].Trim()
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

                Debug.Log("Received Quest JSON: " + generatedQuestJson);
                if (string.IsNullOrEmpty(generatedQuestJson))
                {
                    Debug.LogError("����Ʈ JSON�� ����ֽ��ϴ�.");
                    if (buttonText != null) buttonText.text = "Error!";
                    yield break;
                }

                questStartTester.StartQuestFromJson(generatedQuestJson);
                if (buttonText != null) buttonText.text = "Quest Created!";
            }
            else
            {
                Debug.LogError("���� ��û ����: " + webRequest.error);
                if (buttonText != null) buttonText.text = "Connection Failed";
            }
        }
    }
}
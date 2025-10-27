using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class QuestRequest
{
    public string prompt;
}

[System.Serializable]
public class QuestResponse
{
    public string result;
}

public class QuestGenerator : MonoBehaviour
{
    private string serverUrl = "http://localhost:5000/generate_quest";
    
    public void GenerateQuest(string promptText)
    {
        StartCoroutine(SendQuestRequest(promptText));
    }
    
    IEnumerator SendQuestRequest(string promptText)
    {
        // 요청 데이터 생성
        QuestRequest requestData = new QuestRequest();
        requestData.prompt = promptText;
        
        // JSON으로 변환
        string jsonData = JsonUtility.ToJson(requestData);
        
        // HTTP 요청 생성
        using (UnityWebRequest request = new UnityWebRequest(serverUrl, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            
            // 요청 전송
            yield return request.SendWebRequest();
            
            // 응답 처리
            if (request.result == UnityWebRequest.Result.Success)
            {
                string responseText = request.downloadHandler.text;
                QuestResponse response = JsonUtility.FromJson<QuestResponse>(responseText);
                
                Debug.Log("퀘스트 생성 완료: " + response.result);
                // 여기서 response.result를 파싱하여 게임에 적용
                ProcessQuestData(response.result);
            }
            else
            {
                Debug.LogError("요청 실패: " + request.error);
            }
        }
    }
    
    void ProcessQuestData(string questJson)
    {
        // 받은 JSON 데이터를 게임에서 사용할 수 있도록 처리
        Debug.Log("받은 퀘스트 데이터: " + questJson);
        // TODO: JSON 파싱하여 실제 퀘스트 객체로 변환
    }
}
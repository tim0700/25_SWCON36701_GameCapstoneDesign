using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class GameContext
{
    public string playerName;
    public int level;
    public string location;
    public string mainObjective;
}

public class QuestResponse
{
    public string quest;
}

public class QuestClient : MonoBehaviour
{
    // Flask 서버 URL
    private string serverUrl = "http://localhost:5000/generate_quest";

    void Start()
    {
        // 예시 실행
        StartCoroutine(SendContextToServer());
    }

    IEnumerator SendContextToServer()
    {
        // 게임 컨텍스트 생성
        GameContext context = new GameContext
        {
            playerName = "에밀리",
            level = 12,
            location = "얼어붙은 동굴",
            mainObjective = "얼음 수정 찾기"
        };

        string jsonDatatest = "{\n  \"trigger_context\": {\n    \"quest_giver_npc\": {\n      \"id\": \"npc_amber\",\n      \"name\": \"엠버\",\n      \"role\": \"페보니우스 기사단 정찰 기사\",\n      \"traits\": [\n        \"활발함\",\n        \"솔직함\",\n        \"열정적임\",\n        \"비행 실력이 뛰어남\"\n      ]\n    },\n    \"related_locations\": [\n      {\n        \"id\": \"loc_mondstadt_city\",\n        \"name\": \"몬드성\",\n        \"description\": \"바람의 도시, 페보니우스 기사단이 위치한 중심 도시\"\n      },\n      {\n        \"id\": \"loc_whispering_woods\",\n        \"name\": \"바람이 시작되는 곳\",\n        \"description\": \"비행 시험이 열리는 몬드 근교 평원\"\n      },\n      {\n        \"id\": \"loc_lake_cidre\",\n        \"name\": \"시드르 호수\",\n        \"description\": \"비행 연습 및 이벤트가 개최되는 몬드 외곽 호수\"\n      }\n    ],\n    \"related_actors\": [\n      {\n        \"id\": \"player_character\",\n        \"name\": \"여행자\",\n        \"player_awareness_status\": \"엠버와 신뢰감을 형성한 외지인 동료\"\n      },\n      {\n        \"id\": \"npc_examiner\",\n        \"name\": \"페보니우스 기사단 시험관\",\n        \"player_awareness_status\": \"엠버의 상사이자, 비행 자격 심사 담당자\"\n      },\n      {\n        \"id\": \"npc_yura\",\n        \"name\": \"유라\",\n        \"player_awareness_status\": \"아직 알지 못함\"\n      }\n    ],\n    \"relation_graph\": {\n      \"nodes\": [\n        \"npc_amber\",\n        \"player_character\",\n        \"npc_examiner\",\n        \"npc_yura\"\n      ],\n      \"edges\": [\n        {\n          \"source\": \"npc_amber\",\n          \"target\": \"player_character\",\n          \"relationship\": \"비행 시험 교관\"\n        },\n        {\n          \"source\": \"npc_amber\",\n          \"target\": \"npc_examiner\",\n          \"relationship\": \"기사단 내 상하 관계\"\n        },\n        {\n          \"source\": \"npc_amber\",\n          \"target\": \"npc_yura\",\n          \"relationship\": \"몬드에 사는 친구\"\n        }\n      ]\n    }\n  }\n}";


        // JSON 직렬화
        string jsonData = JsonUtility.ToJson(context);
        // Debug.Log("보내는 데이터: " + jsonData);
        Debug.Log("보내는 데이터: " + jsonDatatest);

        // UnityWebRequest 생성
        using (UnityWebRequest req = new UnityWebRequest(serverUrl, "POST"))
        {
            byte[] body = Encoding.UTF8.GetBytes(jsonDatatest);
            req.uploadHandler = new UploadHandlerRaw(body);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            // 4️⃣ 요청 전송
            yield return req.SendWebRequest();

            // 5️⃣ 응답 처리
            if (req.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("서버 응답: " + req.downloadHandler.text);

                // JSON 응답 파싱
                QuestResponse res = JsonUtility.FromJson<QuestResponse>(req.downloadHandler.text);
                Debug.Log("생성된 퀘스트 내용:\n" + res.quest);
            }
            else
            {
                Debug.LogError("요청 실패: " + req.error);
            }
        }
    }
}


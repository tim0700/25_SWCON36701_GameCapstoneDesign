// NPC.cs
using UnityEngine;
// using TMPro; // TextMeshPro는 QuestStartTester가 직접 제어하므로 필요 없음

public class NPC : MonoBehaviour
{
    // 1. 인스펙터에서 설정할 NPC의 고유 ID
    public string npcId;
    public float interactionOffset = 1.5f; // 플레이어가 설 위치 (NPC 옆)

    // 2. (Say 함수는 QuestStartTester가 직접 UI를 제어하므로 삭제)

    // 3. 클릭 감지를 위한 BoxCollider2D 자동 추가
    void Awake()
    {
        if (GetComponent<BoxCollider2D>() == null)
        {
            gameObject.AddComponent<BoxCollider2D>();
        }
    }

    // 4. NPC 클릭 시 호출됨
    private void OnMouseDown()
    {
        // 1. 플레이어 오브젝트를 찾음
        GameObject player = GameObject.FindWithTag("Player");
        if (player == null)
        {
            Debug.LogError("씬에 'Player' 태그를 가진 오브젝트가 없습니다!");
            return;
        }

        // 2. 플레이어를 이 NPC 옆으로 이동시킴
        player.transform.position = new Vector2(transform.position.x + interactionOffset, transform.position.y);
        Debug.Log($"{player.name}를 {this.name} 옆으로 이동시킴");

        // 3. "두뇌"에게 'TALK' 이벤트가 발생했음을 알림
        QuestStartTester.Instance.NotifyEvent("TALK", npcId);
    }
}
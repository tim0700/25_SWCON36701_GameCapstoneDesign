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

}
using UnityEngine;
using UnityEngine.EventSystems;

public class PlayerController : MonoBehaviour
{
    public float offset = 1.5f;

    private QuestRequester questRequester;
    private DialogueInputPanel dialoguePanel;
    private QuestStartTester questStartTester;

    void Start()
    {
        questRequester = FindFirstObjectByType<QuestRequester>();
        questStartTester = FindFirstObjectByType<QuestStartTester>();
        dialoguePanel = FindFirstObjectByType<DialogueInputPanel>();
    }

    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            // UI 위에서 클릭했는지 확인 (버튼, 입력 필드 등)
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                // UI 클릭이면 플레이어 이동하지 않음
                return;
            }
            
            Vector2 mousePosition = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            RaycastHit2D hit = Physics2D.Raycast(mousePosition, Vector2.zero);

            if (hit.collider != null)
            {
                // 1. NPC를 클릭했는지 확인 (CharacterInfo 대신 NPC 사용)
                NPC targetNPC = hit.collider.GetComponent<NPC>();
                if (targetNPC != null)
                {
                    HandleNpcClick(targetNPC);
                    return; // NPC 클릭 처리 완료
                }

                // 2. 장소/몬스터/던전을 클릭했는지 확인
                QuestLocation targetLocation = hit.collider.GetComponent<QuestLocation>();
                if (targetLocation != null)
                {
                    HandleLocationClick(targetLocation);
                    return; // 장소 클릭 처리 완료
                }

                // (만약 CharacterInfo를 꼭 써야 한다면 GetComponent<NPC>() 대신 사용)
            }
            else
            {
                // 빈 공간을 클릭하면 플레이어 이동
                transform.position = new Vector2(mousePosition.x, mousePosition.y);
            }
        }
    }

    void HandleNpcClick(NPC target)
    {
        // 1. 플레이어를 NPC 옆으로 이동
        Vector2 targetPosition = target.transform.position;
        transform.position = new Vector2(targetPosition.x + offset, targetPosition.y);

        // 2. 퀘스트 진행 상태 확인
        if (questStartTester != null && questStartTester.isQuestInProgress)
        {
            // --- 퀘스트가 진행 중일 때 ---
            // 퀘스트 매니저에게 "TALK" 이벤트를 알립니다.
            Debug.Log($"[PlayerController] 퀘스트 이벤트 알림: TALK {target.npcId}");
            QuestStartTester.Instance.NotifyEvent("TALK", target.npcId);
        }
        else if (dialoguePanel != null && questRequester != null)
        {
            // --- 퀘스트가 없을 때 (새 퀘스트 생성 시도) ---
            // DialogueInputPanel을 표시하고 플레이어 입력을 받습니다.
            Debug.Log($"[PlayerController] 대화 입력 패널 표시: {target.npcId}");
            dialoguePanel.ShowPanel(target.npcId, (dialogue) => {
                // 플레이어가 대화를 입력하거나 스킵하면 이 콜백이 호출됩니다.
                Debug.Log($"[PlayerController] 대화 제출됨: {(string.IsNullOrEmpty(dialogue) ? "(스킵됨)" : dialogue)}");
                questRequester.OnCreateQuestButtonPressed(target.npcId, dialogue);
            });
        }
        else if (questRequester != null)
        {
            // --- DialogueInputPanel이 없는 경우 (폴백) ---
            // 빈 대화로 퀘스트 생성을 요청합니다.
            Debug.LogWarning("[PlayerController] DialogueInputPanel을 찾을 수 없습니다. 빈 대화로 퀘스트 생성.");
            questRequester.OnCreateQuestButtonPressed(target.npcId, "");
        }
    }

    void HandleLocationClick(QuestLocation target)
    {
        // 1. 플레이어를 장소로 이동
        transform.position = target.transform.position;

        // 2. 퀘스트가 진행 중일 때만 처리
        if (questStartTester != null && questStartTester.isQuestInProgress)
        {
            string eventType = target.eventType.ToString(); // GOTO, KILL, DUNGEON
            string entityId = target.entityId;

            Debug.Log($"[PlayerController] 퀘스트 이벤트 알림: {eventType} {entityId}");
            QuestStartTester.Instance.NotifyEvent(eventType, entityId);
        }
    }
}
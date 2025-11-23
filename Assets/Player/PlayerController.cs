using System.Collections;
using System.Runtime.CompilerServices;
using UnityEngine;
using UnityEngine.Assertions.Must;
using UnityEngine.InputSystem;
using UnityEngine.UI;

public class PlayerController : MonoBehaviour
{
    public float offset = 1.5f;
    private QuestRequester questRequester;
    private QuestStartTester questStartTester;

    private PlayerInputHandler inputHandler;

    void Awake()
    {
        inputHandler = FindFirstObjectByType<PlayerInputHandler>();   
    }
    void Start()
    {
        questRequester = FindFirstObjectByType<QuestRequester>();
        questStartTester = FindFirstObjectByType<QuestStartTester>();
    }

    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
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
                
                // 3. 포탈을 클릭했는지 확인
                Portal targetPortal = hit.collider.GetComponent<Portal>();
                if (targetPortal != null)
                {
                    HandlePortalClick(targetPortal);
                    return; // 포탈 클릭 처리 완료
                }
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
        else if (questRequester != null)
        {
            // --- 퀘스트가 없을 때 (새 퀘스트 생성 시도) ---
            // QuestRequester에게 이 NPC ID로 퀘스트 생성을 요청합니다.
            StartCoroutine(WaitForInputCompletion(target));
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

    void HandlePortalClick(Portal portal)
    {
        // 플레이어를 포탈로 이동
        transform.position = portal.transform.position;
        
        // Portal에 연결된 장소로 이동 처리
        // 카메라와 플레이어 위치를 새로운 location으로 옮김
        Debug.Log($"[PlayerController] 포탈 이동: {portal.linkedLocation.name}");
        Vector2 targetPosition = portal.linkedLocation.transform.position;
        Camera.main.transform.position = new Vector3(targetPosition.x, targetPosition.y, Camera.main.transform.position.z);
        transform.position = new Vector3(targetPosition.x, targetPosition.y, transform.position.z);
    }

    private IEnumerator WaitForInputCompletion(NPC target)
    {
        inputHandler.StartPlayerInput();

        yield return new WaitUntil(() => !inputHandler.IsInputting);

        // 입력이 완료된 후 처리
        string playerInput = inputHandler.GetLastInput;
        Debug.Log($"플레이어 입력 완료: {playerInput}");

        Debug.Log($"[PlayerController] 새 퀘스트 생성 요청: {target.npcId}");

        questRequester.OnCreateQuestButtonPressed(target.npcId);
    }
}
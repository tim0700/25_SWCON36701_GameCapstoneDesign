using UnityEngine;

/// <summary>
/// 탑뷰 맵에서 플레이어 이동 및 상호작용을 관리하는 컨트롤러
/// </summary>
public class TopDownPlayerController : MonoBehaviour
{
    [Header("Movement Settings")]
    [Tooltip("플레이어 이동 속도")]
    public float moveSpeed = 5f;

    [Header("Interaction Settings")]
    [Tooltip("상호작용 가능한 거리")]
    public float interactionRange = 2f;
    [Tooltip("NPC 레이어 (Inspector에서 설정)")]
    public LayerMask npcLayer;

    private Rigidbody2D rb;
    private Vector2 movement;
    private Animator animator; // 애니메이터가 있다면 사용
    private NPC nearbyNPC; // 현재 근처에 있는 NPC
    private bool isDialogueActive = false; // 대화 중 여부

    /// <summary>
    /// 대화 상태 설정 (NPCInteractionUI에서 호출)
    /// </summary>
    public void SetDialogueActive(bool active)
    {
        isDialogueActive = active;
        Debug.Log($"[Player] 대화 모드: {active}");
    }

    void Start()
    {
        // Rigidbody2D 컴포넌트 가져오기
        rb = GetComponent<Rigidbody2D>();
        
        if (rb != null)
        {
            // 탑뷰는 중력이 없음
            rb.gravityScale = 0f;
            // 회전 방지 (Z축 고정)
            rb.constraints = RigidbodyConstraints2D.FreezeRotation;
        }

        // Animator 컴포넌트 가져오기 (선택사항)
        animator = GetComponent<Animator>();
    }

    void Update()
    {
        // 대화 중에는 이동 불가
        if (!isDialogueActive)
        {
            // WASD 입력 받기
            movement.x = Input.GetAxisRaw("Horizontal"); // A/D 또는 좌/우 화살표
            movement.y = Input.GetAxisRaw("Vertical");   // W/S 또는 위/아래 화살표

            // 애니메이션 처리 (Animator가 있는 경우)
            if (animator != null)
            {
                animator.SetFloat("Horizontal", movement.x);
                animator.SetFloat("Vertical", movement.y);
                animator.SetFloat("Speed", movement.sqrMagnitude);
            }

            // 매 프레임마다 NPC 근처 확인
            CheckNearbyNPC();

            // E키 입력 감지 - NPC 상호작용
            if (Input.GetKeyDown(KeyCode.E))
            {
                TryInteractWithNPC();
            }
        }
        else
        {
            // 대화 중에는 이동 멈춤
            movement = Vector2.zero;
        }
    }

    /// <summary>
    /// 매 프레임마다 근처 NPC를 확인하고 프롬프트 표시/숨김
    /// </summary>
    private void CheckNearbyNPC()
    {
        // 플레이어 주변의 NPC 찾기
        Collider2D[] nearbyObjects = Physics2D.OverlapCircleAll(transform.position, interactionRange, npcLayer);

        NPC closestNPC = null;
        float closestDistance = float.MaxValue;

        // 가장 가까운 NPC 찾기
        foreach (Collider2D obj in nearbyObjects)
        {
            NPC npc = obj.GetComponent<NPC>();
            if (npc != null)
            {
                float distance = Vector2.Distance(transform.position, obj.transform.position);
                if (distance < closestDistance)
                {
                    closestDistance = distance;
                    closestNPC = npc;
                }
            }
        }

        // 이전 NPC와 다른 경우 프롬프트 업데이트
        if (closestNPC != nearbyNPC)
        {
            // 이전 NPC 프롬프트 숨김
            if (nearbyNPC != null)
            {
                nearbyNPC.HidePrompt();
            }

            // 새 NPC 프롬프트 표시
            nearbyNPC = closestNPC;
            if (nearbyNPC != null)
            {
                nearbyNPC.ShowPrompt();
            }
        }
    }

    void FixedUpdate()
    {
        // 물리 기반 이동 (Rigidbody2D 사용)
        if (rb != null)
        {
            // normalized로 대각선 이동 속도 정규화
            rb.MovePosition(rb.position + movement.normalized * moveSpeed * Time.fixedDeltaTime);
        }
        else
        {
            // Rigidbody2D가 없는 경우 Transform으로 이동
            transform.Translate(movement.normalized * moveSpeed * Time.fixedDeltaTime);
        }
    }

    /// <summary>
    /// NPC와 상호작용 시도 (E키)
    /// </summary>
    private void TryInteractWithNPC()
    {
        // 현재 근처에 있는 NPC가 있으면 대화 시작
        if (nearbyNPC != null)
        {
            Debug.Log($"[E키 상호작용] {nearbyNPC.name}와 대화 시작 시도");
            nearbyNPC.StartDialogue();
        }
        else
        {
            Debug.Log("[E키 상호작용] 근처에 상호작용 가능한 NPC가 없습니다.");
        }
    }

    /// <summary>
    /// 상호작용 범위를 Scene 뷰에서 시각화 (디버깅용)
    /// </summary>
    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, interactionRange);
    }
}

using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// NPC 대화 UI를 관리하는 매니저 클래스
/// </summary>
public class NPCInteractionUI : MonoBehaviour
{
    [Header("UI References")]
    [Tooltip("대화창 전체 패널")]
    public GameObject dialoguePanel;
    
    [Tooltip("NPC 이름 표시 텍스트")]
    public TextMeshProUGUI npcNameText;
    
    [Tooltip("플레이어 입력 필드")]
    public TMP_InputField playerInputField;
    
    [Tooltip("전송 버튼")]
    public Button sendButton;
    
    [Tooltip("대화 로딩 중 표시 (선택사항)")]
    public GameObject loadingIndicator;

    [Header("Settings")]
    [Tooltip("Enter 키로 전송 가능")]
    public bool submitOnEnter = true;

    // 현재 대화 중인 NPC
    private NPC currentNPC;
    private QuestRequester questRequester;
    private TopDownPlayerController playerController;

    void Start()
    {
        // QuestRequester 찾기
        questRequester = FindObjectOfType<QuestRequester>();
        
        if (questRequester == null)
        {
            //Debug.LogError("[NPCInteractionUI] QuestRequester를 찾을 수 없습니다!");
        }

        // 플레이어 컨트롤러 찾기
        playerController = FindObjectOfType<TopDownPlayerController>();
        if (playerController == null)
        {
            //Debug.LogWarning("[NPCInteractionUI] TopDownPlayerController를 찾을 수 없습니다!");
        }

        // 버튼 이벤트 연결
        if (sendButton != null)
        {
            sendButton.onClick.AddListener(OnSendButtonClicked);
        }

        // 초기 상태: 대화창 숨김
        HideDialogue();
    }

    void Update()
    {
        // Enter 키로 전송
        if (submitOnEnter && dialoguePanel != null && dialoguePanel.activeSelf)
        {
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
            {
                OnSendButtonClicked();
            }
        }
    }

    /// <summary>
    /// 대화창 열기
    /// </summary>
    public void ShowDialogue(NPC npc)
    {
        if (npc == null)
        {
            //Debug.LogWarning("[NPCInteractionUI] NPC가 null입니다.");
            return;
        }

        currentNPC = npc;

        //Debug.Log($"[NPCInteractionUI] {npc.gameObject.name}와 대화 시작");
        //Debug.Log($"[NPCInteractionUI] dialoguePanel 상태: {(dialoguePanel != null ? "연결됨" : "NULL!")}");
        //Debug.Log($"[NPCInteractionUI] npcNameText 상태: {(npcNameText != null ? "연결됨" : "NULL")}");
        //Debug.Log($"[NPCInteractionUI] playerInputField 상태: {(playerInputField != null ? "연결됨" : "NULL")}");

        // UI 활성화
        if (dialoguePanel != null)
        {
            //Debug.Log($"[NPCInteractionUI] dialoguePanel 활성화 전: {dialoguePanel.activeSelf}");
            dialoguePanel.SetActive(true);
            //Debug.Log($"[NPCInteractionUI] dialoguePanel 활성화 후: {dialoguePanel.activeSelf}");
        }
        else
        {
            //Debug.LogError("[NPCInteractionUI] dialoguePanel이 NULL입니다! Inspector에서 연결하세요!");
            return;
        }

        // NPC 이름 표시
        if (npcNameText != null)
        {
            npcNameText.text = $"{npc.gameObject.name}와 대화 중...";
        }

        // 입력 필드 초기화 및 포커스
        if (playerInputField != null)
        {
            playerInputField.text = "";
            playerInputField.Select();
            playerInputField.ActivateInputField();
        }

        // 로딩 표시 숨김
        if (loadingIndicator != null)
        {
            loadingIndicator.SetActive(false);
        }

        // 플레이어 이동 막기
        if (playerController != null)
        {
            playerController.SetDialogueActive(true);
        }
    }

    /// <summary>
    /// 대화창 닫기
    /// </summary>
    public void HideDialogue()
    {
        if (dialoguePanel != null)
        {
            dialoguePanel.SetActive(false);
        }

        currentNPC = null;

        // 플레이어 이동 허용
        if (playerController != null)
        {
            playerController.SetDialogueActive(false);
        }

        //Debug.Log("[NPCInteractionUI] 대화 종료");
    }

    /// <summary>
    /// 전송 버튼 클릭 시
    /// </summary>
    private void OnSendButtonClicked()
    {
        if (currentNPC == null)
        {
            //Debug.LogWarning("[NPCInteractionUI] 현재 대화 중인 NPC가 없습니다.");
            return;
        }

        if (playerInputField == null)
        {
            //Debug.LogError("[NPCInteractionUI] Input Field가 할당되지 않았습니다.");
            return;
        }

        string playerInput = playerInputField.text.Trim();

        // 빈 입력 체크 - 빈 입력도 허용 (Recent Memory만으로 퀘스트 생성)
        if (string.IsNullOrEmpty(playerInput))
        {
            //Debug.Log("[NPCInteractionUI] 빈 입력 - Recent Memory만으로 퀘스트 생성");
            // return 제거 - 계속 진행하여 Recent Memory 기반 퀘스트 생성
        }
        else
        {
            //Debug.Log($"[NPCInteractionUI] 플레이어 입력: {playerInput}");
        }

        // 로딩 표시
        if (loadingIndicator != null)
        {
            loadingIndicator.SetActive(true);
        }

        // QuestRequester를 통해 퀘스트 생성 시작
        if (questRequester != null && !string.IsNullOrEmpty(currentNPC.npcId))
        {
            StartCoroutine(questRequester.FetchMemoriesAndCreateQuest(
                currentNPC.npcId, 
                playerInput
            ));

            // 대화창 닫기 (또는 계속 열어둘 수도 있음)
            HideDialogue();
        }
        else
        {
            //Debug.LogError("[NPCInteractionUI] QuestRequester가 없거나 NPC ID가 비어있습니다.");
            if (loadingIndicator != null)
            {
                loadingIndicator.SetActive(false);
            }
        }
    }

    /// <summary>
    /// ESC 키로 대화 취소
    /// </summary>
    public void OnCancelButtonClicked()
    {
        HideDialogue();
    }
}

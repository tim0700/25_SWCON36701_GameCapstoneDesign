// NPC.cs
using JetBrains.Annotations;
using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using TMPro;

public class NPC : MonoBehaviour
{
    [Header("NPC Info")]
    [Tooltip("NPC의 고유 ID (DB에서 자동 로드됨)")]
    public string npcId;
    
    [Tooltip("플레이어 상호작용 거리")]
    public float interactionOffset = 1.5f;

    [Header("UI References")]
    [Tooltip("NPC 이름 표시 텍스트 (항상 표시)")]
    public TextMeshProUGUI npcNameText;
    
    [Tooltip("상호작용 프롬프트 오브젝트 (근처에만 표시)")]
    public GameObject interactionPrompt;
    
    [Tooltip("대화 UI 매니저")]
    public NPCInteractionUI dialogueUI;

    private bool isPlayerNearby = false;

    void Awake()
    {
        // BoxCollider2D 자동 추가 (상호작용용)
        if (GetComponent<BoxCollider2D>() == null)
        {
            gameObject.AddComponent<BoxCollider2D>();
        }
    }

    void Start()
    {
        // DB에서 NPC ID 로드
        LoadNPCDataFromDB();

        // NPC 이름 표시 (항상 보임)
        if (npcNameText != null)
        {
            npcNameText.text = gameObject.name;
        }

        // 초기 상태: 프롬프트 숨김
        HidePrompt();

        // DialogueUI 자동 찾기 (할당되지 않은 경우)
        if (dialogueUI == null)
        {
            dialogueUI = FindObjectOfType<NPCInteractionUI>();
            if (dialogueUI == null)
            {
                Debug.LogWarning($"[NPC {gameObject.name}] NPCInteractionUI를 찾을 수 없습니다!");
            }
        }
    }

    /// <summary>
    /// DB에서 NPC 정보 로드
    /// </summary>
    private void LoadNPCDataFromDB()
    {
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;
        
        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                // GameObject 이름으로 NPC ID 찾기
                cmd.CommandText = $"SELECT NPCID FROM NPC WHERE NAME = '{gameObject.name}'";

                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        npcId = reader.GetString(0);
                        Debug.Log($"[NPC] {gameObject.name}의 NPCID: {npcId}");
                    }
                    else
                    {
                        Debug.LogWarning($"[NPC] DB에서 '{gameObject.name}' NPC를 찾을 수 없습니다!");
                    }
                }
            }
            dbConnection.Close();
        }
    }

    /// <summary>
    /// 상호작용 프롬프트 표시 (플레이어가 근처에 왔을 때)
    /// </summary>
    public void ShowPrompt()
    {
        isPlayerNearby = true;
        if (interactionPrompt != null)
        {
            interactionPrompt.SetActive(true);
        }
    }

    /// <summary>
    /// 상호작용 프롬프트 숨김 (플레이어가 멀어졌을 때)
    /// </summary>
    public void HidePrompt()
    {
        isPlayerNearby = false;
        if (interactionPrompt != null)
        {
            interactionPrompt.SetActive(false);
        }
    }

    /// <summary>
    /// 대화 시작 (E키 눌렀을 때)
    /// 우선순위: 1. 퀘스트 목표 확인 → 2. 대화창 열기
    /// </summary>
    public void StartDialogue()
    {
        // 1순위: 현재 진행 중인 퀘스트의 TALK 목표 NPC인지 확인
        if (QuestStartTester.Instance != null && !string.IsNullOrEmpty(npcId))
        {
            if (QuestStartTester.Instance.IsTargetNPC(npcId))
            {
                Debug.Log($"[NPC] {gameObject.name}와 대화 - 퀘스트 목표 달성!");
                QuestStartTester.Instance.NotifyEvent("TALK", npcId);
                return; // 퀘스트 완료, 대화창 열지 않음
            }
        }

        // 2순위: 퀘스트 목표가 아니면 대화창 열기 (새 퀘스트 생성)
        Debug.Log($"[NPC] {gameObject.name}와 대화 - 대화창 열기");
        
        if (dialogueUI != null)
        {
            dialogueUI.ShowDialogue(this);
        }
        else
        {
            Debug.LogError($"[NPC {gameObject.name}] DialogueUI가 설정되지 않았습니다!");
        }
    }

    /// <summary>
    /// 플레이어가 근처에 있는지 확인
    /// </summary>
    public bool IsPlayerNearby()
    {
        return isPlayerNearby;
    }
}
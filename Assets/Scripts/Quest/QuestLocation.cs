using UnityEngine;
using System.Data;
using Mono.Data.Sqlite;
using TMPro;
using System.Collections;

[RequireComponent(typeof(BoxCollider2D))]
public class QuestLocation : MonoBehaviour
{
    public string entityId;

    public enum QuestEventType { GOTO, KILL, DUNGEON }
    public QuestEventType eventType = QuestEventType.GOTO;

    [Header("UI References")]
    [Tooltip("상호작용 프롬프트 오브젝트")]
    public GameObject interactionPrompt;
    
    [Tooltip("프롬프트 텍스트")]
    public TextMeshProUGUI promptText;

    [Header("Effect")]
    [Tooltip("상호작용 시 재생할 Particle System")]
    public ParticleSystem interactionEffect;

    [Header("Respawn Settings")]
    [Tooltip("사라진 후 다시 나타나기까지 시간 (초)")]
    public float respawnTime = 2f;

    private bool isPlayerNearby = false;
    private bool isActive = true; // 상호작용 가능 여부
    private SpriteRenderer spriteRenderer;
    private BoxCollider2D boxCollider;

    void Start()
    {
        // SpriteRenderer와 BoxCollider2D 참조
        spriteRenderer = GetComponent<SpriteRenderer>();
        boxCollider = GetComponent<BoxCollider2D>();

        // Open DB to get entityId
        string dbname = "/StaticDB.db";
        string connectionString = "URI=file:" + Application.streamingAssetsPath + dbname;

        // Get game object tag to determine entity type
        string tag = gameObject.tag;

        using (IDbConnection dbConnection = new SqliteConnection(connectionString))
        {
            dbConnection.Open();

            using (IDbCommand cmd = dbConnection.CreateCommand())
            {
                if(tag == "Location")
                {
                    cmd.CommandText = $"SELECT LOCID FROM LOC WHERE NAME = '{gameObject.name}'";
                }
                else if(tag == "Dungeon")
                {
                    cmd.CommandText = $"SELECT DUNID FROM DUNGEON WHERE NAME = '{gameObject.name}'";
                }
                else if(tag == "Monster")
                {
                    cmd.CommandText = $"SELECT MONID FROM MONSTER WHERE NAME = '{gameObject.name}'";
                }

                using (IDataReader reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        entityId = reader.GetString(0);
                        Debug.Log($"[QuestLocation] {gameObject.name} - ID: {entityId}, Type: {eventType}");
                    }
                    else
                    {
                        Debug.LogWarning($"[QuestLocation] DB에서 '{gameObject.name}'을 찾을 수 없습니다!");
                    }
                }

                dbConnection.Close();
            }
        }

        // Collider를 Trigger로 설정
        if (boxCollider != null)
        {
            boxCollider.isTrigger = true;
        }

        // 프롬프트 초기 설정
        if (interactionPrompt != null)
        {
            interactionPrompt.SetActive(false);
        }

        // 프롬프트 텍스트 설정
        if (promptText != null)
        {
            string actionText = eventType == QuestEventType.KILL ? "공격" : 
                               eventType == QuestEventType.DUNGEON ? "입장" : "이동";
            promptText.text = $"[F] {actionText}";
        }
    }

    void Update()
    {
        // 플레이어가 근처에 있고, 활성화 상태이며, F키를 누르면 상호작용
        if (isPlayerNearby && isActive && Input.GetKeyDown(KeyCode.F))
        {
            Interact();
        }
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        // 플레이어가 범위 안에 들어오면 프롬프트 표시 (활성화 상태일 때만)
        if (other.CompareTag("Player") && isActive)
        {
            isPlayerNearby = true;
            ShowPrompt();
        }
    }

    void OnTriggerExit2D(Collider2D other)
    {
        // 플레이어가 범위를 벗어나면 프롬프트 숨김
        if (other.CompareTag("Player"))
        {
            isPlayerNearby = false;
            HidePrompt();
        }
    }

    /// <summary>
    /// 상호작용 프롬프트 표시
    /// </summary>
    private void ShowPrompt()
    {
        if (interactionPrompt != null)
        {
            interactionPrompt.SetActive(true);
        }
    }

    /// <summary>
    /// 상호작용 프롬프트 숨김
    /// </summary>
    private void HidePrompt()
    {
        if (interactionPrompt != null)
        {
            interactionPrompt.SetActive(false);
        }
    }

    /// <summary>
    /// F키를 눌렀을 때 상호작용
    /// </summary>
    private void Interact()
    {
        Debug.Log($"[QuestLocation] {gameObject.name}과 상호작용! Type: {eventType}, ID: {entityId}");

        // 파티클 이펙트 재생 (사라지기 전에)
        if (interactionEffect != null)
        {
            interactionEffect.Play();
        }

        // QuestStartTester에 이벤트 알림
        if (QuestStartTester.Instance != null && !string.IsNullOrEmpty(entityId))
        {
            QuestStartTester.Instance.NotifyEvent(eventType.ToString(), entityId);
        }
        else
        {
            Debug.LogWarning("[QuestLocation] QuestStartTester Instance가 없거나 entityId가 비어있습니다!");
        }

        // 프롬프트 숨김
        HidePrompt();

        // 오브젝트 일시적으로 비활성화 후 리스폰
        StartCoroutine(RespawnCoroutine());
    }

    /// <summary>
    /// 2초 후 다시 나타나는 코루틴
    /// </summary>
    private IEnumerator RespawnCoroutine()
    {
        // 비활성화
        isActive = false;

        // 스프라이트 숨김
        if (spriteRenderer != null)
        {
            spriteRenderer.enabled = false;
        }

        // Collider 비활성화 (상호작용 불가)
        if (boxCollider != null)
        {
            boxCollider.enabled = false;
        }

        Debug.Log($"[QuestLocation] {gameObject.name} 사라짐 - {respawnTime}초 후 리스폰");

        // 대기 (이펙트는 계속 재생됨)
        yield return new WaitForSeconds(respawnTime);

        // 다시 활성화
        if (spriteRenderer != null)
        {
            spriteRenderer.enabled = true;
        }

        if (boxCollider != null)
        {
            boxCollider.enabled = true;
        }

        isActive = true;

        Debug.Log($"[QuestLocation] {gameObject.name} 리스폰 완료");
    }
}
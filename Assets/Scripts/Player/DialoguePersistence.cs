using UnityEngine;

/// <summary>
/// DialogueManager(NPCInteractionUI)를 씬 전환 시에도 유지하는 스크립트
/// DialogueManager GameObject에 추가하여 사용
/// </summary>
public class DialoguePersistence : MonoBehaviour
{
    private static DialoguePersistence instance;

    void Awake()
    {
        // Singleton 패턴으로 중복 방지
        if (instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
            Debug.Log("[DialogueManager] DontDestroyOnLoad 적용");
        }
        else
        {
            Destroy(gameObject);
            Debug.Log("[DialogueManager] 중복 인스턴스 제거");
        }
    }
}

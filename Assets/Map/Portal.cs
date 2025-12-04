using UnityEngine;
using UnityEngine.SceneManagement;

public class Portal : MonoBehaviour
{
    [Header("Portal Settings")]
    [Tooltip("이동할 씬 이름 (예: VillageScene, ForestScene)")]
    public string targetSceneName;
    
    [Tooltip("목표 씬의 스폰 위치")]
    public Vector3 spawnPosition;

    private bool hasExited = false; // 플레이어가 포탈을 벗어났는지

    void Awake()
    {
        BoxCollider2D collider = GetComponent<BoxCollider2D>();
        if (collider == null)
        {
            collider = gameObject.AddComponent<BoxCollider2D>();
        }
        collider.isTrigger = true;
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
        {
            // 플레이어가 포탈을 벗어났다가 다시 들어왔을 때만 작동
            if (hasExited)
            {
                ActivatePortal();
            }
        }
    }

    void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
        {
            hasExited = true; // 플레이어가 벗어남 - 다음 진입 시 작동 가능
        }
    }

    private void ActivatePortal()
    {
        Debug.Log($"[Portal] {gameObject.name} → {targetSceneName} 이동");
        
        // 포탈 사용 후 플래그 리셋 (다음 씬에서 다시 벗어나야 함)
        hasExited = false;
        
        // 스폰 위치 저장
        PlayerPrefs.SetFloat("SpawnX", spawnPosition.x);
        PlayerPrefs.SetFloat("SpawnY", spawnPosition.y);
        PlayerPrefs.SetFloat("SpawnZ", spawnPosition.z);
        PlayerPrefs.Save();
        
        // 씬 로드
        SceneManager.LoadScene(targetSceneName);
    }
}

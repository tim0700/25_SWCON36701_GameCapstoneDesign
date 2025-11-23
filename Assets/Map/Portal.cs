using UnityEngine;

public class Portal : MonoBehaviour
{
    // 포탈이 연결된 장소 정보, GameObject로 저장
    public GameObject linkedLocation;

    void Awake()
    {
        if (GetComponent<BoxCollider2D>() == null)
        {
            gameObject.AddComponent<BoxCollider2D>();
        }
    }
}

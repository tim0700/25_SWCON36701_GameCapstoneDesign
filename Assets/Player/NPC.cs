// NPC.cs
using JetBrains.Annotations;
using UnityEngine;
// using TMPro; // TextMeshPro�� QuestStartTester�� ���� �����ϹǷ� �ʿ� ����

public class NPC : MonoBehaviour
{
    // 1. �ν����Ϳ��� ������ NPC�� ���� ID
    public string npcId;
    public float interactionOffset = 1.5f; // �÷��̾ �� ��ġ (NPC ��)

    // 2. (Say �Լ��� QuestStartTester�� ���� UI�� �����ϹǷ� ����)

    // 3. Ŭ�� ������ ���� BoxCollider2D �ڵ� �߰�
    void Awake()
    {
        if (GetComponent<BoxCollider2D>() == null)
        {
            gameObject.AddComponent<BoxCollider2D>();
        }
    }
}
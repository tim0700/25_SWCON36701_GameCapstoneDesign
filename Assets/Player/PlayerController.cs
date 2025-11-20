using UnityEditor.Rendering.LookDev;
using UnityEngine;

public class PlayerController : MonoBehaviour
{
    // Ÿ�� ������ �̵��� ���� �Ÿ� ������
    public float offset = 1.5f;

    void Update()
    {
        // ���콺 ���� ��ư Ŭ�� ����
        if (Input.GetMouseButtonDown(0))
        {
            // ���콺 Ŭ�� ��ġ�� ���� ��ǥ�� ��ȯ
            Vector2 mousePosition = Camera.main.ScreenToWorldPoint(Input.mousePosition);

            // Ŭ���� ��ġ�� �ݶ��̴��� �ִ��� Ȯ���ϱ� ���� Ray �߻�
            RaycastHit2D hit = Physics2D.Raycast(mousePosition, Vector2.zero);

            // ���� �ݶ��̴��� �¾Ҵٸ� (���𰡸� Ŭ���ߴٸ�)
            if (hit.collider != null)
            {
                // Ŭ���� ������Ʈ���� CharacterInfo ������Ʈ�� ������
                CharacterInfo targetCharacter = hit.collider.GetComponent<CharacterInfo>();

                // CharacterInfo ������Ʈ�� �ִٸ� (Ÿ�� ĳ���͸� Ŭ���ߴٸ�)
                if (targetCharacter != null)
                {
                    // Ÿ�� ĳ���� ������ �÷��̾� ��ġ �̵�
                    // Ÿ���� �����ʿ� �ڸ��� �⵵�� ��ġ ����
                    Vector2 targetPosition = hit.collider.transform.position;
                    transform.position = new Vector2(targetPosition.x + offset, targetPosition.y);

                    // Ÿ�� ĳ������ ID�� �ֿܼ� ���
                    Debug.Log("Clicked Character ID: " + targetCharacter.characterID);

                    // +) Send Quest Trigger Event to QuestInputGenerator(first, replace trigger with scene start)
                    QuestInputGenerator questInputGenerator = FindFirstObjectByType<QuestInputGenerator>();

                    string contextData = "";
                    if (questInputGenerator != null)
                    {
                        contextData = questInputGenerator.GatherContextData(targetCharacter.characterID);
                        Debug.Log("Gathered Context Data: " + contextData);
                    }

                    // +) Trigger Quest Request to FastAPI Server
                    // Once quest is generated, QuestStartTester will start the quest
                    // While generated quest is in progress, this part will be skipped until the quest is completed
                    // 
                    QuestRequester questRequester = FindFirstObjectByType<QuestRequester>();
                    if (questRequester != null && questRequester.questStartTester.isQuestInProgress == false)
                    {
                        questRequester.OnCreateQuestButtonPressed(contextData);
                    }
                }
            }
            // �ݶ��̴��� ���� �ʾҴٸ� (����� Ŭ���ߴٸ�)
            else
            {
                // Ŭ���� ���� ��ǥ�� �÷��̾� ��ġ�� �ٷ� �̵�
                transform.position = new Vector2(mousePosition.x, mousePosition.y);
            }
        }
    }
}

using UnityEngine;

public class QuestTrigger : MonoBehaviour
{
    [SerializeField] private string initialPrompt = "테스트용 퀘스트 생성: 플레이어가 마을 입구에서 수상한 소리를 들었다.";
    
    void Start()
    {
        Debug.Log("QuestTrigger.Start 호출 - 퀘스트 생성 시도");
        QuestGenerator generator = GetComponent<QuestGenerator>();
        if (generator == null)
            generator = FindObjectOfType<QuestGenerator>();

        if (generator == null)
        {
            Debug.LogError("QuestGenerator를 찾을 수 없음. 같은 GameObject에 추가하거나 씬에 배치하세요.");
            return;
        }

        generator.GenerateQuest(initialPrompt);
    }
}
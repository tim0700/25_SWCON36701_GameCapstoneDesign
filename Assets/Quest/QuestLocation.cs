using UnityEngine;

[RequireComponent(typeof(BoxCollider2D))]
public class QuestLocation : MonoBehaviour
{
    public string entityId;

    public enum QuestEventType { GOTO, KILL, DUNGEON }
    public QuestEventType eventType = QuestEventType.GOTO;

    private void OnMouseDown()
    {
        GameObject player = GameObject.FindWithTag("Player");
        if (player == null)
        {
            Debug.LogError("씬에 'Player' 태그를 가진 오브젝트가 없습니다!");
            return;
        }

        // 플레이어를 이 오브젝트의 위치로 이동시킴
        player.transform.position = transform.position;

        string eventTypeString = eventType.ToString(); // "GOTO", "KILL", "DUNGEON"

        Debug.Log($"{player.name}가 {this.name}({entityId}) 위치로 이동했습니다. 이벤트 타입: {eventTypeString}");
        QuestStartTester.Instance.NotifyEvent(eventTypeString, entityId);
    }
}
using UnityEngine;

[RequireComponent(typeof(BoxCollider2D))]
public class QuestLocation : MonoBehaviour
{
    public string entityId;

    public enum QuestEventType { GOTO, KILL, DUNGEON }
    public QuestEventType eventType = QuestEventType.GOTO;


}
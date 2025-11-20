// QuestStartTester.cs
using UnityEngine;
using Newtonsoft.Json;
using System.Collections.Generic;
using TMPro; 

public class QuestStartTester : MonoBehaviour
{
    public static QuestStartTester Instance;

    public bool isQuestInProgress => currentQuest != null;

    [Header("UI & Game Objects")]
    public TextMeshProUGUI dialogueText;
    public TextMeshProUGUI objectiveText;

    [Header("Local Test Mode")]
    public bool useTestJsonOnStart = true;

    [TextArea(15, 30)]
    public string questJsonString;

    private QuestData currentQuest;
    private int currentStepIndex;

    public string questgiverNpcId;

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    void Start()
    {
        if (useTestJsonOnStart && !string.IsNullOrEmpty(questJsonString))
        {
            Debug.LogWarning("--- �׽�Ʈ ���� ����Ʈ ���� ---");
            StartQuestFromJson(questJsonString);
        }
        else
        {
            Debug.Log("--- ���� ��� ���� ���� ---");
        }
    }

    public void StartQuestFromJson(string json)
    {
        try
        {
            currentQuest = JsonConvert.DeserializeObject<QuestData>(json);
            currentStepIndex = 0;

            StartStep(currentStepIndex);
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"����Ʈ �Ľ� ����: {ex.Message}");
        }
    }

    private void StartStep(int stepIndex)
    {
        if (currentQuest == null || stepIndex >= currentQuest.QuestSteps.Count)
        {
            Debug.Log("����Ʈ�� ��� �ܰ踦 �Ϸ��߽��ϴ�!");
            dialogueText.text = "Quest Complete!";
            objectiveText.text = "";
            currentQuest = null; 
            return;
        }

        QuestStep step = currentQuest.QuestSteps[stepIndex];

        objectiveText.text = step.DescriptionForPlayer;

        if (step.Dialogues.OnStart.Count > 0)
        {
            dialogueText.text = $"[{step.Dialogues.OnStart[0].SpeakerId}]: {step.Dialogues.OnStart[0].Line}";
        }
        else
        {
            dialogueText.text = ""; 
        }
    }

    public void NotifyEvent(string eventType, string eventId)
    {
        if (currentQuest == null) return;

        QuestStep currentStep = currentQuest.QuestSteps[currentStepIndex];

        bool typeMatch = false;

        // 1.  objective_type �� (GOTO, TALK, KILL, DUNGEON ��� ó��)
        if (currentStep.ObjectiveType.ToUpper() == eventType.ToUpper())
        {
            if (eventType == "TALK")
            {
                typeMatch = (currentStep.Details.TargetNpcId == eventId);
            }
            else if (eventType == "GOTO")
            {
                typeMatch = (currentStep.Details.TargetLocationId == eventId);
            }
            else if (eventType == "KILL") // ���� óġ
            {
                typeMatch = (currentStep.Details.TargetMonsterId == eventId);
            }
            else if (eventType == "DUNGEON") // ���� Ŭ����
            {
                typeMatch = (currentStep.Details.TargetDungeonId == eventId);
            }
        }

        if (typeMatch)
        {
            // 2.  �Ϸ� �α׸� Ÿ�Կ� �°� ����
            if (eventType == "KILL")
            {
                Debug.Log($"��ǥ �޼�: ���� '{eventId}'�� óġ�߽��ϴ�.");
            }
            else if (eventType == "DUNGEON")
            {
                Debug.Log($"��ǥ �޼�: ���� '{eventId}'�� Ŭ�����߽��ϴ�.");
            }
            else
            {
                Debug.Log($"��ǥ �޼�: {eventType} - {eventId}");
            }

            CompleteStep(currentStepIndex);
        }
        else
        {
            // 3. ���� �޽��� ��ȭ
            string requiredDetail = "ID_UNKNOWN";
            if (currentStep.ObjectiveType == "TALK") requiredDetail = currentStep.Details.TargetNpcId;
            else if (currentStep.ObjectiveType == "GOTO") requiredDetail = currentStep.Details.TargetLocationId;
            else if (currentStep.ObjectiveType == "KILL") requiredDetail = currentStep.Details.TargetMonsterId;
            else if (currentStep.ObjectiveType == "DUNGEON") requiredDetail = currentStep.Details.TargetDungeonId;

            Debug.Log($"�߸��� Ŭ��: (�ʿ�: {currentStep.ObjectiveType} - {requiredDetail}), (Ŭ��: {eventType} - {eventId})");
        }
    }
    // ���� �ܰ踦 �Ϸ��ϰ� ���� �ܰ�� �Ѿ�� �Լ�
    private void CompleteStep(int stepIndex)
    {
        QuestStep step = currentQuest.QuestSteps[stepIndex];

        // 1. GOTO Ÿ���� ���, on_complete ��� ���
        if (step.ObjectiveType == "GOTO" && step.Dialogues.OnComplete.Count > 0)
        {
            dialogueText.text = $"[{step.Dialogues.OnComplete[0].SpeakerId}]: {step.Dialogues.OnComplete[0].Line}";
        }

        // 2. ���� �ܰ�� �ε��� ����
        currentStepIndex++;

        // 3. (��� ��� ��) ���� �ܰ� ����
        Invoke("StartNextStep", 1.5f); // 1.5�� ���
    }

    private void StartNextStep()
    {
        StartStep(currentStepIndex);
    }
}
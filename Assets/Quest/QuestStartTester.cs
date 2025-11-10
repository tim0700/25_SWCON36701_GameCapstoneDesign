// QuestStartTester.cs
using UnityEngine;
using Newtonsoft.Json;
using System.Collections.Generic;
using TMPro; 

public class QuestStartTester : MonoBehaviour
{
    public static QuestStartTester Instance;

    [Header("UI & Game Objects")]
    public TextMeshProUGUI dialogueText;
    public TextMeshProUGUI objectiveText;

    [Header("Local Test Mode")]
    public bool useTestJsonOnStart = true;

    [TextArea(15, 30)]
    public string questJsonString;

    private QuestData currentQuest;
    private int currentStepIndex;

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    void Start()
    {
        if (useTestJsonOnStart && !string.IsNullOrEmpty(questJsonString))
        {
            Debug.LogWarning("--- 테스트 모드로 퀘스트 시작 ---");
            StartQuestFromJson(questJsonString);
        }
        else
        {
            Debug.Log("--- 서버 대기 모드로 시작 ---");
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
            Debug.LogError($"퀘스트 파싱 오류: {ex.Message}");
        }
    }

    private void StartStep(int stepIndex)
    {
        if (currentQuest == null || stepIndex >= currentQuest.QuestSteps.Count)
        {
            Debug.Log("퀘스트의 모든 단계를 완료했습니다!");
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

        // 1.  objective_type 비교 (GOTO, TALK, KILL, DUNGEON 모두 처리)
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
            else if (eventType == "KILL") // 몬스터 처치
            {
                typeMatch = (currentStep.Details.TargetMonsterId == eventId);
            }
            else if (eventType == "DUNGEON") // 던전 클리어
            {
                typeMatch = (currentStep.Details.TargetDungeonId == eventId);
            }
        }

        if (typeMatch)
        {
            // 2.  완료 로그를 타입에 맞게 변경
            if (eventType == "KILL")
            {
                Debug.Log($"목표 달성: 몬스터 '{eventId}'를 처치했습니다.");
            }
            else if (eventType == "DUNGEON")
            {
                Debug.Log($"목표 달성: 던전 '{eventId}'를 클리어했습니다.");
            }
            else
            {
                Debug.Log($"목표 달성: {eventType} - {eventId}");
            }

            CompleteStep(currentStepIndex);
        }
        else
        {
            // 3. 오류 메시지 상세화
            string requiredDetail = "ID_UNKNOWN";
            if (currentStep.ObjectiveType == "TALK") requiredDetail = currentStep.Details.TargetNpcId;
            else if (currentStep.ObjectiveType == "GOTO") requiredDetail = currentStep.Details.TargetLocationId;
            else if (currentStep.ObjectiveType == "KILL") requiredDetail = currentStep.Details.TargetMonsterId;
            else if (currentStep.ObjectiveType == "DUNGEON") requiredDetail = currentStep.Details.TargetDungeonId;

            Debug.Log($"잘못된 클릭: (필요: {currentStep.ObjectiveType} - {requiredDetail}), (클릭: {eventType} - {eventId})");
        }
    }
    // 현재 단계를 완료하고 다음 단계로 넘어가는 함수
    private void CompleteStep(int stepIndex)
    {
        QuestStep step = currentQuest.QuestSteps[stepIndex];

        // 1. GOTO 타입인 경우, on_complete 대사 출력
        if (step.ObjectiveType == "GOTO" && step.Dialogues.OnComplete.Count > 0)
        {
            dialogueText.text = $"[{step.Dialogues.OnComplete[0].SpeakerId}]: {step.Dialogues.OnComplete[0].Line}";
        }

        // 2. 다음 단계로 인덱스 증가
        currentStepIndex++;

        // 3. (잠시 대기 후) 다음 단계 시작
        Invoke("StartNextStep", 1.5f); // 1.5초 대기
    }

    private void StartNextStep()
    {
        StartStep(currentStepIndex);
    }
}
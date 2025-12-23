using UnityEngine;
using UnityEngine.UI;
using System;

public class PlayerInputHandler : MonoBehaviour
{
    private InputField textInput;
    
    private string inputString = null;
    private bool isInputting = false;
    

    private void Awake()
    {
        textInput = GetComponentInChildren<InputField>();
    }

    private void Start()
    {
        // 초기에는 입력 UI 비활성화
        textInput.gameObject.SetActive(false);
    }

    private void Update()
    {
        // 입력 중일 때만 처리
        if (isInputting)
        {
            HandleInput();
        }
    }

    public void StartPlayerInput()
    {
        Debug.Log("플레이어 입력 시작");
        
        // UI 활성화
        textInput.gameObject.SetActive(true);
        textInput.text = ""; // 기존 텍스트 초기화
        textInput.ActivateInputField(); // 입력 필드에 포커스 설정
        
        // 입력 상태 활성화
        isInputting = true;
        
        // 커서 비활성화
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    private void HandleInput()
    {
        // 엔터 키로 입력 완료
        if (Input.GetKeyDown(KeyCode.Return))
        {
            CompleteInput();
        }
        
        // ESC 키로 입력 취소
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            CancelInput();
        }
    }

    private void CompleteInput()
    {
        inputString = textInput.text;
        
        Debug.Log("입력 완료: " + inputString);
                
        // UI 및 상태 정리
        EndInput();
    }


    private void CancelInput()
    {
        Debug.Log("입력 취소");
        
        // UI 및 상태 정리
        EndInput();
    }


    private void EndInput()
    {
        // UI 비활성화
        textInput.gameObject.SetActive(false);
        
        // 입력 상태 비활성화
        isInputting = false;
        
        // 커서 잠금 해제
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    public bool IsInputting => isInputting;
    public string GetLastInput => inputString;
}

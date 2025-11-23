// DialogueInputPanel.cs
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;

/// <summary>
/// UI component for capturing player dialogue input before quest generation.
/// Validates input length and provides submit/skip options.
/// </summary>
public class DialogueInputPanel : MonoBehaviour
{
    [Header("UI Components")]
    public CanvasGroup canvasGroup;  // NEW: For visibility control
    public TMP_InputField dialogueInput;
    public Button submitButton;
    public Button skipButton;
    public TextMeshProUGUI validationText;
    
    [Header("Validation Settings")]
    public int minLength = 5;
    public int maxLength = 200;
    
    [Header("UI Text")]
    public string placeholderText = "What do you need help with?";
    public string tooShortMessage = "Please enter at least {0} characters.";
    public string tooLongMessage = "Maximum {0} characters allowed.";
    
    private Action<string> onDialogueSubmittedCallback;
    private string currentNpcId;
    
    void Awake()
    {
        // Initialize panel as hidden using CanvasGroup
        if (canvasGroup != null)
        {
            canvasGroup.alpha = 0f;
            canvasGroup.interactable = false;
            canvasGroup.blocksRaycasts = false;
        }
        
        // Setup button listeners
        if (submitButton != null)
        {
            submitButton.onClick.AddListener(OnSubmitClicked);
        }
        
        if (skipButton != null)
        {
            skipButton.onClick.AddListener(OnSkipClicked);
        }
        
        // Setup input field
        if (dialogueInput != null)
        {
            dialogueInput.characterLimit = maxLength;
            
            // Set placeholder text
            if (dialogueInput.placeholder != null)
            {
                TextMeshProUGUI placeholder = dialogueInput.placeholder as TextMeshProUGUI;
                if (placeholder != null)
                {
                    placeholder.text = placeholderText;
                }
            }
            
            // Listen for input changes to clear validation errors
            dialogueInput.onValueChanged.AddListener(OnInputChanged);
        }
        
        // Hide validation text initially
        if (validationText != null)
        {
            validationText.gameObject.SetActive(false);
        }
    }
    
    /// <summary>
    /// Shows the dialogue input panel and sets up the callback.
    /// </summary>
    /// <param name="npcId">ID of the NPC being interacted with</param>
    /// <param name="callback">Callback to invoke when dialogue is submitted or skipped</param>
    public void ShowPanel(string npcId, Action<string> callback)
    {
        currentNpcId = npcId;
        onDialogueSubmittedCallback = callback;
        
        // Reset UI state
        if (dialogueInput != null)
        {
            dialogueInput.text = "";
        }
        
        if (validationText != null)
        {
            validationText.gameObject.SetActive(false);
        }
        
        // Show panel using CanvasGroup
        if (canvasGroup != null)
        {
            canvasGroup.alpha = 1f;
            canvasGroup.interactable = true;
            canvasGroup.blocksRaycasts = true;
        }
        
        // Focus input field
        if (dialogueInput != null)
        {
            dialogueInput.Select();
            dialogueInput.ActivateInputField();
        }
        
        Debug.Log($"[DialogueInputPanel] Shown for NPC: {npcId}");
    }
    
    /// <summary>
    /// Hides the dialogue input panel.
    /// </summary>
    public void HidePanel()
    {
        if (canvasGroup != null)
        {
            canvasGroup.alpha = 0f;
            canvasGroup.interactable = false;
            canvasGroup.blocksRaycasts = false;
        }
        
        Debug.Log("[DialogueInputPanel] Hidden");
    }
    
    /// <summary>
    /// Called when the Submit button is clicked.
    /// Validates input and invokes callback if valid.
    /// </summary>
    private void OnSubmitClicked()
    {
        if (dialogueInput == null) return;
        
        string dialogue = dialogueInput.text.Trim();
        
        // Validate dialogue length
        if (dialogue.Length < minLength)
        {
            ShowValidationError(string.Format(tooShortMessage, minLength));
            return;
        }
        
        if (dialogue.Length > maxLength)
        {
            ShowValidationError(string.Format(tooLongMessage, maxLength));
            return;
        }
        
        // Valid input - invoke callback
        Debug.Log($"[DialogueInputPanel] Dialogue submitted: {dialogue}");
        HidePanel();
        
        if (onDialogueSubmittedCallback != null)
        {
            onDialogueSubmittedCallback.Invoke(dialogue);
        }
    }
    
    /// <summary>
    /// Called when the Skip button is clicked.
    /// Invokes callback with empty string.
    /// </summary>
    private void OnSkipClicked()
    {
        Debug.Log("[DialogueInputPanel] Dialogue skipped");
        HidePanel();
        
        if (onDialogueSubmittedCallback != null)
        {
            onDialogueSubmittedCallback.Invoke("");
        }
    }
    
    /// <summary>
    /// Called when input field value changes.
    /// Clears validation errors.
    /// </summary>
    private void OnInputChanged(string value)
    {
        if (validationText != null && validationText.gameObject.activeSelf)
        {
            validationText.gameObject.SetActive(false);
        }
    }
    
    /// <summary>
    /// Shows a validation error message.
    /// </summary>
    private void ShowValidationError(string message)
    {
        if (validationText != null)
        {
            validationText.text = message;
            validationText.gameObject.SetActive(true);
        }
        
        Debug.LogWarning($"[DialogueInputPanel] Validation error: {message}");
    }
    
    void OnDestroy()
    {
        // Clean up listeners
        if (submitButton != null)
        {
            submitButton.onClick.RemoveListener(OnSubmitClicked);
        }
        
        if (skipButton != null)
        {
            skipButton.onClick.RemoveListener(OnSkipClicked);
        }
        
        if (dialogueInput != null)
        {
            dialogueInput.onValueChanged.RemoveListener(OnInputChanged);
        }
    }
}

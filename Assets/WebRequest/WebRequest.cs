using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class WebRequest : MonoBehaviour
{
    // localhost Flask 엔드포인트 (에디터에서 테스트할 때)
    [SerializeField] private string apiUrl = "http://127.0.0.1:5000/generate_quest";
    [SerializeField] private string accessToken = "";
    [SerializeField] private bool runGetRequest = false;

    void Start()
    {
        Debug.Log("RestApiExample.Start called on GameObject: " + gameObject.name + " active=" + gameObject.activeInHierarchy + " enabled=" + enabled);

        if (runGetRequest)
            StartCoroutine(GetRequest(apiUrl));

        string jsonBody = "{\"prompt\":\"Hello from Unity\"}";
        Debug.Log("Posting to: " + apiUrl + " body: " + jsonBody);
        StartCoroutine(PostRequest(apiUrl, jsonBody));
    } 

    IEnumerator GetRequest(string url)
    {
        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();

            string[] pages = url.Split('/');
            int page = pages.Length - 1;

            if (webRequest.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(pages[page] + ": Error: " + webRequest.error);
            }
            else
            {
                Debug.Log(pages[page] + ":\nReceived: " + webRequest.downloadHandler.text);
            }
        }
    }

    IEnumerator PostRequest(string url, string jsonData)
    {
        Debug.Log("PostRequest started");
        var request = new UnityWebRequest(url, "POST");
        byte[] bodyRaw = new System.Text.UTF8Encoding().GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        Debug.Log("PostRequest completed, result: " + request.result + " code: " + request.responseCode + " error: " + request.error);
        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.Log("Error: " + request.error + " body: " + request.downloadHandler.text);
        }
        else
        {
            Debug.Log("Received: " + request.downloadHandler.text);
        }
    }
}
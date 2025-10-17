using UnityEngine;

public class PlayerController : MonoBehaviour
{
    // 타겟 옆으로 이동할 때의 거리 오프셋
    public float offset = 1.5f;

    void Update()
    {
        // 마우스 왼쪽 버튼 클릭 감지
        if (Input.GetMouseButtonDown(0))
        {
            // 마우스 클릭 위치를 월드 좌표로 변환
            Vector2 mousePosition = Camera.main.ScreenToWorldPoint(Input.mousePosition);

            // 클릭한 위치에 콜라이더가 있는지 확인하기 위해 Ray 발사
            RaycastHit2D hit = Physics2D.Raycast(mousePosition, Vector2.zero);

            // 만약 콜라이더에 맞았다면 (무언가를 클릭했다면)
            if (hit.collider != null)
            {
                // 클릭한 오브젝트에서 CharacterInfo 컴포넌트를 가져옴
                CharacterInfo targetCharacter = hit.collider.GetComponent<CharacterInfo>();

                // CharacterInfo 컴포넌트가 있다면 (타겟 캐릭터를 클릭했다면)
                if (targetCharacter != null)
                {
                    // 타겟 캐릭터 옆으로 플레이어 위치 이동
                    // 타겟의 오른쪽에 자리를 잡도록 위치 설정
                    Vector2 targetPosition = hit.collider.transform.position;
                    transform.position = new Vector2(targetPosition.x + offset, targetPosition.y);

                    // 타겟 캐릭터의 ID를 콘솔에 출력
                    Debug.Log("Clicked Character ID: " + targetCharacter.characterID);
                }
            }
            // 콜라이더에 맞지 않았다면 (배경을 클릭했다면)
            else
            {
                // 클릭한 월드 좌표로 플레이어 위치를 바로 이동
                transform.position = new Vector2(mousePosition.x, mousePosition.y);
            }
        }
    }
}

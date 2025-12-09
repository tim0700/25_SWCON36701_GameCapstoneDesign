using UnityEngine;

/// <summary>
/// 플레이어를 부드럽게 따라가는 카메라 컨트롤러
/// </summary>
public class CameraFollow : MonoBehaviour
{
    [Header("Target")]
    [Tooltip("카메라가 따라갈 대상 (플레이어)")]
    public Transform target;

    [Header("Follow Settings")]
    [Tooltip("카메라 이동 부드러움 정도 (0~1, 낮을수록 부드러움)")]
    [Range(0f, 1f)]
    public float smoothSpeed = 0.125f;
    
    [Tooltip("카메라와 플레이어 사이의 오프셋")]
    public Vector3 offset = new Vector3(0f, 0f, -10f);

    [Header("Map Bounds (Optional)")]
    [Tooltip("맵 경계 제한 사용 여부 (맵 밖이 보이지 않도록)")]
    public bool useMapBounds = false;
    
    [Tooltip("맵의 최소 위치 (왼쪽 아래 모서리)")]
    public Vector2 mapMinBounds = new Vector2(-10f, -10f);
    
    [Tooltip("맵의 최대 위치 (오른쪽 위 모서리)")]
    public Vector2 mapMaxBounds = new Vector2(10f, 10f);
    
    [Header("Auto Calculate Bounds")]
    [Tooltip("Tilemap Collider를 기준으로 자동 계산")]
    public bool autoCalculateBounds = false;
    
    [Tooltip("자동 계산할 Tilemap GameObject (Ground 레이어 등)")]
    public GameObject mapTilemap;

    [Header("Look Ahead (Optional)")]
    [Tooltip("플레이어가 움직이는 방향을 미리 봄")]
    public bool useLookAhead = false;
    
    [Tooltip("Look ahead 거리")]
    public float lookAheadDistance = 2f;
    
    [Tooltip("Look ahead 부드러움")]
    public float lookAheadSpeed = 2f;

    private Vector3 currentVelocity;
    private Vector3 lookAheadPos;
    private Camera cam;
    private float cameraHalfWidth;
    private float cameraHalfHeight;

    void Start()
    {
        // 카메라 컴포넌트 가져오기
        cam = GetComponent<Camera>();
        
        // 자동 경계 계산
        if (autoCalculateBounds && mapTilemap != null)
        {
            CalculateMapBounds();
        }
        
        // 카메라 뷰포트 크기 계산
        UpdateCameraSize();
    }

    void LateUpdate()
    {
        // 타겟이 설정되지 않았으면 실행하지 않음
        if (target == null)
        {
            Debug.LogWarning("CameraFollow: Target이 설정되지 않았습니다!");
            return;
        }

        // 목표 위치 계산
        Vector3 desiredPosition = target.position + offset;

        // Look Ahead 기능 (선택사항)
        if (useLookAhead)
        {
            Rigidbody2D targetRb = target.GetComponent<Rigidbody2D>();
            if (targetRb != null && targetRb.linearVelocity.magnitude > 0.1f)
            {
                Vector3 lookAheadTarget = targetRb.linearVelocity.normalized * lookAheadDistance;
                lookAheadPos = Vector3.Lerp(lookAheadPos, lookAheadTarget, Time.deltaTime * lookAheadSpeed);
                desiredPosition += lookAheadPos;
            }
        }

        // 맵 경계 제한 (카메라 뷰포트를 고려하여 맵 밖이 안보이게)
        if (useMapBounds && cam != null)
        {
            // 카메라 크기 업데이트 (orthographic size가 변경될 수 있으므로)
            UpdateCameraSize();
            
            // 카메라가 맵 밖을 보지 않도록 경계 계산
            float clampedX = Mathf.Clamp(
                desiredPosition.x,
                mapMinBounds.x + cameraHalfWidth,
                mapMaxBounds.x - cameraHalfWidth
            );
            
            float clampedY = Mathf.Clamp(
                desiredPosition.y,
                mapMinBounds.y + cameraHalfHeight,
                mapMaxBounds.y - cameraHalfHeight
            );
            
            desiredPosition.x = clampedX;
            desiredPosition.y = clampedY;
        }

        // 부드러운 이동 (Lerp 사용)
        Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed);
        
        // 카메라 위치 업데이트
        transform.position = smoothedPosition;
    }

    /// <summary>
    /// 맵 경계를 Scene 뷰에서 시각화 (디버깅용)
    /// </summary>
    private void OnDrawGizmosSelected()
    {
        if (useMapBounds)
        {
            // 맵 전체 경계 (파란색)
            Gizmos.color = Color.cyan;
            DrawBounds(mapMinBounds, mapMaxBounds);
            
            // 카메라 이동 가능 범위 (초록색)
            if (cam != null)
            {
                UpdateCameraSize();
                Gizmos.color = Color.green;
                Vector2 cameraMinBounds = new Vector2(
                    mapMinBounds.x + cameraHalfWidth,
                    mapMinBounds.y + cameraHalfHeight
                );
                Vector2 cameraMaxBounds = new Vector2(
                    mapMaxBounds.x - cameraHalfWidth,
                    mapMaxBounds.y - cameraHalfHeight
                );
                DrawBounds(cameraMinBounds, cameraMaxBounds);
            }
        }
    }
    
    /// <summary>
    /// 사각형 경계 그리기 헬퍼 함수
    /// </summary>
    private void DrawBounds(Vector2 min, Vector2 max)
    {
        Vector3 bottomLeft = new Vector3(min.x, min.y, 0);
        Vector3 bottomRight = new Vector3(max.x, min.y, 0);
        Vector3 topLeft = new Vector3(min.x, max.y, 0);
        Vector3 topRight = new Vector3(max.x, max.y, 0);

        Gizmos.DrawLine(bottomLeft, bottomRight);
        Gizmos.DrawLine(bottomRight, topRight);
        Gizmos.DrawLine(topRight, topLeft);
        Gizmos.DrawLine(topLeft, bottomLeft);
    }
    
    /// <summary>
    /// 카메라 뷰포트 크기 계산 (Orthographic)
    /// </summary>
    private void UpdateCameraSize()
    {
        if (cam == null) return;
        
        cameraHalfHeight = cam.orthographicSize;
        cameraHalfWidth = cameraHalfHeight * cam.aspect;
    }
    
    /// <summary>
    /// Tilemap의 경계를 자동으로 계산
    /// </summary>
    private void CalculateMapBounds()
    {
        if (mapTilemap == null) return;
        
        // Tilemap 또는 Collider에서 경계 가져오기
        Renderer renderer = mapTilemap.GetComponent<Renderer>();
        if (renderer != null)
        {
            Bounds bounds = renderer.bounds;
            mapMinBounds = bounds.min;
            mapMaxBounds = bounds.max;
            //Debug.Log($"맵 경계 자동 계산 완료: Min={mapMinBounds}, Max={mapMaxBounds}");
        }
        else
        {
            //Debug.LogWarning("Tilemap Renderer를 찾을 수 없습니다. 수동으로 경계를 설정하세요.");
        }
    }

    /// <summary>
    /// 카메라를 즉시 타겟 위치로 이동 (씬 시작 시 유용)
    /// </summary>
    public void SnapToTarget()
    {
        if (target != null)
        {
            transform.position = target.position + offset;
        }
    }
}

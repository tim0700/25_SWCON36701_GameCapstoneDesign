# 🎮 NPC 캐릭터 시트 생성기

AI를 사용하여 게임용 NPC 캐릭터를 자동 생성하는 FastAPI 백엔드 서버입니다.

## ✨ 주요 기능

- **AI 기반 생성**: Google Gemini 2.5 Pro를 사용한 고품질 캐릭터 생성
- **커스터마이징**: 시스템 프롬프트와 JSON 스키마를 자유롭게 수정 가능
- **RESTful API**: FastAPI 기반의 간편한 HTTP API
- **검증 시스템**: Pydantic을 통한 다층 데이터 검증
- **크로스 플랫폼**: Windows, Linux, macOS 모두 지원

## 📁 프로젝트 구조

```
claude_captstone/
├── app/                          # FastAPI 애플리케이션
│   ├── api/                      # API 라우트
│   ├── core/                     # 핵심 유틸리티
│   ├── models/                   # 데이터 모델
│   ├── services/                 # 비즈니스 로직
│   └── templates/                # 프롬프트 & 스키마
│       ├── system_prompt.txt     # 👈 AI 시스템 프롬프트 (수정 가능)
│       └── character_sheet_schema.json  # 👈 출력 JSON 구조 (수정 가능)
├── data/npcs/                    # 생성된 캐릭터 저장 폴더
├── requirements.txt              # Python 패키지 목록
├── .env.example                  # 환경변수 예시
└── README_KR.md                  # 이 문서

```

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.8 이상
- Google Cloud 계정 (Vertex AI API 활성화)
- 서비스 계정 JSON 키 파일

### 1. 설치

#### Linux/Mac:
```bash
# 저장소 클론 (또는 폴더 복사)
cd /path/to/claude_captstone

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

#### Windows:
```bash
# 저장소 클론 (또는 폴더 복사)
cd C:\path\to\claude_captstone

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # Linux/Mac
notepad .env  # Windows
```

**.env 파일 내용:**
```env
# Google Cloud 설정
GOOGLE_CLOUD_PROJECT=your-project-id          # Google Cloud 프로젝트 ID
GOOGLE_CLOUD_LOCATION=us-central1             # 리전 (Gemini 2.5 Pro 지원 리전)
GOOGLE_APPLICATION_CREDENTIALS=your-key.json  # 서비스 계정 키 파일 경로

# 모델 설정
GEMINI_MODEL=gemini-2.5-pro                   # 사용할 Gemini 모델
TEMPERATURE=0.7                                # 생성 온도 (0.0-1.0)
MAX_OUTPUT_TOKENS=8192                         # 최대 출력 토큰

# 애플리케이션 설정
TEMPLATES_DIR=app/templates                    # 템플릿 폴더
OUTPUT_DIR=data/npcs                          # 출력 폴더
```

### 3. 서버 실행

```bash
# 개발 모드로 실행 (자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 후 접속:
- **API 문서**: http://localhost:8000/docs
- **대체 문서**: http://localhost:8000/redoc

## 📖 사용 방법

### API 엔드포인트

#### 1. 캐릭터 생성
```http
POST /api/v1/generate-character-sheet
Content-Type: application/json

{
  "character_id": "npc_wandering_mage_elara",
  "seed_description": "지식을 찾아 떠도는 마법사. 까칠하지만 따뜻한 마음을 가졌다. 고대 유물의 단서를 쫓고 있다."
}
```

**응답:**
```json
{
  "success": true,
  "character_id": "npc_wandering_mage_elara",
  "file_path": "data/npcs/npc_wandering_mage_elara.json",
  "generated_at": "2025-11-02T19:45:00.123Z",
  "message": "Character sheet generated successfully"
}
```

#### 2. 캐릭터 조회
```http
GET /api/v1/character/npc_wandering_mage_elara
```

#### 3. 캐릭터 목록
```http
GET /api/v1/characters
```

#### 4. 캐릭터 삭제
```http
DELETE /api/v1/character/npc_wandering_mage_elara
```

### Unity에서 사용하기

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class NPCGenerator : MonoBehaviour
{
    private const string API_URL = "http://localhost:8000/api/v1/generate-character-sheet";

    [System.Serializable]
    public class NPCRequest
    {
        public string character_id;
        public string seed_description;
    }

    [System.Serializable]
    public class NPCResponse
    {
        public bool success;
        public string character_id;
        public string file_path;
    }

    public void GenerateNPC()
    {
        StartCoroutine(GenerateNPCCoroutine());
    }

    private IEnumerator GenerateNPCCoroutine()
    {
        NPCRequest request = new NPCRequest
        {
            character_id = "npc_village_elder",
            seed_description = "오랜 세월을 살아온 마을 장로. 현명하지만 어두운 과거를 숨기고 있다."
        };

        string json = JsonUtility.ToJson(request);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);

        using (UnityWebRequest www = new UnityWebRequest(API_URL, "POST"))
        {
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");

            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                NPCResponse response = JsonUtility.FromJson<NPCResponse>(www.downloadHandler.text);
                Debug.Log($"NPC 생성 완료: {response.file_path}");
            }
            else
            {
                Debug.LogError($"에러: {www.error}");
            }
        }
    }
}
```

## 🎨 커스터마이징

### 시스템 프롬프트 수정

`app/templates/system_prompt.txt` 파일을 편집하여 AI의 역할과 생성 규칙을 변경할 수 있습니다.

```txt
# Role
You are the Senior Narrative Designer AI for a medieval fantasy RPG.

# Mission
Generate rich, detailed NPC character sheets...
```

### JSON 스키마 수정

`app/templates/character_sheet_schema.json` 파일을 편집하여 출력 구조를 변경할 수 있습니다.

```json
{
  "type": "object",
  "properties": {
    "npc_id": { "type": "string" },
    "name": { "type": "string" },
    "age": { "type": "string" },
    ...
  }
}
```

**주의**: 스키마를 변경한 경우 `app/models/character_sheet.py`의 Pydantic 모델도 함께 수정해야 합니다.

## 🔧 Unity 프로젝트 통합

Unity 프로젝트에 백엔드를 통합하려면:

### 1. 폴더 구조
```
YourUnityProject/
├── Assets/                    # Unity 에셋
├── ProjectSettings/           # Unity 설정
└── Backend/                   # 👈 이 프로젝트 복사
    ├── app/
    ├── requirements.txt
    └── .env.example
```

### 2. .gitignore 업데이트

Unity 프로젝트의 `.gitignore` 파일에 다음 내용을 추가:

```gitignore
# ==================== Python Backend ====================
Backend/__pycache__/
Backend/**/__pycache__/
Backend/venv/
Backend/.env
Backend/*.json
!Backend/app/templates/*.json
Backend/data/
Backend/*.log
Backend/logs/
```

### 3. 팀원 설정

각 팀원은:
1. Git pull로 프로젝트 받기
2. `Backend/` 폴더에서 Python 환경 설정 (위의 설치 가이드 참조)
3. 자신의 Google Cloud 크리덴셜 파일을 `Backend/` 폴더에 배치
4. `.env` 파일 설정

### 4. 협업 방식

**옵션 A: 로컬 개발**
- 각 개발자가 자신의 PC에서 백엔드 서버 실행
- Unity에서 `http://localhost:8000` 사용

**옵션 B: 팀 공유**
- 한 명이 백엔드 서버 실행 (호스트)
- 다른 팀원들은 호스트의 IP로 접속
  ```csharp
  private const string API_URL = "http://192.168.1.100:8000/api/v1/...";
  ```

**옵션 C: 클라우드 배포**
- Google Cloud Run, AWS 등에 배포
- 모든 팀원이 배포된 URL 사용

## 🛠️ 문제 해결

### 1. `404 Model not found` 에러

**원인**: Gemini 2.5 Pro가 지원되지 않는 리전

**해결**:
```env
# .env 파일에서 리전 변경
GOOGLE_CLOUD_LOCATION=us-central1  # 또는 us-east1, europe-west1
```

지원 리전: `us-central1`, `us-east1`, `us-west1`, `europe-west1`, `asia-southeast1`

### 2. `Your default credentials were not found` 에러

**원인**: Google Cloud 크리덴셜 설정 오류

**해결**:
1. 서비스 계정 JSON 키 파일이 프로젝트 폴더에 있는지 확인
2. `.env` 파일에서 경로가 올바른지 확인:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=my-service-account-key.json
   ```
3. 상대 경로 사용 (파일이 프로젝트 루트에 있을 경우)

### 3. `422 Validation Error` 에러

**원인**: Pydantic 모델과 생성된 JSON 구조 불일치

**해결**:
- `app/templates/character_sheet_schema.json` 확인
- `app/models/character_sheet.py` 모델 구조 확인
- 두 파일의 필드가 일치하는지 확인

### 4. Unity에서 CORS 에러

**원인**: 브라우저 보안 정책 (Unity WebGL 빌드 시)

**해결**: FastAPI는 이미 CORS를 허용하도록 설정되어 있습니다. 문제가 지속되면 `app/main.py`에서 CORS 설정 확인.

### 5. 포트가 이미 사용 중

**해결**:
```bash
# 다른 포트 사용
uvicorn app.main:app --reload --port 8001

# Unity에서도 포트 변경
private const string API_URL = "http://localhost:8001/api/v1/...";
```

## 📋 Google Cloud 설정

### 1. 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 ID 기록

### 2. Vertex AI API 활성화

1. 좌측 메뉴 > "API 및 서비스" > "라이브러리"
2. "Vertex AI API" 검색
3. "사용 설정" 클릭

### 3. 서비스 계정 생성

1. 좌측 메뉴 > "IAM 및 관리자" > "서비스 계정"
2. "서비스 계정 만들기" 클릭
3. 이름 입력 (예: `npc-generator`)
4. 역할 선택: **Vertex AI User**
5. "완료" 클릭

### 4. JSON 키 다운로드

1. 생성된 서비스 계정 클릭
2. "키" 탭 선택
3. "키 추가" > "새 키 만들기"
4. JSON 형식 선택 후 "만들기"
5. 다운로드된 JSON 파일을 프로젝트 폴더로 이동

## 📚 추가 리소스

### API 문서
- 서버 실행 후: http://localhost:8000/docs
- ReDoc 형식: http://localhost:8000/redoc

### 프로젝트 구조 상세

- `app/api/routes/` - API 엔드포인트 정의
- `app/services/vertex_client.py` - Gemini API 클라이언트
- `app/services/template_manager.py` - 템플릿 로딩
- `app/services/prompt_builder.py` - 프롬프트 조합
- `app/services/validator.py` - 비즈니스 로직 검증
- `app/models/character_sheet.py` - Pydantic 데이터 모델

### 로그 확인

```bash
# 로그 파일 확인
cat logs/app.log

# 실시간 로그 모니터링
tail -f logs/app.log
```

## 🔐 보안 주의사항

### Git에 커밋하면 안 되는 것:

- ❌ `.env` 파일 (환경변수)
- ❌ `*.json` 서비스 계정 키 파일
- ❌ `data/npcs/` 생성된 캐릭터 파일
- ❌ `logs/` 로그 파일
- ❌ `venv/` 가상환경

`.gitignore` 파일이 이들을 자동으로 제외하지만, 실수로 추가하지 않도록 주의하세요.

### 크리덴셜 공유 방법

팀원들과 크리덴셜을 공유해야 한다면:
- ✅ 비밀번호 관리자 사용 (1Password, LastPass 등)
- ✅ 팀 드라이브 비공개 폴더
- ✅ 암호화된 메시지 앱
- ❌ 이메일, Slack, Discord 등 일반 메시징 (위험)

## 💡 팁

### 생성 품질 향상

1. **구체적인 설명**: seed_description에 구체적인 정보 제공
   ```json
   {
     "seed_description": "30대 여성 마법사. 불친절하지만 지식욕이 강함. 고대 도서관을 찾고 있음. 화상 흉터가 있음."
   }
   ```

2. **온도 조절**: `.env` 파일에서 `TEMPERATURE` 조정
   - `0.3-0.5`: 일관성 높음, 보수적
   - `0.7`: 균형 (기본값)
   - `0.9-1.0`: 창의적, 다양성 높음

3. **시스템 프롬프트 개선**: `app/templates/system_prompt.txt`에 상세한 규칙 추가

### 성능 최적화

- **온도 캐싱**: 템플릿은 자동으로 캐싱됨
- **병렬 생성**: 여러 캐릭터를 동시에 요청 가능
- **재시도 로직**: 실패 시 자동 재시도 (최대 3회)

## 📞 문의 및 지원

문제가 발생하면:
1. 로그 확인: `logs/app.log`
2. API 문서 확인: http://localhost:8000/docs
3. 이 가이드의 "문제 해결" 섹션 참조

## 📄 라이센스 및 기타

- **개발 환경**: Python 3.8+, FastAPI, Google Gemini 2.5 Pro
- **SDK 버전**: google-genai>=0.2.0 (2025년 최신 SDK)
- **크로스 플랫폼**: Windows, Linux, macOS 완전 지원

---

**즐거운 게임 개발 되세요! 🎮✨**

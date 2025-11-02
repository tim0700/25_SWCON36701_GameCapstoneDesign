# 🔑 환경변수 설정 가이드

`.env` 파일은 보안상 Git에 포함되지 않습니다. 각 팀원이 직접 설정해야 합니다.

## 1️⃣ .env 파일 생성

```bash
# Backend 폴더로 이동
cd Backend

# .env.example을 복사하여 .env 생성
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

## 2️⃣ Google Cloud 크리덴셜 받기

### 방법 A: 팀 리더에게 받기 (추천)

팀 리더가 다음 파일들을 공유합니다:
1. **서비스 계정 JSON 키 파일** (예: `my-project-xxxxx.json`)
2. **Google Cloud 프로젝트 ID**

**파일 받는 곳:**
- 팀 Google Drive 비공개 폴더
- Discord/Slack 직접 메시지
- 비밀번호 관리자

받은 JSON 파일을 `Backend/` 폴더에 저장하세요.

### 방법 B: 직접 발급받기

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 (또는 새로 생성)
3. "IAM 및 관리자" → "서비스 계정" 이동
4. "서비스 계정 만들기" 클릭
5. 역할: **Vertex AI User** 선택
6. JSON 키 다운로드
7. 다운로드한 파일을 `Backend/` 폴더에 저장

## 3️⃣ .env 파일 편집

```bash
# .env 파일 열기
notepad .env  # Windows
nano .env     # Linux/Mac
```

**수정할 내용:**

```env
# Google Cloud 설정 (필수)
GOOGLE_CLOUD_PROJECT=your-project-id          # 👈 팀 리더에게 받은 프로젝트 ID
GOOGLE_CLOUD_LOCATION=us-central1             # 👈 그대로 두기
GOOGLE_APPLICATION_CREDENTIALS=your-key.json  # 👈 다운로드한 JSON 파일명

# 모델 설정 (선택 사항)
GEMINI_MODEL=gemini-2.5-pro                   # 👈 그대로 두기
TEMPERATURE=0.7                                # 0.0-1.0 (창의성 조절)
MAX_OUTPUT_TOKENS=8192                         # 👈 그대로 두기

# 기타 설정 (선택 사항)
TEMPLATES_DIR=app/templates
OUTPUT_DIR=data/npcs
API_TIMEOUT=60
MAX_RETRIES=3
DEBUG=false
LOG_LEVEL=INFO
```

### 🔍 설정 값 설명

| 항목 | 설명 | 예시 |
|------|------|------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud 프로젝트 ID | `my-rpg-project-12345` |
| `GOOGLE_CLOUD_LOCATION` | 서버 리전 (Gemini 지원 지역) | `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | JSON 키 파일명 | `service-account-key.json` |
| `GEMINI_MODEL` | 사용할 AI 모델 | `gemini-2.5-pro` |
| `TEMPERATURE` | 생성 창의성 (낮을수록 일관성↑) | `0.7` |

## 4️⃣ 설정 확인

```bash
# Backend 폴더에서 가상환경 실행
cd Backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 서버 실행하여 테스트
uvicorn app.main:app --reload --port 8000
```

서버가 정상 실행되면:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## ❓ 자주 묻는 질문

### Q1: 프로젝트 ID를 모르겠어요
**A:** JSON 키 파일을 텍스트 에디터로 열면 `"project_id": "..."` 항목에서 확인 가능

```json
{
  "type": "service_account",
  "project_id": "my-rpg-project-12345",  👈 이것
  "private_key_id": "...",
  ...
}
```

### Q2: JSON 파일 경로를 어떻게 적나요?
**A:** 파일이 `Backend/` 폴더에 있다면 파일명만 적으면 됩니다:
```env
GOOGLE_APPLICATION_CREDENTIALS=my-key.json
```

하위 폴더에 있다면:
```env
GOOGLE_APPLICATION_CREDENTIALS=credentials/my-key.json
```

### Q3: "404 Model not found" 에러가 나요
**A:** 리전을 변경하세요:
```env
GOOGLE_CLOUD_LOCATION=us-central1  # 또는 us-east1, europe-west1
```

지원 리전: `us-central1`, `us-east1`, `us-west1`, `europe-west1`, `asia-southeast1`

### Q4: "Credentials not found" 에러가 나요
**A:**
1. JSON 파일이 `Backend/` 폴더에 있는지 확인
2. `.env` 파일의 파일명이 정확한지 확인
3. 파일명에 공백이나 특수문자가 없는지 확인

### Q5: 팀원들끼리 같은 계정을 써도 되나요?
**A:** 네, 개발 단계에서는 하나의 서비스 계정을 공유해도 됩니다. 단, 다음을 주의하세요:
- JSON 키 파일을 Git에 올리지 마세요 (`.gitignore`로 보호됨)
- 공개 채널(오픈 채팅)에 올리지 마세요
- 프로젝트 종료 후 키 폐기 고려

## 🔒 보안 주의사항

**절대 하지 말 것:**
- ❌ `.env` 파일을 Git에 커밋
- ❌ JSON 키 파일을 Git에 커밋
- ❌ 공개 채널에 크리덴셜 공유
- ❌ 스크린샷에 크리덴셜 포함

**해야 할 것:**
- ✅ `.env.example`은 Git에 커밋 (OK)
- ✅ 비공개 채널로 크리덴셜 공유
- ✅ 프로젝트 종료 후 키 폐기
- ✅ 각자 PC의 `Backend/` 폴더에만 보관

## 📋 체크리스트

설정을 완료했다면 체크하세요:

- [ ] `.env` 파일 생성 완료
- [ ] Google Cloud 프로젝트 ID 입력
- [ ] JSON 키 파일을 `Backend/` 폴더에 복사
- [ ] `.env`에서 JSON 파일명 설정
- [ ] 서버 실행 테스트 성공
- [ ] http://localhost:8000/docs 접속 확인

---

**문제가 해결되지 않으면 `README.md`의 "문제 해결" 섹션을 참조하세요.**

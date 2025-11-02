# ⚡ 빠른 시작 가이드 (5분)

NPC 캐릭터 생성기를 5분 안에 실행하는 방법입니다.

## 1️⃣ 설치 (2분)

```bash
# 가상환경 생성
python3 -m venv venv  # Windows: python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

## 2️⃣ 환경 설정 (2분)

```bash
# 환경변수 파일 생성
cp .env.example .env

# .env 파일 편집 (3가지만 수정, .env.example 참조)
nano .env  # Windows: notepad .env
```

**.env 파일에서 수정할 내용:**
```env
GOOGLE_CLOUD_PROJECT=your-project-id           # Google Cloud 프로젝트 ID
GOOGLE_CLOUD_LOCATION=us-central1              # 리전 (그대로 두면 됨)
GOOGLE_APPLICATION_CREDENTIALS=your-key.json   # 크리덴셜 파일명
```

**크리덴셜 파일 배치:**
- Google Cloud에서 다운로드한 JSON 키 파일을 이 폴더에 복사
- 파일명을 `.env`의 `GOOGLE_APPLICATION_CREDENTIALS`와 일치시키기

## 3️⃣ 실행 (1분)

```bash
# 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

서버가 실행되면:
- http://localhost:8001/docs 접속
- `POST /api/v1/generate-character-sheet` 클릭
- "Try it out" 클릭
- 예제 입력:

```json
{
  "character_id": "npc_test_mage",
  "seed_description": "불을 다루는 마법사. 성격이 급하지만 마음은 따뜻하다."
}
```

- "Execute" 클릭 → 캐릭터 생성 완료! 🎉

## ❓ 문제 발생 시

### "Model not found" 에러
→ `.env`에서 `GOOGLE_CLOUD_LOCATION=us-central1`로 변경

### "Credentials not found" 에러
→ 크리덴셜 JSON 파일이 프로젝트 폴더에 있는지 확인

### 그 외 문제
→ `README.md`의 "문제 해결" 섹션 참조

---

**상세 가이드**: `README.md` 참조

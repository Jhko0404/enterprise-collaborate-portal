# 🤖 Claude Code Guide - Enterprise AI Collaborate Portal

이 문서는 **Claude Code (또는 AI 코딩 어시스턴트)**가 이 레포지토리를 이해하고, 고객의 GCP 환경에 자율적으로 안전하고 빠르게 배포 및 운영할 수 있도록 돕는 지침서입니다.

---

## 📌 1. 프로젝트 개요 & 아키텍처 원칙

* **서비스명**: 엔터프라이즈 AI 협업 회의록 포털 (Enterprise AI Collaborate Portal)
* **기술 스택**:
  * Backend: Python 3.11, FastAPI, Pydantic, Uvicorn, FFmpeg
  * Frontend: Vanilla Modern HTML/JS/CSS (SPA), KST 시간 자동 포맷터
  * Cloud Infra: Google Cloud Run (비공개 서빙), Google Cloud API Gateway (공개 인그레스), GCS (미디어/보관소), Vertex AI (Gemini 3.7 Flash), Cloud Speech-to-Text (Chirp 2)
* **핵심 아키텍처 3대 원칙**:
  1. **GCS Direct Resumable Upload**: 브라우저에서 대용량 미디어(MP4, MOV 등)를 API Gateway를 거치지 않고 GCS로 직접 이어올려 Gateway의 32MB 페이로드 제한을 완전 우회합니다.
  2. **Zero-Transfer AI 추론**: GCS URI(`gs://...`)를 Vertex AI Gemini 3.7 Flash(`location='global'`)에 직접 전달하여 무손실 고속 화자 분리(Diarization) 및 회의록 생성을 수행합니다.
  3. **Zero-Trust 백엔드 보안**: Cloud Run은 외부 직접 호출이 차단(`--no-allow-unauthenticated`)되어 있으며, API Gateway의 서비스 계정(`agent-gateway-sa`) OIDC 토큰으로만 호출됩니다.

---

## 🚀 2. 자동 배포 지침 (Claude Code 실행 워크플로우)

사용자가 **"배포해줘"**, **"GCP에 올려줘"**, **"설치해줘"**라고 요청하면 다음 순서로 작업을 수행하세요:

### 1단계: 사전 환경 확인
```bash
# 1. 활성화된 GCP 계정 및 프로젝트 확인
gcloud auth list
gcloud config get-value project

# 2. .env 파일 존재 여부 확인 (없으면 .env.example 복사)
if [ ! -f .env ]; then cp .env.example .env; fi
```

### 2단계: 원클릭 통합 배포 스크립트 실행
```bash
# 통합 배포 스크립트 실행 (API 활성화, GCS 버킷 생성, Cloud Run, API Gateway 전체 일괄 배포)
./deploy/quickstart.sh
```
* **결과 확인**: 스크립트 마지막에 출력되는 `https://enterprise-agent-gateway-xxxx.uc.gateway.dev` 주소를 사용자에게 제공합니다.

---

## 💻 3. 로컬 개발 및 테스트 실행 지침

로컬에서 디버깅하거나 수정할 때:
```bash
# 1. 가상환경 및 패키지 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 로컬 서버 실행 (포트 9090)
./run_server.sh
```

---

## 📁 4. 주요 파일 및 디렉토리 맵

* `app/main.py`: FastAPI 메인 진입점 및 REST API 엔드포인트
* `app/services/gemini_service.py`: Vertex AI Gemini 3.7 Flash 연동 파이프라인
* `app/services/storage_service.py`: GCS Resumable Upload 세션 발급 로직
* `static/app.js`: 프론트엔드 UI 인터랙션, GCS 직접 청크 업로드, KST 시간 변환
* `static/index.html`: 메인 웹 UI
* `deploy/quickstart.sh`: 전체 원스톱 배포 스크립트
* `deploy/deploy_backend.sh`: Cloud Run 백엔드 단독 배포 스크립트
* `deploy/deploy_gateway.sh`: API Gateway 단독 배포 스크립트
* `deploy/openapi2-agentgateway.yaml`: API Gateway OpenAPI 2.0 스펙 정의

---

## 🛠️ 5. 트러블슈팅 지침

1. **GCS 업로드 시 HTTP 403 / CORS 에러**:
   - `storage_service.py`의 `create_resumable_upload_session`에 접속 브라우저의 `origin`이 올바르게 전달되는지 확인하세요.
2. **API Gateway 403 Forbidden**:
   - Gateway 전용 서비스 계정(`agent-gateway-sa`)에 Cloud Run의 `roles/run.invoker` 권한이 부여되어 있는지 확인하세요 (`./deploy/deploy_gateway.sh`가 자동 부여).
3. **타임존 문제**:
   - UI 시간은 `static/app.js`의 `formatKstDateTime()` 함수에 의해 KST(UTC+9)로 변환되어 표시됩니다.

# 🚀 02. 고객 환경 배포 및 운영 가이드 (Deployment & Operations Guide)

> **Enterprise AI 협업포털 고객사 설치, 설정, 배포 및 운영 매뉴얼**

---

## 1. 사전 필수 요구사항 (Prerequisites)

### 1.1. 시스템 환경 요구사항
* **운영체제**: Linux (Ubuntu 20.04+, Debian 11+ 권장), macOS, Windows WSL2
* **Python**: Python 3.10 이상 (Python 3.11 권장)
* **Google Cloud SDK (`gcloud`)**: 최신 버전 설치
* **FFmpeg**: (선택: 로컬 미디어 분할 테스트용) `sudo apt-get install -y ffmpeg`

### 1.2. GCP 프로젝트 및 IAM 권한 요구사항
배포를 실행하는 엔지니어 계정 또는 서비스 계정에 다음 IAM 역할이 부여되어 있어야 합니다:
* **Cloud Run 관리자** (`roles/run.admin`): 프라이빗 백엔드 컨테이너 서비스 배포 및 스케일링
* **API Gateway 관리자** (`roles/apigateway.admin`): 게이트웨이 및 라우팅 명세 등록
* **서비스 계정 관리자 / 사용자** (`roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountUser`): 전용 OIDC 인그레스 서비스 계정 생성 및 권한 위임
* **스토리지 관리자** (`roles/storage.admin`): 임시 미디어 버킷 생성 및 1일 수명주기(Lifecycle) 설정
* **Vertex AI 사용자** (`roles/aiplatform.user`): Gemini 3.7 Flash 멀티모달 모델 호출
* **Cloud Speech 클라이언트** (`roles/speech.client`): Cloud Speech-to-Text (Chirp 2) 호출
* **Cloud Build 편집자** (`roles/cloudbuild.builds.editor`): 컨테이너 이미지 자동 빌드

---

## 2. 로컬 가상화 환경 및 GCP 인증 구성 (Local Setup & Auth)

### 2.1. Python 가상환경(venv) 생성 및 활성화
```bash
# 1. 프로젝트 폴더로 이동
cd enterprise-collaborate-portal

# 2. 가상환경 생성
python3 -m venv .venv

# 3. 가상환경 활성화
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 4. 의존성 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2. Google Cloud 로그인 및 Application Default Credentials (ADC) 설정
```bash
# 1. gcloud CLI 콘솔 로그인
gcloud auth login

# 2. 로컬 테스트 및 API 호출용 애플리케이션 기본 자격증명(ADC) 획득
gcloud auth application-default login

# 3. 대상 GCP 프로젝트 설정
gcloud config set project YOUR_GCP_PROJECT_ID
```

---

## 3. 배포 방식 선택 (Deployment Methods)

### 옵션 1. 클로드 코드 (Claude Code / AI Agent) 대화형 10초 배포 (추천)
터미널에서 `claude` 실행 후 아래와 같이 요청:
```bash
> "현재 프로젝트를 GCP 프로젝트(YOUR_GCP_PROJECT_ID)의 us-central1 리전에 전체 배포해줘."
```
* Claude Code가 `CLAUDE.md` 가이드라인을 기반으로 환경 감지, API 활성화, 컨테이너 빌드, 게이트웨이 연동을 전자동 수행합니다.

### 옵션 2. 원클릭 통합 배포 (CLI One-Click)
```bash
./deploy/quickstart.sh YOUR_GCP_PROJECT_ID us-central1
```

---

## 4. 3-Step 상세 단계별 순차 배포 절차 (Step-by-Step Manual)

### Step 1. 고객 환경 초기화 (APIs, GCS 수명주기 버킷, .env 자동 구성)
```bash
# 문법: ./deploy/setup_customer_environment.sh [PROJECT_ID] [REGION]
./deploy/setup_customer_environment.sh YOUR_GCP_PROJECT_ID us-central1
```
* **수행 작업**:
  * 8개 필수 GCP API 자동 활성화 (`run`, `apigateway`, `aiplatform`, `speech`, `storage`, `cloudbuild` 등)
  * 임시 오디오 버킷(`gs://[PROJECT_ID]-meet-audio-temp`) 생성 및 1일 자동 파기(Lifecycle) 규칙 바인딩
  * `.env` 환경설정 파일 자동 생성

### Step 2. Cloud Run 프라이빗 백엔드 배포
```bash
./deploy/deploy_backend.sh YOUR_GCP_PROJECT_ID us-central1
```
* **수행 작업**:
  * Cloud Build를 통한 FFmpeg 포함 컨테이너 자동 빌드
  * 프라이빗 Cloud Run 서비스(`--no-allow-unauthenticated`, 2 vCPU, 4GiB, Concurrency 20, 1~20 자동 스케일링) 배포

### Step 3. Google Cloud API Gateway 배포
```bash
./deploy/deploy_gateway.sh YOUR_GCP_PROJECT_ID us-central1
```
* **수행 작업**:
  * API Gateway 전용 서비스 계정(`agent-gateway-sa`) 생성 및 Cloud Run Invoker 권한 부여
  * OpenAPI 2.0 라우팅 설정 등록 및 게이트웨이 롤아웃
  * 배포 완료 후 외부 접근 가능한 공용 URL(`https://YOUR_GATEWAY.gateway.dev`) 출력

---

## 4. 자체 진단 및 동작 검증 (Verification & Health Check)

### 4.1. 단위 테스트 5종 전수 검증 (100% Pass)
```bash
python3 tests/06_comprehensive_unit_test.py
```

### 4.2. API 헬스체크 및 실시간 상태 점검
```bash
# 1. 템플릿 목록 조회
curl -s "https://YOUR_GATEWAY.gateway.dev/api/v1/templates"

# 2. 회의록 보관함 목록 조회
curl -s "https://YOUR_GATEWAY.gateway.dev/api/v1/reports"

# 3. 회의록 및 비동기 STT 진행 상황 진단 스크립트 실행
./scripts/check_report.sh [리포트ID 또는 검색어]
```

---

## 5. 운영 및 모니터링 가이드 (Operations & Monitoring)

### 5.1. 실시간 로그 모니터링 (Cloud Logging)
```bash
# Cloud Run 실시간 로그 스트리밍
gcloud logging tail 'resource.type="cloud_run_revision" AND resource.labels.service_name="coway-meet-notes-service"' --project=YOUR_GCP_PROJECT_ID

# 특정 리포트의 STT 진행 로그 추적
gcloud logging read 'resource.type="cloud_run_revision" AND textPayload=~"[Cloud STT]"' --limit=30 --project=YOUR_GCP_PROJECT_ID
```

### 5.2. 트러블슈팅 가이드 (Troubleshooting)
* **Cloud Run Cold Start 시 회의록이 사라지는 경우**: 시스템에 내장된 GCS 영속 동기화 기능이 자동으로 `gs://[BUCKET]/metadata/reports_database.json`에서 복구합니다.
* **GCS 업로드 시 CORS 오류**: `./deploy/setup_customer_environment.sh`를 실행하여 버킷 CORS 설정을 최신화합니다.
* **Cloud STT 지연**: 15분 단위 청크가 10개 이상인 경우 동시 병렬 스레드(ThreadPoolExecutor)에 의해 분할 처리되므로 웹앱의 실시간 프로그레스 바를 통해 진행률을 모니터링합니다.

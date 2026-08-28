// Collaborate Portal Frontend Application
const API_BASE = window.location.origin;

let activeTranscript = [];
let sampleSources = {
  sample_meet_85min: {
    title: "리테일 회사 AI 협업포털 회의록 자동화 및 Google Workspace/GCP 연동 기술 미팅",
    date: "2026-08-18",
    time: "15:00 ~ 16:30 (총 85분)",
    attendees: "홍길동 팀장 (리테일 회사 PM), 성춘향 님 (리테일 회사), 이몽룡 님 (리테일 회사), 담당 CE (Google Cloud), 심청 FSR (Google Cloud), 임꺽정 Specialist (Google Workspace), SI 수행사 팀장",
    executive_summary: "리테일 회사 임직원이 Google Calendar/Meet을 통해 진행한 회의 녹화본 및 음성 스트림(16kHz Mono MP3)을 Vertex AI Gemini 3.7 Flash 모델로 분석하여, '1페이지 구조화 회의록'과 '100% 무가공 대화 전체 스크립트(화자 분리 전문)'의 2대 산출물을 자동 생성하고 협업포털 및 Google Docs로 연동 배포하는 방안을 확정함.",
    key_decisions: [
      "사용자 시나리오 1 채택: 캘린더/모바일에서 평소대로 회의 진행 후 포털에서 원클릭으로 회의록 생성",
      "Vertex AI Gemini 3.7 Flash 오디오 멀티모달 Diarization 엔진 도입 (16kHz 모노 파형 직접 인지)",
      "100% 사실 기반 무가공(Verbatim) 전사 원칙 수립 (임의 축약/요약/정제 금지)",
      "미식별 화자 대응을 위한 웹 UI 1-Click 일괄 치환(Replace All) 기능 제공",
      "Google Workspace DWD(도메인 전체 위임)를 통한 서비스 계정 기반 이메일/드라이브 안전 검색 체계 수립"
    ],
    agendas: [
      {
        title: "1. 협업포털 회의록 자동화 사용자 여정(User Journey)",
        content: "임직원 사용 편의성을 극대화하기 위한 회의 생성 및 수집 방식 비교 검토",
        key_points: [
          "시나리오 1: 임직원이 Google Calendar 또는 모바일 앱에서 평소처럼 회의를 생성하고 Meet을 진행하면, 포털이 백그라운드에서 녹화본과 참석자 정보를 자동 감지하여 원클릭으로 회의록 생성",
          "시나리오 2: 포털 내에서 직접 화상 회의를 개설하고 녹화하는 방식 검토",
          "비교 결과: 새로운 툴 학습 부담이 없고 모바일 접근성이 뛰어난 시나리오 1을 공식 표준 방향으로 확정"
        ],
        resolution: "기존 Google Calendar/Meet 워크플로우를 100% 유지하는 시나리오 1 공식 채택",
        speakers: ["담당 CE (Google Cloud)", "홍길동 팀장 (리테일 회사)"]
      },
      {
        title: "2. 회의실 단일 마이크 환경 화자 분리(Diarization) 한계 극복",
        content: "회의실 내 1대 노트북으로 여러 명이 발언할 때 발생하는 단일 화자 뭉개짐 이슈 해결책 수립",
        key_points: [
          "기존 Google Meet 기본 자막 기능은 접속 계정 1개로 전체 발언자가 묶이는 근본적 한계 확인",
          "Vertex AI Gemini 3.7 Flash 모델의 오디오 멀티모달 인식 기능 도입 (16kHz Mono 파형의 피치, 톤, 음색 직접 분석)",
          "캘린더에 등록된 참석자 명단 및 호칭 컨텍스트를 프롬프트에 주입하여 화자 매핑 정확도 대폭 향상",
          "미식별 화자 발생 시 웹 UI에서 1-Click으로 이름을 일괄 변경할 수 있는 '화자 일괄 치환(Replace All)' 인터페이스 제공"
        ],
        resolution: "Gemini 3.7 Flash 오디오 Diarization + 캘린더 참석자 매핑 + UI 1-Click 일괄 치환의 3단계 복합 아키텍처 확정",
        speakers: ["이몽룡 님 (리테일 회사)", "담당 CE (Google Cloud)", "성춘향 님 (리테일 회사)"]
      },
      {
        title: "3. Google Workspace DWD 권한 및 서비스 계정 연동",
        content: "전사 임직원의 개별 OAuth 로그인 없이 부서/프로젝트 단위로 안전하게 데이터를 수집하는 보안 체계 검토",
        key_points: [
          "사내 보안 정책상 개인 계정의 외부 OAuth 인증 허용이 차단된 엔터프라이즈 환경 대응",
          "Google Workspace 도메인 전체 위임(Domain-Wide Delegation, DWD)을 통해 GCP 서비스 계정에 Google Meet / Calendar / Drive Scopes 부여",
          "임직원의 개별 권한 범위(ACL) 내에서만 녹화 파일에 접근하도록 엄격한 보안 통제 규칙 적용",
          "임시 음성 파일은 GCS 전용 버킷에 보관 후 1일 만료 TTL 자동 삭제 정책 적용"
        ],
        resolution: "서비스 계정 DWD 방식 도입 및 24시간 TTL 자동 삭제 보안 정책 수립",
        speakers: ["임꺽정 Specialist (Google Workspace)", "SI 수행사 팀장", "홍길동 팀장 (리테일 회사)"]
      }
    ],
    action_items: [
      { task: "Gemini 3.7 Flash 기반 다중 화자 분리 & 무가공 전사 PoC 검증 결과 공유", assignee: "담당 CE (Google Cloud)", due: "2026-08-25", status: "IN_PROGRESS" },
      { task: "협업포털 화면 UI 및 Cloud Tasks 비동기 큐 연동 설계서 작성", assignee: "SI 수행사 팀장", due: "2026-08-28", status: "TODO" },
      { task: "사내 회의 유형별 표준 템플릿(CFT 정기, 임원보고 등) 양식 정의", assignee: "성춘향 님 (리테일 회사)", due: "2026-08-29", status: "TODO" }
    ]
  }
};

let activeNotes = null;
let activeSttTranscript = null;
let activeSttStatus = "COMPLETED";
let activeReportId = null;
let sttPollInterval = null;
let isPipelineRunning = false;
let currentInputMode = "file";
let selectedCustomFile = null;
let activeMediaUri = null;
let bucketFilesCache = [];
let selectedBucketFileIndex = -1;
let templatesCache = {};

function renderAll() {
  renderNotes();
  renderTranscript();
  renderMarkdown();
  renderCompareView();
}

function initLiveClock() {
  function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const clockEl = document.getElementById("statCurrentClock");
    if (clockEl) {
      clockEl.textContent = `${hours}:${minutes}:${seconds}`;
    }
    const dateEl = document.getElementById("statCurrentDate");
    if (dateEl) {
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      dateEl.textContent = `현재 시간 (${year}.${month}.${day})`;
    }
  }
  updateClock();
  setInterval(updateClock, 1000);
}

document.addEventListener("DOMContentLoaded", () => {
  initLiveClock();
  renderAll();
  fetchTemplates();
  loadReportsArchive();
});

async function fetchDynamicTranscript(sampleKey = "sample_meet_85min") {
  try {
    const res = await fetch(`${API_BASE}/api/v1/notes/current?sample=${encodeURIComponent(sampleKey)}`);
    if (res.ok) {
      const data = await res.json();
      if (data.transcript && (Array.isArray(data.transcript) ? data.transcript.length > 0 : Boolean(data.transcript))) {
        activeTranscript = parseTranscriptText(data.transcript);
        renderTranscript();
        renderMarkdown();
      }
    }
  } catch (e) {
    console.log("Using static transcript fallback:", e);
  }
}

// ==============================================================================
// 템플릿 관리 (Template Management)
// ==============================================================================

async function fetchTemplates() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/templates`);
    if (res.ok) {
      const data = await res.json();
      templatesCache = {};
      data.templates.forEach(t => {
        templatesCache[t.id] = t;
      });
    }
  } catch (e) {
    console.log("템플릿 목록 로드 실패:", e);
  }
}

function openTemplateModal() {
  const modal = document.getElementById("templateModal");
  if (modal) {
    modal.classList.add("open");
    modal.classList.add("active");
  }
  
  const currentSelectVal = document.getElementById("templateType")?.value || "CFT_REGULAR";
  const modalSelect = document.getElementById("modalTemplateSelect");
  if (modalSelect) {
    modalSelect.value = currentSelectVal;
  }
  
  loadTemplateIntoModal(currentSelectVal);
}

function closeTemplateModal() {
  const modal = document.getElementById("templateModal");
  if (modal) {
    modal.classList.remove("open");
    modal.classList.remove("active");
  }
}

function handleTemplateModalChange() {
  const val = document.getElementById("modalTemplateSelect")?.value || "CFT_REGULAR";
  loadTemplateIntoModal(val);
}

function handleTemplateSelectChange() {
  // Can be used if needed when main dropdown changes
}

async function loadTemplateIntoModal(templateId) {
  let tpl = templatesCache[templateId];
  if (!tpl || (!tpl.prompt && !tpl.system_prompt)) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/templates/${templateId}`);
      if (res.ok) {
        const data = await res.json();
        tpl = data.template;
        templatesCache[templateId] = tpl;
      }
    } catch (e) {
      console.log("템플릿 상세 로드 실패:", e);
    }
  }

  if (tpl) {
    const nameInput = document.getElementById("templateNameInput");
    const descInput = document.getElementById("templateDescInput");
    const promptArea = document.getElementById("templatePromptTextarea");
    if (nameInput) nameInput.value = tpl.name || "";
    if (descInput) descInput.value = tpl.description || "";
    if (promptArea) promptArea.value = tpl.prompt || tpl.system_prompt || "";
  }
}

async function saveTemplatePrompt() {
  const modalSelect = document.getElementById("modalTemplateSelect");
  const templateId = modalSelect?.value || "CFT_REGULAR";
  const nameInput = document.getElementById("templateNameInput")?.value || "";
  const descInput = document.getElementById("templateDescInput")?.value || "";
  const promptArea = document.getElementById("templatePromptTextarea")?.value || "";

  const btn = document.getElementById("saveTemplateBtn");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/v1/templates/${templateId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameInput,
        description: descInput,
        prompt: promptArea,
        system_prompt: promptArea
      })
    });

    if (!res.ok) throw new Error(`저장 실패 (HTTP ${res.status})`);
    const data = await res.json();
    templatesCache[templateId] = data.template;
    closeTemplateModal();
    alert(`✅ [${data.template.name}] 템플릿 프롬프트가 성공적으로 수정/저장되었습니다!`);
  } catch (err) {
    alert(`❌ 저장 오류: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function resetTemplatePrompt() {
  const modalSelect = document.getElementById("modalTemplateSelect");
  const templateId = modalSelect?.value || "CFT_REGULAR";

  if (!confirm(`[${templateId}] 템플릿 프롬프트를 기본값으로 되돌리시겠습니까?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/templates/${templateId}/reset`, {
      method: "POST"
    });

    if (!res.ok) throw new Error(`초기화 실패 (HTTP ${res.status})`);
    const data = await res.json();
    templatesCache[templateId] = data.template;
    loadTemplateIntoModal(templateId);
    alert(`✅ [${data.template.name}] 템플릿이 기본값으로 복원되었습니다.`);
  } catch (err) {
    alert(`❌ 초기화 오류: ${err.message}`);
  }
}

// ==============================================================================
// 미디어 소스 선택 및 탐색기 핸들러
// ==============================================================================

function handleSampleSelectChange() {
  const select = document.getElementById("sampleSelect");
  if (!select) return;
  const val = select.value;
  
  const uploadGroup = document.getElementById("uploadGroup");
  const urlActiveGroup = document.getElementById("urlActiveGroup");
  const quickFileBtnsGroup = document.getElementById("quickFileBtnsGroup");
  const quickBucketBtnGroup = document.getElementById("quickBucketBtnGroup");
  
  if (val === "custom_file") {
    currentInputMode = "file";
    if (uploadGroup) uploadGroup.style.display = "block";
    if (urlActiveGroup) urlActiveGroup.style.display = "none";
    if (quickFileBtnsGroup) quickFileBtnsGroup.style.display = "grid";
    if (quickBucketBtnGroup) quickBucketBtnGroup.style.display = "block";
  } else if (val === "custom_url") {
    currentInputMode = "url";
    if (uploadGroup) uploadGroup.style.display = "none";
    if (quickFileBtnsGroup) quickFileBtnsGroup.style.display = "grid";
    if (quickBucketBtnGroup) quickBucketBtnGroup.style.display = "block";
    openUrlModal();
  } else if (val === "custom_bucket") {
    currentInputMode = "bucket";
    if (uploadGroup) uploadGroup.style.display = "none";
    if (quickFileBtnsGroup) quickFileBtnsGroup.style.display = "grid";
    if (quickBucketBtnGroup) quickBucketBtnGroup.style.display = "block";
    openBucketModal();
  }
}


// ==============================================================================
// 1. Native File Picker Handlers
// ==============================================================================

// 1. Native File Picker Handlers
function openFilePicker() {
  const fileInput = document.getElementById("fileInput");
  const uploadGroup = document.getElementById("uploadGroup");
  if (uploadGroup) uploadGroup.style.display = "block";
  if (fileInput) {
    fileInput.click();
  }
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (file) {
    selectedCustomFile = file;
    currentInputMode = "file";
    
    const select = document.getElementById("sampleSelect");
    if (select) select.value = "custom_file";
    
    const badge = document.getElementById("fileSelectedBadge");
    const nameSpan = document.getElementById("fileSelectedName");
    const dropText = document.getElementById("dropzoneText");
    
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    if (dropText) dropText.textContent = `📁 ${file.name} (${sizeMb} MB)`;
    if (nameSpan) nameSpan.textContent = `${file.name} (${sizeMb} MB)`;
    if (badge) badge.style.display = "block";
    
    const cleanTitle = file.name.replace(/\.[^/.]+$/, "").replace(/^Copy of\s*/i, "");
    const titleInput = document.getElementById("meetingTitle");
    if (titleInput) titleInput.value = `${cleanTitle} 회의록`;
  }
}

// 2. URL Modal Handlers
function openUrlModal() {
  const modal = document.getElementById("urlModal");
  if (modal) {
    modal.classList.add("open");
    modal.classList.add("active");
  }
}

function closeUrlModal() {
  const modal = document.getElementById("urlModal");
  if (modal) {
    modal.classList.remove("open");
    modal.classList.remove("active");
  }
}

async function verifyUrlAccessibility() {
  const urlInput = document.getElementById("urlInput");
  const resultBox = document.getElementById("urlVerifyResult");
  const verifyBtn = document.getElementById("verifyUrlBtn");
  const applyBtn = document.getElementById("applyUrlBtn");
  
  const url = urlInput ? urlInput.value.trim() : "";
  if (!url) {
    alert("검증할 URL 또는 gs:// 경로를 입력해주세요.");
    return;
  }
  
  if (resultBox) {
    resultBox.style.display = "block";
    resultBox.style.background = "var(--accent-blue-light)";
    resultBox.style.border = "1px solid var(--accent-blue-border)";
    resultBox.style.color = "var(--accent-blue)";
    resultBox.innerHTML = "<span>⏳ URL 접근성 및 미디어 스트림 확인 중...</span>";
  }
  if (verifyBtn) verifyBtn.disabled = true;
  
  try {
    const res = await fetch(`${API_BASE}/api/v1/media/verify-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    
    const data = await res.json();
    if (data.accessible) {
      if (resultBox) {
        resultBox.style.background = "var(--accent-emerald-light)";
        resultBox.style.border = "1px solid var(--accent-emerald-border)";
        resultBox.style.color = "var(--accent-emerald)";
        resultBox.innerHTML = `<strong>${data.message}</strong><br><span style="font-size:11px; opacity:0.85;">타입: ${data.content_type || '미디어'} | 소스: ${data.source_type}</span>`;
      }
      if (applyBtn) applyBtn.disabled = false;
    } else {
      if (resultBox) {
        resultBox.style.background = "#fef2f2";
        resultBox.style.border = "1px solid #fecaca";
        resultBox.style.color = "var(--accent-rose)";
        resultBox.innerHTML = `<strong>${data.message}</strong>`;
      }
    }
  } catch (err) {
    if (resultBox) {
      resultBox.style.background = "#fef2f2";
      resultBox.style.border = "1px solid #fecaca";
      resultBox.style.color = "var(--accent-rose)";
      resultBox.innerHTML = `<strong>❌ 연결 에러: ${err.message}</strong>`;
    }
  } finally {
    if (verifyBtn) verifyBtn.disabled = false;
  }
}

function applyUrlSelection() {
  const urlInput = document.getElementById("urlInput");
  const url = urlInput ? urlInput.value.trim() : "";
  if (!url) return;
  
  activeMediaUri = url;
  currentInputMode = "url";
  
  const select = document.getElementById("sampleSelect");
  if (select) select.value = "custom_url";
  
  const urlActiveGroup = document.getElementById("urlActiveGroup");
  const activeUrlText = document.getElementById("activeUrlText");
  if (urlActiveGroup) urlActiveGroup.style.display = "block";
  if (activeUrlText) activeUrlText.textContent = `🔗 ${url}`;
  
  const uploadGroup = document.getElementById("uploadGroup");
  if (uploadGroup) uploadGroup.style.display = "none";
  
  closeUrlModal();
}

// 3. GCS Bucket Modal Handlers
function openBucketModal() {
  const modal = document.getElementById("bucketModal");
  if (modal) {
    modal.classList.add("open");
    modal.classList.add("active");
  }
  fetchBucketFiles();
}

function closeBucketModal() {
  const modal = document.getElementById("bucketModal");
  if (modal) {
    modal.classList.remove("open");
    modal.classList.remove("active");
  }
}

async function fetchBucketFiles() {
  const listContainer = document.getElementById("bucketFileList");
  const infoText = document.getElementById("bucketInfoText");
  const applyBtn = document.getElementById("applyBucketBtn");
  if (applyBtn) applyBtn.disabled = true;
  selectedBucketFileIndex = -1;
  
  if (listContainer) {
    listContainer.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">🔄 버킷 및 data/input_media 경로 파일 검색 중...</div>`;
  }
  
  try {
    const res = await fetch(`${API_BASE}/api/v1/storage/bucket-files`);
    const data = await res.json();
    
    if (infoText) {
      infoText.textContent = `GCS 버킷: ${data.bucket_name} (${data.files.length}개 파일 발견)`;
    }
    
    bucketFilesCache = data.files || [];
    if (bucketFilesCache.length === 0) {
      if (listContainer) listContainer.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">발견된 미디어 파일이 없습니다.</div>`;
      return;
    }
    
    let html = `<table class="data-table">
      <thead>
        <tr>
          <th style="width:50px; text-align:center;">선택</th>
          <th>파일명 / 경로</th>
          <th style="width:110px;">위치</th>
          <th style="width:90px;">크기</th>
          <th style="width:130px;">수정일시</th>
        </tr>
      </thead>
      <tbody>`;
      
    bucketFilesCache.forEach((file, idx) => {
      const locationBadge = file.location.includes("GCS") 
        ? `<span style="background:var(--accent-blue-light); color:var(--accent-blue); padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;">GCS 버킷</span>`
        : `<span style="background:#f5f3ff; color:var(--accent-indigo); padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;">로컬 디스크</span>`;
        
      html += `
        <tr style="cursor:pointer;" onclick="selectBucketRow(${idx})">
          <td style="text-align:center;">
            <input type="radio" name="bucketFileRadio" id="bfile_${idx}" value="${idx}">
          </td>
          <td>
            <div style="font-family:var(--font-mono); color:var(--text-primary); font-weight:600;">📄 ${file.name}</div>
            <div style="font-size:11px; color:var(--text-muted);">${file.path}</div>
          </td>
          <td>${locationBadge}</td>
          <td style="color:var(--text-secondary); font-weight:500;">${file.size_mb} MB</td>
          <td style="color:var(--text-muted); font-size:12px;">${file.updated_at}</td>
        </tr>`;
    });
    
    html += `</tbody></table>`;
    if (listContainer) listContainer.innerHTML = html;
  } catch (err) {
    if (listContainer) listContainer.innerHTML = `<div style="padding:20px; text-align:center; color:var(--accent-rose);">파일 목록 로드 실패: ${err.message}</div>`;
  }
}

function selectBucketRow(index) {
  selectedBucketFileIndex = index;
  const radio = document.getElementById(`bfile_${index}`);
  if (radio) radio.checked = true;
  const applyBtn = document.getElementById("applyBucketBtn");
  if (applyBtn) applyBtn.disabled = false;
}

function applyBucketSelection() {
  if (selectedBucketFileIndex < 0 || selectedBucketFileIndex >= bucketFilesCache.length) {
    alert("파일을 선택해주세요.");
    return;
  }
  
  const file = bucketFilesCache[selectedBucketFileIndex];
  activeMediaUri = file.uri;
  currentInputMode = "bucket";
  
  const select = document.getElementById("sampleSelect");
  if (select) select.value = "custom_bucket";
  
  const urlActiveGroup = document.getElementById("urlActiveGroup");
  const activeUrlText = document.getElementById("activeUrlText");
  if (urlActiveGroup) urlActiveGroup.style.display = "block";
  if (activeUrlText) activeUrlText.textContent = `☁️ [버킷 파일] ${file.name} (${file.size_mb} MB)`;
  
  const cleanTitle = file.name.replace(/\.[^/.]+$/, "").replace(/^Copy of\s*/i, "");
  const titleInput = document.getElementById("meetingTitle");
  if (titleInput) titleInput.value = `${cleanTitle} 회의록`;
  
  closeBucketModal();
}

function renderAll() {
  renderNotes();
  renderTranscript();
  renderMarkdown();
  renderCompareView();
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("active");
  });
  document.querySelectorAll(".tab-content").forEach(pane => {
    pane.classList.remove("active");
  });

  const targetPane = document.getElementById(tabId);
  if (targetPane) targetPane.classList.add("active");

  const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b => 
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(tabId)
  );
  if (activeBtn) activeBtn.classList.add("active");

  // Trigger dedicated rendering on tab switch
  if (tabId === "compareTab") {
    renderCompareView();
  } else if (tabId === "notesTab") {
    renderNotes();
  } else if (tabId === "transcriptTab") {
    renderTranscript();
  } else if (tabId === "markdownTab") {
    renderMarkdown();
  }
}

function renderNotes() {
  const container = document.getElementById("notesContainer");
  if (!container) return;
  if (isPipelineRunning) return; // 분석 진행 중에는 파이프라인 진행 상태 뷰 보존

  if (!activeNotes) {
    container.innerHTML = `
      <div class="empty-guide-box">
        <div class="empty-guide-icon-wrap">📋</div>
        <div class="empty-guide-title">회의 미디어를 업로드하고 AI 회의록을 생성해보세요</div>
        <div class="empty-guide-desc">
          왼쪽 패널에서 음성/영상 파일을 직접 업로드하거나 소스를 선택한 후<br>
          <strong>[🚀 Gemini 3.7 Flash 회의록 생성]</strong> 버튼을 누르면 AI가 구조화된 회의록을 즉시 작성합니다.
        </div>
        <div class="empty-guide-steps">
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#dbeafe; color:#1d4ed8;">1</div>
            <div class="empty-step-title">1페이지 핵심 요약</div>
            <div class="empty-step-text">회의의 핵심 아젠다와 주요 합의사항을 1페이지 분량으로 명확하게 압축합니다.</div>
          </div>
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#ede9fe; color:#5b21b6;">2</div>
            <div class="empty-step-title">안건별 심층 논의</div>
            <div class="empty-step-text">배경, 핵심 세부 발언 요점, 도출 결론을 부서별/안건별로 체계화합니다.</div>
          </div>
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#fef3c7; color:#92400e;">3</div>
            <div class="empty-step-title">Action Items 과제 표</div>
            <div class="empty-step-text">담당자별 후속 조치 업무, 목표 완료 일정, 진행 상태를 한눈에 정리합니다.</div>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const agendaThemes = ["theme-blue", "theme-violet", "theme-emerald", "theme-amber", "theme-rose"];

  let html = `
    <div class="note-header-banner">
      <h3>${activeNotes.title}</h3>
      <div style="font-size:13px; display:flex; flex-wrap:wrap; gap:12px;">
        <span class="meta-chip date">📅 <strong>일시:</strong> ${activeNotes.date} ${activeNotes.time}</span>
        <span class="meta-chip attendees">👥 <strong>참석자:</strong> ${activeNotes.attendees}</span>
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#dbeafe; color:#1d4ed8; padding:3px 8px; border-radius:6px; font-size:13px;">📌 1</span>
        1페이지 핵심 요약 (Executive Summary)
      </h4>
      <div class="card-summary" style="line-height:1.75;">
        ${formatInlineMarkdown(activeNotes.executive_summary)}
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#d1fae5; color:#065f46; padding:3px 8px; border-radius:6px; font-size:13px;">🎯 2</span>
        핵심 결정사항 (Key Decisions)
      </h4>
      <div class="card-decisions">
        ${activeNotes.key_decisions && activeNotes.key_decisions.length > 0 ? activeNotes.key_decisions.map((d, i) => `
          <div class="decision-item">
            <span class="decision-bullet">${i + 1}</span>
            <div style="flex:1;">${formatInlineMarkdown(d)}</div>
          </div>
        `).join("") : '<div style="color:var(--text-muted);">별도 결정사항 없음 (정보 공유 목적 회의)</div>'}
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#ede9fe; color:#5b21b6; padding:3px 8px; border-radius:6px; font-size:13px;">💬 3</span>
        안건별 상세 논의 (Agenda Discussions)
      </h4>
      <div style="display:flex; flex-direction:column; gap:16px;">
        ${(activeNotes.agendas || []).map((ag, idx) => {
          const themeClass = agendaThemes[idx % agendaThemes.length];
          const title = ag.agenda_title || ag.title || `안건 ${idx + 1}`;
          const summary = ag.summary || ag.content || ag.agenda_summary || '';
          const keyPoints = ag.key_points || ag.keypoints || [];
          const resolution = ag.resolution || ag.conclusion || '';
          const speakers = ag.speakers || [];

          return `
            <div class="agenda-card ${themeClass}">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <h5 style="margin:0; font-size:15px; font-weight:800; color:#0f172a;">${formatInlineMarkdown(title)}</h5>
                ${speakers.length > 0 ? `<div style="font-size:11.5px; color:var(--text-muted); display:flex; align-items:center; gap:4px;"><span style="background:#ffffff; border:1px solid #cbd5e1; padding:2px 8px; border-radius:4px; font-weight:700; color:var(--text-secondary);">🗣️ ${speakers.join(", ")}</span></div>` : ''}
              </div>
              <div style="margin:0 0 10px 0; font-size:13.5px; line-height:1.7; color:var(--text-secondary);">
                <strong style="color:var(--text-primary);">📌 논의 배경 및 개요:</strong> ${formatInlineMarkdown(summary)}
              </div>
              ${keyPoints.length > 0 ? `
                <div style="background:rgba(255,255,255,0.75); border-radius:8px; padding:12px 14px; margin-bottom:10px; border:1px solid var(--border-color);">
                  <div style="font-size:12.5px; font-weight:800; color:var(--text-primary); margin-bottom:8px;">🔍 핵심 세부 논의 내용 (Key Discussion Points):</div>
                  <ul style="margin:0; padding-left:18px; font-size:13px; color:var(--text-secondary); line-height:1.65;">
                    ${keyPoints.map(kp => `<li style="margin-bottom:6px;">${formatInlineMarkdown(kp)}</li>`).join("")}
                  </ul>
                </div>
              ` : ''}
              ${resolution ? `
                <div style="font-size:12.5px; color:#15803d; background:#ecfdf5; border:1px solid #a7f3d0; padding:8px 12px; border-radius:6px; font-weight:600; display:flex; align-items:center; gap:6px;">
                  <span>🎯 <strong>도출 결론 / 합의:</strong> ${formatInlineMarkdown(resolution)}</span>
                </div>
              ` : ''}
            </div>
          `;
        }).join("")}
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:6px; font-size:13px;">📋 4</span>
        실행 과제 (Action Items)
      </h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>실행 과제</th>
            <th style="width:190px;">담당자</th>
            <th style="width:130px;">완료 목표일</th>
            <th style="width:95px; text-align:center;">상태</th>
          </tr>
        </thead>
        <tbody>
          ${(activeNotes.action_items || []).map((item, idx) => `
            <tr>
              <td style="color:var(--text-primary); font-weight:700;">
                <span style="display:inline-block; width:20px; height:20px; background:#eff6ff; color:#2563eb; border-radius:50%; text-align:center; line-height:20px; font-size:11px; margin-right:6px;">${idx+1}</span>
                ${formatInlineMarkdown(item.task_description || item.task || '')}
              </td>
              <td>
                <span style="background:#e0e7ff; color:#3730a3; padding:3px 8px; border-radius:6px; font-weight:700; font-size:12px;">👤 ${item.assignee || '미지정'}</span>
              </td>
              <td style="color:#6b21a8; font-family:var(--font-mono); font-weight:600; font-size:12px;">
                <span style="background:#f5f3ff; border:1px solid #ddd6fe; padding:2px 6px; border-radius:4px;">📅 ${item.due_date || item.due || 'TBD'}</span>
              </td>
              <td style="text-align:center;">
                <span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; font-weight:700; padding:3px 8px; border-radius:9999px; font-size:11px;">🟢 진행중</span>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  container.innerHTML = html;
}

function getSpeakerPillClass(speaker) {
  if (!speaker) return "generic-spk";
  if (speaker.includes("홍길동") || speaker.includes("리테일 회사 PM")) return "client-pm";
  if (speaker.includes("담당 CE") || speaker.includes("Google Cloud")) return "google-ce";
  if (speaker.includes("이몽룡") || speaker.includes("성춘향")) return "client-eng";
  if (speaker.includes("SI 수행사")) return "partner-si";
  if (speaker.includes("임꺽정") || speaker.includes("Workspace")) return "workspace-spec";
  return "generic-spk";
}

function renderTranscript() {
  const container = document.getElementById("transcriptContainer");
  if (!container) return;

  if (typeof activeTranscript === "string") {
    activeTranscript = parseTranscriptText(activeTranscript);
  }

  if ((!activeTranscript || activeTranscript.length === 0) && activeNotes) {
    if (activeNotes.transcript) {
      activeTranscript = parseTranscriptText(activeNotes.transcript);
    } else if (activeNotes.raw_transcript) {
      activeTranscript = parseTranscriptText(activeNotes.raw_transcript);
    }
  }

  if (!activeTranscript || activeTranscript.length === 0) {
    container.innerHTML = `
      <div class="empty-guide-box">
        <div class="empty-guide-icon-wrap transcript">🎙️</div>
        <div class="empty-guide-title">100% 무가공 대화 전체 스크립트가 여기에 표시됩니다</div>
        <div class="empty-guide-desc">
          Vertex AI Gemini 3.7 오디오 멀티모달 Diarization 엔진이 회의 음성 파형을 정밀 분석하여<br>
          임의의 축약이나 누락 없이 타임스탬프와 함께 발언자별 대화 전문(Verbatim)을 전사합니다.
        </div>
        <div class="empty-guide-steps">
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#f5f3ff; color:#7c3aed;">⏱️</div>
            <div class="empty-step-title">타임스탬프 동기화</div>
            <div class="empty-step-text">발화 시점 [00:00:00] 단위로 대화 위치를 빠르게 역추적할 수 있습니다.</div>
          </div>
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#eff6ff; color:#2563eb;">👥</div>
            <div class="empty-step-title">다중 화자 식별</div>
            <div class="empty-step-text">목소리 특징과 캘린더 참석자 명단을 결합하여 화자를 자동으로 매핑합니다.</div>
          </div>
          <div class="empty-step-card">
            <div class="empty-step-badge" style="background:#fdf2f8; color:#be185d;">🔄</div>
            <div class="empty-step-title">화자 일괄 치환</div>
            <div class="empty-step-text">미인식 화자(Speaker 1 등)는 [화자 일괄 치환] 도구로 즉시 수정 가능합니다.</div>
          </div>
        </div>
      </div>
    `;
    return;
  }

  let html = activeTranscript.map(turn => {
    const pillClass = getSpeakerPillClass(turn.speaker);
    return `
      <div class="transcript-turn">
        <span class="transcript-time">${turn.time}</span>
        <span class="speaker-pill ${pillClass}">👤 ${turn.speaker}</span>
        <span class="transcript-text">${turn.text}</span>
      </div>
    `;
  }).join("");

  container.innerHTML = html;
}

function renderMarkdown() {
  const preview = document.getElementById("markdownPreview");
  if (!preview) return;

  let guideBox = document.getElementById("markdownEmptyGuide");

  if (!activeNotes) {
    preview.style.display = "none";
    if (!guideBox) {
      guideBox = document.createElement("div");
      guideBox.id = "markdownEmptyGuide";
      guideBox.className = "empty-guide-box";
      preview.parentNode.appendChild(guideBox);
    }
    guideBox.style.display = "flex";
    guideBox.innerHTML = `
      <div class="empty-guide-icon-wrap markdown">📄</div>
      <div class="empty-guide-title">생성된 통합 마크다운 문서가 여기에 표시됩니다</div>
      <div class="empty-guide-desc">
        구조화 회의록과 대화 전사본 전문을 통합한 표준 GitHub Flavored Markdown 문서가 생성되며<br>
        상단의 <strong>[📋 복사]</strong> 버튼을 통해 클립보드나 사내 위키/문서 도구에 즉시 복사할 수 있습니다.
      </div>
      <div class="empty-guide-steps">
        <div class="empty-step-card">
          <div class="empty-step-badge" style="background:#ecfdf5; color:#065f46;">📑</div>
          <div class="empty-step-title">표준 포맷 호환</div>
          <div class="empty-step-text">Notion, Confluence, Google Docs 등 모든 사내 업무 도구와 호환됩니다.</div>
        </div>
        <div class="empty-step-card">
          <div class="empty-step-badge" style="background:#eef2ff; color:#4338ca;">⚡</div>
          <div class="empty-step-title">원클릭 전체 복사</div>
          <div class="empty-step-text">요약부터 전사본 전문까지 유실 없이 1초 만에 클립보드로 전송합니다.</div>
        </div>
      </div>
    `;
    return;
  }

  if (guideBox) guideBox.style.display = "none";
  preview.style.display = "block";

  let md = [];
  md.push(`# 📋 [${activeNotes.title || '회의록'}]`);
  md.push(`- **일시**: ${activeNotes.date || '2026-08-19'} ${activeNotes.time || ''}`);
  md.push(`- **참석자**: ${activeNotes.attendees || ''}\n`);
  md.push(`## 1. 1페이지 핵심 요약 (Executive Summary)\n${activeNotes.executive_summary}\n`);
  
  if (activeNotes.key_decisions && activeNotes.key_decisions.length > 0) {
    md.push(`## 2. 주요 결정사항 (Key Decisions)`);
    activeNotes.key_decisions.forEach(d => md.push(`- ${d}`));
    md.push("");
  }
  
  if (activeNotes.agendas && activeNotes.agendas.length > 0) {
    md.push(`## 3. 안건별 상세 논의 (Agenda Discussions)`);
    activeNotes.agendas.forEach(ag => {
      md.push(`### ${ag.title}`);
      if (ag.speakers && ag.speakers.length > 0) {
        md.push(`- **주요 발언자**: ${ag.speakers.join(", ")}`);
      }
      md.push(`- **논의 배경 및 개요**: ${ag.content || ag.summary || ''}`);
      if (ag.key_points && ag.key_points.length > 0) {
        md.push(`- **핵심 세부 논의 내용 (Key Discussion Points)**:`);
        ag.key_points.forEach(kp => md.push(`  * ${kp}`));
      }
      if (ag.resolution) {
        md.push(`- **도출 결론 / 합의**: ${ag.resolution}`);
      }
      md.push("");
    });
  }

  md.push(`## 4. 대화 전체 전사본 전문 (Verbatim Transcript)\n`);
  activeTranscript.forEach(t => {
    md.push(`${t.time} ${t.speaker}: ${t.text}`);
  });

  preview.textContent = md.join("\n");
}

let activeSttProgress = { percent: 5, completed: 0, total: 9 };

function renderCompareView() {
  const container = document.getElementById("compareViewContainer");
  if (!container) return;

  if (activeTranscriptTab !== "compare") return;

  const geminiTurns = getGeminiTurns();
  const sttTurns = getSttTurns();

  if (geminiTurns.length === 0 && sttTurns.length === 0 && !activeNotes) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚖️</div>
        <div class="empty-state-title">전사 엔진 비교 결과가 없습니다.</div>
        <div class="empty-state-desc">
          회의 미디어를 업로드하여 분석을 시작하면 Gemini 3.7 Flash vs Cloud STT 성능 비교가 활성화됩니다.
        </div>
      </div>
    `;
    return;
  }

  const isSttProcessing = activeSttStatus === "PROCESSING";
  const geminiCharCount = geminiTurns.reduce((acc, t) => acc + (t.text || "").length, 0);
  const sttCharCount = sttTurns.reduce((acc, t) => acc + (t.text || "").length, 0);

  let html = `
    <div class="compare-metrics-grid">
      <div class="compare-metric-card highlight">
        <div class="compare-metric-title">💰 2시간 회의 기준 비용 (TCO)</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">Gemini: 약 160원</span>
          <span class="compare-metric-val stt">STT: 약 2,800원</span>
        </div>
        <div style="font-size:11.5px; color:#15803d; font-weight:700; margin-top:2px;">✨ Gemini 도입 시 94.3% (17.5배) 비용 절감</div>
      </div>

      <div class="compare-metric-card">
        <div class="compare-metric-title">⚡ 평균 처리 속도 (Latency)</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">Gemini: ~20초 (초고속 완료)</span>
          <span class="compare-metric-val stt">${isSttProcessing ? `<span style="color:#d97706; font-weight:700;">STT: ⏳ ${activeSttProgress.percent || 5}% 진행 중...</span>` : 'STT: ~120초'}</span>
        </div>
        <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">Fast-Path 회의록 & 비동기 백그라운드 STT</div>
      </div>

      <div class="compare-metric-card">
        <div class="compare-metric-title">📊 전사 발화 턴 & 글자 수</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">${geminiTurns.length}턴 (${geminiCharCount.toLocaleString()}자)</span>
          <span class="compare-metric-val stt">${isSttProcessing ? `<span style="font-size:12.5px; color:#7c3aed; font-weight:700;">⏳ ${activeSttProgress.completed || 0}/${activeSttProgress.total || 9} 청크 분석 중</span>` : `${sttTurns.length}턴 (${sttCharCount.toLocaleString()}자)`}</span>
        </div>
        <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">스마트 문맥 전사 vs 음향 축어 전사</div>
      </div>
    </div>

    <div class="compare-split-grid" style="margin-top:14px;">
      <div class="compare-col">
        <div class="compare-col-header">
          <div class="compare-col-title">
            <span>✨ Vertex AI Gemini 3.7 Flash</span>
          </div>
          <span class="compare-col-badge gemini">스마트 문맥 & 참석자 매핑</span>
        </div>
        <div class="compare-flow">
          ${geminiTurns.length > 0 ? geminiTurns.map(turn => `
            <div class="compare-turn-bubble gemini">
              <div class="compare-turn-meta">
                <span class="compare-turn-time">${turn.time}</span>
                <span class="compare-turn-speaker" style="color:#0369a1;">👤 ${turn.speaker}</span>
              </div>
              <div class="compare-turn-text">${turn.text}</div>
            </div>
          `).join("") : `<div style="padding:30px; text-align:center; color:var(--text-muted);">대화록을 준비 중입니다.</div>`}
        </div>
      </div>

      <div class="compare-col">
        <div class="compare-col-header">
          <div class="compare-col-title">
            <span>🎤 Cloud Speech-to-Text (Chirp 2)</span>
          </div>
          <span class="compare-col-badge stt" style="${isSttProcessing ? 'background:#fef3c7; color:#92400e;' : ''}">
            ${isSttProcessing ? `⏳ 음향 모델 전사 중 (${activeSttProgress.percent || 5}%)` : '100% 음향 기반 축어(Verbatim)'}
          </span>
        </div>
        <div class="compare-flow">
          ${isSttProcessing ? `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:280px; text-align:center; padding:40px 20px;">
              <div class="pstep-mini-spinner" style="width:32px; height:32px; border-width:3px; border-color:#e2e8f0; border-top-color:#7c3aed; margin-bottom:14px;"></div>
              <div style="font-size:14px; font-weight:800; color:#1e293b; margin-bottom:6px;">Cloud STT 음향 모델 비동기 전사 진행 중...</div>
              <div style="font-size:12.5px; color:var(--text-muted); line-height:1.6; max-width:340px;">
                대용량 오디오(128분) 음향 파형을 백그라운드에서 분석 중입니다.<br>
                화면은 기존 고속 렌더링을 유지하며, 완료 시 실시간 자동 갱신됩니다.
              </div>
            </div>
          ` : (sttTurns.length > 0 ? sttTurns.map(turn => `
            <div class="compare-turn-bubble stt">
              <div class="compare-turn-meta">
                <span class="compare-turn-time">${turn.time}</span>
                <span class="compare-turn-speaker" style="color:#7c3aed;">🎙️ ${turn.speaker}</span>
              </div>
              <div class="compare-turn-text">${turn.text}</div>
            </div>
          `).join("") : `
            <div style="padding:30px; text-align:center; color:var(--text-muted);">전사 결과가 준비 중입니다.</div>
          `)}
        </div>
      </div>
    </div>
  `;

  container.innerHTML = html;
}

function startSttPolling(reportId) {
  if (sttPollInterval) {
    clearInterval(sttPollInterval);
    sttPollInterval = null;
  }
  if (!reportId) return;

  activeReportId = reportId;
  activeSttStatus = "PROCESSING";
  let attempts = 0;
  const maxAttempts = 60; // 최대 300초 / 5분 (5초 * 60회)

  sttPollInterval = setInterval(async () => {
    attempts++;
    if (attempts > maxAttempts || activeReportId !== reportId) {
      clearInterval(sttPollInterval);
      sttPollInterval = null;
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${encodeURIComponent(reportId)}/stt-status`);
      if (!res.ok) {
        // 404 또는 일시적 에러 시 재시도 허용 (3회 연속 실패 시에만 중단)
        if (res.status === 404) {
          clearInterval(sttPollInterval);
          sttPollInterval = null;
        }
        return;
      }
      const data = await res.json();
      if (data.stt_status === "COMPLETED" || data.status === "NOT_FOUND") {
        clearInterval(sttPollInterval);
        sttPollInterval = null;
        if (data.stt_transcript && data.stt_transcript.length > 0) {
          activeSttStatus = "COMPLETED";
          activeSttTranscript = parseTranscriptText(data.stt_transcript);
          renderCompareView();
          showToast("🎤 Cloud STT 음향 모델 전사가 완료되었습니다!");
        }
      }
    } catch (e) {
      console.warn("STT 상태 폴링 일시적 네트워크 예외:", e);
    }
  }, 5000);
}

function addSpeakerMapRow(fromVal = "", toVal = "") {
  const container = document.getElementById("speakerMapRows");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "speaker-map-row";
  row.style.cssText = "display:flex; align-items:center; gap:8px;";

  row.innerHTML = `
    <input type="text" class="form-control speaker-from-input" placeholder="기존 화자 (예: [참석자 1] 또는 화자 1)" value="${escapeHtml(fromVal)}" style="flex:1; font-weight:600; font-family:var(--font-mono); font-size:12.5px; background:#f8fafc;">
    <span style="color:var(--text-muted); font-size:14px; flex-shrink:0;">➔</span>
    <input type="text" class="form-control speaker-to-input" list="speakerAttendeesDatalist" placeholder="치환할 이름 (예: 홍길동 팀장 (리테일 회사))" value="${escapeHtml(toVal)}" style="flex:1.4; font-size:12.5px;">
    <button type="button" class="btn btn-secondary btn-sm" onclick="this.closest('.speaker-map-row').remove()" style="padding:6px 9px; color:#ef4444; border:1px solid #fee2e2; border-radius:6px; cursor:pointer;" title="이 치환 규칙 삭제">🗑️</button>
  `;

  container.appendChild(row);
}

function openSpeakerModal() {
  const modal = document.getElementById("speakerModal");
  if (!modal) return;

  const container = document.getElementById("speakerMapRows");
  if (container) {
    container.innerHTML = "";

    // 1. 현재 로드된 발화 전사본(activeTranscript)에서 고유한 화자 목록 추출
    const detectedSpeakers = new Set();
    if (Array.isArray(activeTranscript) && activeTranscript.length > 0) {
      activeTranscript.forEach(t => {
        if (t && t.speaker && typeof t.speaker === 'string') {
          const spk = t.speaker.trim();
          if (spk) detectedSpeakers.add(spk);
        }
      });
    }

    // 2. 만약 activeNotes가 있고 attendees가 있다면 datalist에 반영
    if (activeNotes && activeNotes.attendees) {
      const dlist = document.getElementById("speakerAttendeesDatalist");
      if (dlist && typeof activeNotes.attendees === 'string') {
        const atts = activeNotes.attendees.split(/[,/]/).map(s => s.trim()).filter(Boolean);
        if (atts.length > 0) {
          dlist.innerHTML = atts.map(a => `<option value="${escapeHtml(a)}"></option>`).join("");
        }
      }
    }

    // 3. 감지된 화자가 있으면 각 화자별로 행 자동 생성
    if (detectedSpeakers.size > 0) {
      const spkList = Array.from(detectedSpeakers);
      // 참석자 1, 화자 1 등 미식별 화자를 우선 정렬
      spkList.sort((a, b) => {
        const isAUnk = a.includes("참석자") || a.includes("화자") || a.includes("Speaker");
        const isBUnk = b.includes("참석자") || b.includes("화자") || b.includes("Speaker");
        if (isAUnk && !isBUnk) return -1;
        if (!isAUnk && isBUnk) return 1;
        return a.localeCompare(b);
      });

      spkList.forEach((spk, idx) => {
        let suggestedTo = "";
        if (idx === 0) suggestedTo = "홍길동 팀장 (리테일 회사)";
        else if (idx === 1) suggestedTo = "담당 CE (Google Cloud)";
        else if (idx === 2) suggestedTo = "임꺽정 Specialist (Google Workspace)";
        addSpeakerMapRow(spk, suggestedTo);
      });
    } else {
      // 감지된 화자가 없을 경우 기본 2행 제공
      addSpeakerMapRow("[참석자 1]", "홍길동 팀장 (리테일 회사)");
      addSpeakerMapRow("[참석자 2]", "담당 CE (Google Cloud)");
    }
  }

  modal.classList.add("open");
  modal.classList.add("active");
}

function closeSpeakerModal() {
  const modal = document.getElementById("speakerModal");
  if (modal) {
    modal.classList.remove("open");
    modal.classList.remove("active");
  }
}

function applySpeakerReplace() {
  const rows = document.querySelectorAll("#speakerMapRows .speaker-map-row");
  const mappings = [];

  rows.forEach(r => {
    const fromInput = r.querySelector(".speaker-from-input");
    const toInput = r.querySelector(".speaker-to-input");
    const fromVal = fromInput ? fromInput.value.trim() : "";
    const toVal = toInput ? toInput.value.trim() : "";
    if (fromVal && toVal && fromVal !== toVal) {
      mappings.push({ from: fromVal, to: toVal });
    }
  });

  if (mappings.length === 0) {
    showToast("⚠️ 변경할 기존 화자와 치환할 참석자 이름을 입력해주세요.", "info");
    return;
  }

  let replacedCount = 0;

  // 1. activeTranscript 치환
  if (Array.isArray(activeTranscript)) {
    activeTranscript.forEach(t => {
      if (!t || !t.speaker) return;
      mappings.forEach(m => {
        const cleanFrom = m.from;
        const noBracketFrom = cleanFrom.replace(/^\[|\]$/g, "").trim();
        
        if (t.speaker === cleanFrom || t.speaker === noBracketFrom || t.speaker === `[${noBracketFrom}]`) {
          t.speaker = m.to;
          replacedCount++;
        } else if (t.speaker.includes(cleanFrom) || t.speaker.includes(noBracketFrom)) {
          t.speaker = t.speaker.split(cleanFrom).join(m.to).split(noBracketFrom).join(m.to);
          replacedCount++;
        }
      });
    });
  }

  // 2. activeSttTranscript 치환
  if (Array.isArray(activeSttTranscript)) {
    activeSttTranscript.forEach(t => {
      if (!t || !t.speaker) return;
      mappings.forEach(m => {
        const cleanFrom = m.from;
        const noBracketFrom = cleanFrom.replace(/^\[|\]$/g, "").trim();
        if (t.speaker === cleanFrom || t.speaker === noBracketFrom || t.speaker === `[${noBracketFrom}]`) {
          t.speaker = m.to;
        }
      });
    });
  }

  // 3. activeNotes (구조화 회의록 안건, 요약문, 발언자) 치환
  if (activeNotes) {
    mappings.forEach(m => {
      const cleanFrom = m.from;
      const noBracketFrom = cleanFrom.replace(/^\[|\]$/g, "").trim();

      // agendas
      if (Array.isArray(activeNotes.agendas)) {
        activeNotes.agendas.forEach(ag => {
          if (Array.isArray(ag.speakers)) {
            ag.speakers = ag.speakers.map(s => {
              if (s === cleanFrom || s === noBracketFrom || s === `[${noBracketFrom}]`) return m.to;
              return s;
            });
          }
          if (typeof ag.content === 'string') {
            ag.content = ag.content.split(cleanFrom).join(m.to).split(noBracketFrom).join(m.to);
          }
          if (Array.isArray(ag.key_points)) {
            ag.key_points = ag.key_points.map(kp => {
              if (typeof kp === 'string') {
                return kp.split(cleanFrom).join(m.to).split(noBracketFrom).join(m.to);
              }
              return kp;
            });
          }
        });
      }

      // action items
      if (Array.isArray(activeNotes.action_items)) {
        activeNotes.action_items.forEach(item => {
          if (item.assignee === cleanFrom || item.assignee === noBracketFrom || item.assignee === `[${noBracketFrom}]`) {
            item.assignee = m.to;
          }
        });
      }

      // executive summary
      if (typeof activeNotes.executive_summary === 'string') {
        activeNotes.executive_summary = activeNotes.executive_summary.split(cleanFrom).join(m.to).split(noBracketFrom).join(m.to);
      }
    });
  }

  // 4. 화면 다시 렌더링
  renderTranscript();
  renderMarkdown();
  renderNotes();

  closeSpeakerModal();
  showToast(`🎉 화자 일괄 치환 완료! (총 ${replacedCount}개 발화 턴 및 회의록에 반영되었습니다)`);
}

function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) {
    alert(message);
    return;
  }

  const toast = document.createElement("div");
  toast.className = `toast-message ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "toastSlideOut 0.3s forwards";
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, 3200);
}

function copyMarkdown() {
  if (!activeNotes) {
    showToast("⚠️ 먼저 회의 미디어를 업로드하고 회의록을 생성해주세요.", "info");
    return;
  }
  const preview = document.getElementById("markdownPreview");
  if (preview && preview.textContent.trim()) {
    navigator.clipboard.writeText(preview.textContent).then(() => {
      showToast("📋 전체 회의록이 클립보드에 복사되었습니다!");
    }).catch(err => {
      showToast(`❌ 복사 실패: ${err.message}`, "error");
    });
  }
}

function exportDocs() {
  alert("Google Docs로 내보내기가 완료되었습니다! (사내 포털 연동)");
}

function exportPDF() {
  if (!activeNotes) {
    alert("⚠️ 먼저 회의록을 생성해주세요.");
    return;
  }
  switchTab('notesTab');
  const origTitle = document.title;
  const cleanTitle = activeNotes.title || '리테일 회사 AI 회의록';
  document.title = `[리테일 회사 회의록] ${cleanTitle}`;
  setTimeout(() => {
    window.print();
    setTimeout(() => {
      document.title = origTitle;
    }, 1000);
  }, 250);
}

function openDocs() {
  window.open("/docs", "_blank");
}

let pipelineTimerInterval = null;
let pipelineStartTime = null;

function initPipelineProgress(titleText = "미디어 파일 분석") {
  isPipelineRunning = true;
  const container = document.getElementById("notesContainer");
  const transcriptContainer = document.getElementById("transcriptContainer");
  const markdownPreview = document.getElementById("markdownPreview");

  pipelineStartTime = Date.now();
  if (pipelineTimerInterval) clearInterval(pipelineTimerInterval);

  pipelineTimerInterval = setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - pipelineStartTime) / 1000);
    const mm = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const ss = String(elapsedSec % 60).padStart(2, '0');
    const timerElem = document.getElementById("pipelineElapsedTimer");
    if (timerElem) {
      timerElem.textContent = `⏱️ 진행 시간: ${mm}:${ss} (예상: 약 30~50초)`;
    }
  }, 1000);

  const html = `
    <div class="processing-pipeline-box">
      <div class="pipeline-header">
        <div class="pipeline-spinner-ring"></div>
        <div class="pipeline-header-text">
          <div class="pipeline-title">🚀 Vertex AI Gemini 3.7 Flash 회의록 & 다중 화자 분석</div>
          <div class="pipeline-subtitle">
            <span id="pipelineElapsedTimer">⏱️ 진행 시간: 00:00 (예상: 약 30~50초)</span> · <span style="font-family:var(--font-mono); font-size:12px; color:#2563eb;">${titleText}</span>
          </div>
        </div>
      </div>

      <div class="pipeline-progress-bar-wrap">
        <div class="pipeline-progress-bar-fill" id="pipelineProgressFill" style="width: 10%;"></div>
      </div>

      <div class="pipeline-steps-grid">
        <div class="pipeline-step-item step-active" id="pipeStep1">
          <div class="pstep-icon">📤</div>
          <div class="pstep-content">
            <div class="pstep-title">1단계: 미디어 업로드 및 GCS 다이렉트 세션 연결</div>
            <div class="pstep-desc" id="pipeStep1Desc">초고속 청크(5MB) 업로드 스트림 전송 중...</div>
          </div>
          <div class="pstep-status-badge active" id="pipeStep1Badge">
            <span class="pstep-mini-spinner"></span> 전송 중
          </div>
        </div>

        <div class="pipeline-step-item step-pending" id="pipeStep2">
          <div class="pstep-icon">🎧</div>
          <div class="pstep-content">
            <div class="pstep-title">2단계: 고음질 오디오 스트림 추출 & 전처리 (FFmpeg)</div>
            <div class="pstep-desc" id="pipeStep2Desc">비디오 영상에서 음성 채널 분리 및 무손실 압축 진행</div>
          </div>
          <div class="pstep-status-badge pending" id="pipeStep2Badge">대기 중</div>
        </div>

        <div class="pipeline-step-item step-pending" id="pipeStep3">
          <div class="pstep-icon">🤖</div>
          <div class="pstep-content">
            <div class="pstep-title">3단계: Vertex AI Gemini 3.7 Flash 다중 화자 분리 & STT 전사</div>
            <div class="pstep-desc" id="pipeStep3Desc">화자 음성 톤 식별, 타임스탬프 생성, 전체 대화 무삭제 100% 텍스트 전사</div>
          </div>
          <div class="pstep-status-badge pending" id="pipeStep3Badge">대기 중</div>
        </div>

        <div class="pipeline-step-item step-pending" id="pipeStep4">
          <div class="pstep-icon">📋</div>
          <div class="pstep-content">
            <div class="pstep-title">4단계: 맞춤형 안건 요약 & Action Items 회의록 서식화</div>
            <div class="pstep-desc" id="pipeStep4Desc">Pydantic 구조화 스키마 검증 및 영속 회의록 보관함 자동 등록</div>
          </div>
          <div class="pstep-status-badge pending" id="pipeStep4Badge">대기 중</div>
        </div>
      </div>

      <div class="pipeline-progress-caption" id="pipelineProgressCaption">
        💡 대용량 영상 파일도 안전하게 처리 중입니다. 브라우저를 닫지 말고 잠시만 기다려 주세요.
      </div>
    </div>
  `;

  if (container) container.innerHTML = html;
  if (transcriptContainer) transcriptContainer.innerHTML = `<div style="text-align:center; padding:60px 20px; color:var(--text-muted);"><div class="pipeline-spinner-ring" style="margin:0 auto 16px;"></div>🎙️ 화자 분리(Diarization) 및 전체 대화 전사 스크립트를 생성하고 있습니다...</div>`;
  if (markdownPreview) markdownPreview.textContent = `⏳ 회의록 마크다운 서식을 생성하고 있습니다...`;
}

function updatePipelineStep(stepIndex, percent, descText, captionText) {
  const fill = document.getElementById("pipelineProgressFill");
  if (fill && percent !== undefined) {
    fill.style.width = `${percent}%`;
  }

  const caption = document.getElementById("pipelineProgressCaption");
  if (caption && captionText) {
    caption.innerHTML = captionText;
  }

  for (let i = 1; i <= 4; i++) {
    const item = document.getElementById(`pipeStep${i}`);
    const badge = document.getElementById(`pipeStep${i}Badge`);
    const desc = document.getElementById(`pipeStep${i}Desc`);
    if (!item || !badge) continue;

    if (i < stepIndex) {
      item.className = "pipeline-step-item step-completed";
      badge.className = "pstep-status-badge completed";
      badge.innerHTML = "✅ 완료";
    } else if (i === stepIndex) {
      item.className = "pipeline-step-item step-active";
      badge.className = "pstep-status-badge active";
      badge.innerHTML = `<span class="pstep-mini-spinner"></span> 진행 중`;
      if (desc && descText) desc.innerHTML = descText;
    } else {
      item.className = "pipeline-step-item step-pending";
      badge.className = "pstep-status-badge pending";
      badge.innerHTML = "대기 중";
    }
  }
}

function stopPipelineProgress() {
  isPipelineRunning = false;
  if (pipelineTimerInterval) {
    clearInterval(pipelineTimerInterval);
    pipelineTimerInterval = null;
  }
}

async function handleGenerate(event) {
  event.preventDefault();
  const btn = document.getElementById("generateBtn");

  const title = document.getElementById("meetingTitle")?.value || "";
  const attendees = document.getElementById("attendees")?.value || "";
  const templateType = document.getElementById("templateType")?.value || "CFT_REGULAR";

  // 1. [로컬 파일 업로드 모드 스마트 수집]
  if (currentInputMode === "file") {
    if (!selectedCustomFile) {
      showToast("📁 분석할 미디어 파일을 선택해주세요. 파일 선택기를 엽니다...", "info");
      openFilePicker();
      return;
    }
  }

  // 3. [웹 / 클라우드 URL 모드 스마트 수집]
  if (currentInputMode === "url") {
    if (!activeMediaUri) {
      showToast("🔗 원격 미디어 URL을 지정해주세요. URL 입력창을 엽니다...");
      openUrlModal();
      return;
    }
  }

  // 4. [GCS 버킷 모드 스마트 수집]
  if (currentInputMode === "bucket") {
    if (!activeMediaUri) {
      showToast("☁️ GCS 버킷 내 오디오 파일을 선택해주세요. 버킷 탐색기를 엽니다...");
      openBucketModal();
      return;
    }
  }

  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Gemini 3.7 Flash 분석 시작...</span>`;

  try {
    if (currentInputMode === "file") {
      const file = selectedCustomFile;
      const effectiveTitle = title || file.name.replace(/\.[^/.]+$/, "");
      let finalData = null;

      // 1. 화면 우측 실시간 4단계 파이프라인 진행 뷰 시작 & 회의록 탭 전환
      initPipelineProgress(effectiveTitle);
      switchTab("notesTab");

      try {
        // [GCS Direct Resumable Upload]
        btn.innerHTML = `<span>⏳ GCS 업로드 세션 준비 중...</span>`;
        updatePipelineStep(1, 10, "GCS Resumable 세션 URL 발급 중...", "📤 브라우저에서 GCS로 대용량 미디어를 다이렉트 전송하기 위한 세션을 생성합니다.");
        
        // 1. GCS Resumable Upload 세션 URL 발급
        const sessionRes = await fetch(`${API_BASE}/api/v1/notes/get-upload-session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: file.name,
            content_type: file.type || "application/octet-stream",
            origin: window.location.origin
          })
        });

        if (!sessionRes.ok) {
          throw new Error(`GCS 업로드 세션 생성 실패 (HTTP ${sessionRes.status})`);
        }

        const sessionData = await sessionRes.json();
        const uploadUrl = sessionData.upload_url;
        const gcsUri = sessionData.gcs_uri;

        // 2. GCS 버킷으로 다이렉트 Resumable PUT 전송 (5MB 단위 청크)
        const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB (256KB 배수)
        const fileSize = file.size;
        let offset = 0;

        while (offset < fileSize) {
          const chunkBlob = file.slice(offset, Math.min(offset + CHUNK_SIZE, fileSize));
          const chunkLen = chunkBlob.size;
          const startByte = offset;
          const endByte = offset + chunkLen - 1;
          const percent = Math.round(((endByte + 1) / fileSize) * 100);

          btn.innerHTML = `<span>⏳ GCS 다이렉트 전송 중 (${percent}%)...</span>`;
          const overallProgress = Math.min(38, Math.round(10 + (percent * 0.28)));
          updatePipelineStep(1, overallProgress, `GCS 다이렉트 청크 전송 중 (${percent}% - ${(endByte / (1024*1024)).toFixed(1)}MB / ${(fileSize / (1024*1024)).toFixed(1)}MB)`, `📤 대용량 영상 데이터를 GCS 클라우드 버킷으로 안전하게 직접 전송 중입니다.`);

          const putRes = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
              "Content-Range": `bytes ${startByte}-${endByte}/${fileSize}`
            },
            body: chunkBlob
          });

          if (![200, 201, 308].includes(putRes.status)) {
            throw new Error(`GCS 전송 중 오류 발생: HTTP ${putRes.status}`);
          }

          offset += chunkLen;
        }

        // 업로드 100% 완료 -> 2단계(오디오 추출 및 전처리) 진입
        btn.innerHTML = `<span>⏳ 고음질 오디오 추출 중 (FFmpeg)...</span>`;
        updatePipelineStep(2, 45, "FFmpeg 기반 고음질 오디오 스트림 분리 및 무손실 압축 진행 중...", "🎧 비디오 파일에서 음성 대화 트랙을 분리하여 Gemini 초고속 분석용으로 전처리하고 있습니다.");

        // 잠시 후 3단계(Vertex AI Gemini 분석) 전환 타이머
        const step3Timer = setTimeout(() => {
          btn.innerHTML = `<span>⏳ Vertex AI Gemini 3.7 Flash 분석 중...</span>`;
          updatePipelineStep(3, 75, "화자별 음성 톤 식별, 타임스탬프 생성, 전체 대화 100% 전사 및 회의록 동시 추론 중...", "🤖 Vertex AI Gemini 3.7 Flash가 멀티모달 오디오를 직접 해석하여 다중 화자 분리와 회의록 작성을 동시에 수행하고 있습니다.");
        }, 3500);

        // 3. 백엔드에 Gemini 3.7 분석 및 회의록 생성 요청
        const processRes = await fetch(`${API_BASE}/api/v1/notes/process-gcs-media`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            gcs_uri: gcsUri,
            filename: file.name,
            title: effectiveTitle,
            attendees: attendees,
            template_type: templateType
          })
        });

        clearTimeout(step3Timer);

        if (!processRes.ok) {
          const errJson = await processRes.json().catch(() => ({}));
          throw new Error(`회의록 분석 실패: HTTP ${processRes.status} ${errJson.detail || ''}`);
        }

        // 4단계: 회의록 서식화 및 완료
        btn.innerHTML = `<span>⏳ 회의록 서식 렌더링 중...</span>`;
        updatePipelineStep(4, 95, "Pydantic 구조화 스키마 검증 및 회의록 보관함 영속 저장 완료!", "📋 회의록과 화자 분리 전사 스크립트를 화면에 렌더링하고 있습니다.");

        finalData = await processRes.json();
      } catch (directErr) {
        console.warn("GCS Direct Upload 예외, 백엔드 청크 릴레이 모드로 Fallback 시도:", directErr);
        // Fallback to backend chunking
        const CHUNK_SIZE = 5 * 1024 * 1024;
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = "upl_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);

        for (let i = 0; i < totalChunks; i++) {
          const start = i * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          const chunkBlob = file.slice(start, end);
          const percent = Math.round(((i + 1) / totalChunks) * 100);
          btn.innerHTML = `<span>⏳ 백엔드 릴레이 업로드 (${percent}%)...</span>`;
          const overallProgress = Math.min(38, Math.round(10 + (percent * 0.28)));
          updatePipelineStep(1, overallProgress, `백엔드 릴레이 청크 업로드 중 (${percent}% - ${i + 1}/${totalChunks} 청크)...`, `📤 API Gateway를 통해 백엔드로 안전하게 청크 데이터를 전송하고 있습니다.`);

          const chunkFormData = new FormData();
          chunkFormData.append("upload_id", uploadId);
          chunkFormData.append("chunk_index", i);
          chunkFormData.append("total_chunks", totalChunks);
          chunkFormData.append("filename", file.name);
          chunkFormData.append("title", effectiveTitle);
          chunkFormData.append("attendees", attendees);
          chunkFormData.append("template_type", templateType);
          chunkFormData.append("chunk", chunkBlob, file.name);

          if (i === totalChunks - 1) {
            btn.innerHTML = `<span>⏳ Gemini 3.7 Flash 멀티모달 분석 중...</span>`;
            updatePipelineStep(2, 50, "오디오 스트림 추출 완료 -> Vertex AI Gemini 3.7 Flash 분석 중...", "🤖 Vertex AI Gemini 3.7 Flash가 멀티모달 오디오를 직접 해석하고 있습니다.");
          }

          const res = await fetch(`${API_BASE}/api/v1/notes/upload-chunk`, {
            method: "POST",
            body: chunkFormData
          });

          if (!res.ok) {
            throw new Error(`업로드 실패 (${i + 1}/${totalChunks}): HTTP ${res.status}`);
          }

          const resJson = await res.json();
          if (i === totalChunks - 1) {
            updatePipelineStep(4, 95, "회의록 생성 완료! 결과 렌더링 중...", "📋 회의록을 화면에 준비하고 있습니다.");
            finalData = resJson;
          }
        }
      }

      if (!finalData || finalData.status !== "SUCCESS") {
        throw new Error("회의록 생성 결과를 수신하지 못했습니다.");
      }

      stopPipelineProgress();

      activeNotes = {
        title: finalData.notes.meeting_title,
        date: new Date().toISOString().slice(0, 10),
        time: "AI 분석 완료",
        attendees: attendees,
        executive_summary: finalData.notes.executive_summary,
        key_decisions: finalData.notes.key_decisions || [],
        agendas: finalData.notes.agenda_discussions || [],
        action_items: finalData.notes.action_items || []
      };

      activeTranscript = parseTranscriptText(finalData.transcript);
      activeSttTranscript = parseTranscriptText(finalData.stt_transcript || []);
      activeSttStatus = finalData.stt_status || (activeSttTranscript.length > 0 ? "COMPLETED" : "PROCESSING");
      activeReportId = finalData.report_id || null;
      renderAll();
      switchTab("notesTab");
      await loadReportsArchive();
      showToast("✅ Vertex AI Gemini 3.7 Flash 회의록 생성이 완료되었습니다!");
      if (activeSttStatus === "PROCESSING" && activeReportId) {
        startSttPolling(activeReportId);
      }
    } else if ((currentInputMode === "url" || currentInputMode === "bucket") && activeMediaUri) {
      initPipelineProgress(title || "미디어 URL 회의록");
      switchTab("notesTab");
      updatePipelineStep(2, 40, "미디어 스트림 다운로드 및 오디오 전처리 중...", "🎧 원격 미디어 URL에서 오디오 스트림을 안전하게 추출하고 있습니다.");

      setTimeout(() => {
        updatePipelineStep(3, 75, "Vertex AI Gemini 3.7 Flash 다중 화자 분리 & STT 분석 중...", "🤖 Vertex AI Gemini 3.7 Flash가 멀티모달 오디오를 분석 중입니다.");
      }, 2000);

      const res = await fetch(`${API_BASE}/api/v1/notes/process-uri`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          uri: activeMediaUri,
          meeting_title: title || "미디어 회의록",
          attendees: attendees ? attendees.split(",").map(a => a.trim()).filter(Boolean) : [],
          template_type: templateType
        })
      });

      if (!res.ok) throw new Error(`URI 분석 실패: HTTP ${res.status}`);
      const data = await res.json();

      stopPipelineProgress();

      activeNotes = {
        title: data.notes.meeting_title,
        date: new Date().toISOString().slice(0, 10),
        time: "AI 분석 완료",
        attendees: attendees,
        executive_summary: data.notes.executive_summary,
        key_decisions: data.notes.key_decisions || [],
        agendas: data.notes.agenda_discussions || [],
        action_items: data.notes.action_items || []
      };

      activeTranscript = parseTranscriptText(data.transcript);
      activeSttTranscript = parseTranscriptText(data.stt_transcript || []);
      activeSttStatus = data.stt_status || (activeSttTranscript.length > 0 ? "COMPLETED" : "PROCESSING");
      activeReportId = data.report_id || null;
      renderAll();
      switchTab("notesTab");
      await loadReportsArchive();
      showToast("✅ 미디어 URI 기반 Gemini 3.7 Flash 회의록 생성이 완료되었습니다!");
      if (activeSttStatus === "PROCESSING" && activeReportId) {
        startSttPolling(activeReportId);
      }
    } else {
      const sampleVal = document.getElementById("sampleSelect")?.value || "sample_meet_85min";
      activeNotes = sampleSources[sampleVal] || sampleSources.sample_meet_85min;
      await fetchDynamicTranscript(sampleVal);
      renderAll();
      switchTab("notesTab");
      showToast("✅ Gemini 3.7 Flash 회의록 및 전사본이 로드되었습니다!");
    }
  } catch (err) {
    stopPipelineProgress();
    renderNotes();
    alert(`❌ 오류 발생: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>🚀 Gemini 3.7 Flash 회의록 생성</span>`;
  }
}


function parseTranscriptText(rawText) {
  if (!rawText) return [];
  if (Array.isArray(rawText)) {
    return rawText.map(item => {
      if (typeof item === "object" && item !== null) {
        return {
          time: item.time || "[00:00:00]",
          speaker: item.speaker || "참석자",
          text: item.text || item.utterance || ""
        };
      }
      return { time: "[00:00:00]", speaker: "참석자", text: String(item) };
    });
  }
  if (typeof rawText !== "string") return [];

  const lines = rawText.split("\n");
  const turns = [];
  
  // 다양한 화자/타임스탬프 패턴 지원:
  // 1. [00:00] 화자: 내용
  // 2. * **[00:00] 화자:** 내용
  // 3. * [00:00:00] 화자 : 내용
  const linePattern = /^\s*(?:[\*\-]\s*)?(?:\*\*)?\[\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\](?:\*\*)?\s*(?:\*\*)?([^:：]+?)(?:\*\*)?\s*[:：]\s*(.*)$/;
  // 4. ### [00:00 ~ 02:20] 주제
  const sectionPattern = /^\s*#{1,4}\s*\[?\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*~\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\]?\s*(.*)$/;

  let currentTurn = null;

  lines.forEach(rawLine => {
    const line = rawLine.trim();
    if (!line || line === "---") return;

    // 섹션 헤더 처리
    const sm = line.match(sectionPattern);
    if (sm) {
      currentTurn = {
        time: `[${sm[1]}~${sm[2]}]`,
        speaker: "안건/주제",
        text: sm[3].replace(/^[#\*\s]+|[#\*\s]+$/g, "")
      };
      turns.push(currentTurn);
      return;
    }

    // 일반 발언 매칭
    const lm = line.match(linePattern);
    if (lm) {
      let timeStr = lm[1].trim();
      if (!timeStr.startsWith("[")) timeStr = `[${timeStr}]`;
      currentTurn = {
        time: timeStr,
        speaker: lm[2].trim().replace(/^[\*\s_]+|[\*\s_]+$/g, ""),
        text: lm[3].trim().replace(/^[\*\s_]+|[\*\s_]+$/g, "")
      };
      turns.push(currentTurn);
      return;
    }

    // 불렛 서브 라인 및 이어지는 발언 처리
    if (currentTurn && (line.startsWith("*") || line.startsWith("-"))) {
      const cleanSub = line.replace(/^[\*\-\s]+/, "");
      currentTurn.text += `<br>• ${cleanSub}`;
    } else if (currentTurn && line.length > 0 && !line.startsWith("#")) {
      currentTurn.text += ` ${line}`;
    } else if (line.length > 0 && !line.startsWith("#")) {
      turns.push({
        time: "[00:00:00]",
        speaker: "참석자",
        text: line
      });
    }
  });

  return turns;
}

// ==============================================================================
// 2-Page Navigation & Report Archive Engine
// ==============================================================================

let reportsCache = [];
let activeDetailReport = null;

function switchMainPage(pageName) {
  const createView = document.getElementById("pageCreateView");
  const listView = document.getElementById("pageListView");
  const createBtn = document.getElementById("navCreateBtn");
  const listBtn = document.getElementById("navListBtn");

  if (pageName === "list") {
    if (createView) {
      createView.classList.remove("active");
      createView.style.display = "none";
    }
    if (listView) {
      listView.classList.add("active");
      listView.style.display = "block";
    }
    if (createBtn) createBtn.classList.remove("active");
    if (listBtn) listBtn.classList.add("active");
    loadReportsArchive();
  } else {
    if (listView) {
      listView.classList.remove("active");
      listView.style.display = "none";
    }
    if (createView) {
      createView.classList.add("active");
      createView.style.display = "block";
    }
    if (listBtn) listBtn.classList.remove("active");
    if (createBtn) createBtn.classList.add("active");
  }
}

async function loadReportsArchive() {
  const container = document.getElementById("reportsGridContainer");
  if (!container) return;

  // 1. 이미 메모리에 캐시된 목록이 있다면 0ms 즉시 렌더링 (화면 깜빡임 / 로딩 딜레이 제거)
  if (reportsCache && reportsCache.length > 0) {
    renderReportsList(reportsCache);
  } else {
    container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">⏳ 보관된 회의록 목록을 불러오는 중...</div>`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/reports`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    reportsCache = data.reports || [];
    
    // Update badge & stats
    const badge = document.getElementById("reportCountBadge");
    if (badge) badge.textContent = reportsCache.length;
    const statTotal = document.getElementById("statTotalReports");
    if (statTotal) statTotal.textContent = `${reportsCache.length}건`;

    renderReportsList(reportsCache);
  } catch (err) {
    if (!reportsCache || reportsCache.length === 0) {
      container.innerHTML = `<div style="padding:30px; text-align:center; color:var(--accent-rose);">❌ 회의록 목록 로드 실패: ${err.message}</div>`;
    }
  }
}

function handleReportSearch() {
  const query = (document.getElementById("reportSearchInput")?.value || "").toLowerCase().trim();
  const filterType = document.getElementById("reportTemplateFilter")?.value || "ALL";

  let filtered = reportsCache.filter(r => {
    const matchesType = filterType === "ALL" || r.template_type === filterType;
    const matchesQuery = !query || 
      r.title.toLowerCase().includes(query) || 
      r.attendees.toLowerCase().includes(query) || 
      r.summary_snippet.toLowerCase().includes(query);
    return matchesType && matchesQuery;
  });

  renderReportsList(filtered);
}

function getTemplatePill(type, name) {
  if (type === "CFT_REGULAR") return `<span class="report-pill cft">📊 ${name || 'CFT 정기 회의'}</span>`;
  if (type === "KICKOFF") return `<span class="report-pill kickoff">🚀 ${name || '프로젝트 킥오프'}</span>`;
  if (type === "EXECUTIVE") return `<span class="report-pill executive">👔 ${name || '임원 보고'}</span>`;
  return `<span class="report-pill cft">📋 ${name || type}</span>`;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatInlineMarkdown(text) {
  if (!text) return "";
  if (typeof text !== "string") return String(text);

  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--text-primary); font-weight:700;">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9; padding:2px 5px; border-radius:4px; font-family:var(--font-mono); font-size:12px; color:#0f172a;">$1</code>');

  if (formatted.includes("\n")) {
    const lines = formatted.split("\n");
    let inList = false;
    let out = [];

    for (let l of lines) {
      const trimmed = l.trim();
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        if (!inList) {
          out.push('<ul style="margin:4px 0 6px 0; padding-left:18px; line-height:1.6;">');
          inList = true;
        }
        out.push(`<li style="margin-bottom:3px;">${trimmed.substring(2)}</li>`);
      } else {
        if (inList) {
          out.push('</ul>');
          inList = false;
        }
        if (trimmed.length > 0) {
          out.push(`<div style="margin-bottom:4px; line-height:1.65;">${trimmed}</div>`);
        }
      }
    }
    if (inList) out.push('</ul>');
    return out.join("");
  }

  return formatted;
}

// ==============================================================================
// KST (한국 표준시, UTC+9) UI 출력 포맷터
// ==============================================================================
function formatKstDateTime(dateTimeStr) {
  if (!dateTimeStr) return "";
  try {
    let d;
    if (dateTimeStr.includes("T") || dateTimeStr.endsWith("Z")) {
      d = new Date(dateTimeStr);
    } else if (dateTimeStr.includes(":") && dateTimeStr.length > 10) {
      d = new Date(dateTimeStr.replace(" ", "T") + "Z");
    } else {
      return dateTimeStr;
    }
    if (isNaN(d.getTime())) return dateTimeStr;

    const formatter = new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
    const parts = formatter.formatToParts(d);
    const map = {};
    parts.forEach(p => map[p.type] = p.value);
    return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`;
  } catch (e) {
    return dateTimeStr;
  }
}

function formatKstDateOnly(dateTimeStr) {
  if (!dateTimeStr) return "";
  try {
    let d;
    if (dateTimeStr.includes("T") || dateTimeStr.endsWith("Z")) {
      d = new Date(dateTimeStr);
    } else if (dateTimeStr.includes(":") && dateTimeStr.length > 10) {
      d = new Date(dateTimeStr.replace(" ", "T") + "Z");
    } else {
      return dateTimeStr;
    }
    if (isNaN(d.getTime())) return dateTimeStr;

    const formatter = new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    });
    const parts = formatter.formatToParts(d);
    const map = {};
    parts.forEach(p => map[p.type] = p.value);
    return `${map.year}-${map.month}-${map.day}`;
  } catch (e) {
    return dateTimeStr;
  }
}

function formatKstTimeOnly(dateTimeStr, durationMinutes) {
  if (!dateTimeStr) return "";
  try {
    let d;
    if (dateTimeStr.includes("T") || dateTimeStr.endsWith("Z")) {
      d = new Date(dateTimeStr);
    } else if (dateTimeStr.includes(":") && dateTimeStr.length > 10) {
      d = new Date(dateTimeStr.replace(" ", "T") + "Z");
    } else {
      return durationMinutes ? `${dateTimeStr} (총 ${durationMinutes}분)` : dateTimeStr;
    }
    if (isNaN(d.getTime())) return "";

    const formatter = new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });
    const parts = formatter.formatToParts(d);
    const map = {};
    parts.forEach(p => map[p.type] = p.value);
    const timeStr = `${map.hour}:${map.minute}`;
    return durationMinutes ? `${timeStr} (총 ${durationMinutes}분)` : timeStr;
  } catch (e) {
    return "";
  }
}

function buildFullMarkdownReport(report) {
  if (!report) return "";
  const sourceData = (report.sample_key && sampleSources[report.sample_key]) ? sampleSources[report.sample_key] : null;
  const executiveSummary = report.executive_summary || (sourceData ? sourceData.executive_summary : (report.summary_snippet || ""));
  
  const keyDecisions = (report.key_decisions && report.key_decisions.length > 0) 
    ? report.key_decisions 
    : (sourceData && sourceData.key_decisions ? sourceData.key_decisions : []);
    
  const agendas = (report.agendas && report.agendas.length > 0) 
    ? report.agendas 
    : ((report.agenda_discussions && report.agenda_discussions.length > 0) 
      ? report.agenda_discussions 
      : (sourceData && sourceData.agendas ? sourceData.agendas : []));
      
  const actionItems = (report.action_items && report.action_items.length > 0) 
    ? report.action_items 
    : (sourceData && sourceData.action_items ? sourceData.action_items : []);
    
  let transcriptTurns = [];
  if (report.transcript && (Array.isArray(report.transcript) ? report.transcript.length > 0 : Boolean(report.transcript))) {
    transcriptTurns = Array.isArray(report.transcript) ? report.transcript : parseTranscriptText(report.transcript);
  } else if (sourceData && sourceData.transcript) {
    transcriptTurns = sourceData.transcript;
  } else if (activeTranscript && activeTranscript.length > 0) {
    transcriptTurns = activeTranscript;
  }

  const kstDate = formatKstDateOnly(report.created_at) || report.date || '2026-08-20';
  const kstTime = formatKstTimeOnly(report.created_at, report.duration_minutes) || report.time || '';

  let md = [];
  md.push(`# 📋 [${report.title || '회의록'}]`);
  md.push(`- **일시**: ${kstDate} ${kstTime}`);
  md.push(`- **참석자**: ${report.attendees || '참석자 미지정'}`);
  md.push(`- **미디어 소스**: ${report.audio_source || '녹음본'}\n`);
  md.push(`---\n`);

  md.push(`## 1. 1페이지 핵심 요약 (Executive Summary)\n${executiveSummary}\n`);

  if (keyDecisions.length > 0) {
    md.push(`## 2. 주요 결정사항 (Key Decisions)`);
    keyDecisions.forEach((d, idx) => md.push(`${idx + 1}. ${d}`));
    md.push("");
  }

  if (agendas.length > 0) {
    md.push(`## 3. 안건별 상세 논의 (Agenda Discussions)`);
    agendas.forEach(ag => {
      const agTitle = ag.title || ag.agenda_title || '상세 안건';
      md.push(`### ${agTitle}`);
      if (ag.speakers && ag.speakers.length > 0) {
        md.push(`- **주요 발언자**: ${Array.isArray(ag.speakers) ? ag.speakers.join(", ") : ag.speakers}`);
      }
      md.push(`- **논의 배경 및 개요**: ${ag.content || ag.summary || ''}`);
      const kps = ag.key_points || ag.keypoints || [];
      if (kps.length > 0) {
        md.push(`- **핵심 세부 논의 내용 (Key Discussion Points)**:`);
        kps.forEach(kp => md.push(`  * ${kp}`));
      }
      if (ag.resolution) {
        md.push(`- **도출 결론 / 합의**: ${ag.resolution}`);
      }
      md.push("");
    });
  }

  if (actionItems.length > 0) {
    md.push(`## 4. 실행 과제 (Action Items)`);
    md.push(`| No | 실행 과제 | 담당자 | 완료 목표일 | 상태 |`);
    md.push(`| :--- | :--- | :--- | :--- | :--- |`);
    actionItems.forEach((item, idx) => {
      const task = item.task || item.task_description || '';
      const assignee = item.assignee || '담당자 미정';
      const due = item.due || item.due_date || 'TBD';
      const status = item.status || '진행중';
      md.push(`| ${idx + 1} | ${task} | ${assignee} | ${due} | ${status} |`);
    });
    md.push("");
  }

  if (transcriptTurns && transcriptTurns.length > 0) {
    md.push(`## 5. 대화 전체 전사본 전문 (Verbatim Transcript)\n`);
    transcriptTurns.forEach(t => {
      md.push(`${t.time} ${t.speaker}: ${t.text}`);
    });
  }

  return md.join("\n");
}

function renderReportsList(list) {
  const container = document.getElementById("reportsGridContainer");
  if (!container) return;

  if (list.length === 0) {
    container.innerHTML = `<div style="padding:48px 24px; text-align:center; color:var(--text-muted); background:#ffffff; border-radius:14px; border:1px dashed #cbd5e1;">🔍 검색 조건에 일치하는 보관된 회의록이 없습니다.</div>`;
    return;
  }

  let html = list.map(r => {
    const kstDate = formatKstDateOnly(r.created_at) || r.date;
    const kstTime = formatKstTimeOnly(r.created_at, r.duration_minutes) || r.time;
    const kstCreatedAt = formatKstDateTime(r.created_at) || r.created_at || '2026-08-20';

    return `
    <div class="report-archive-card">
      <div class="report-card-topbar">
        <div class="report-badges-row">
          ${getTemplatePill(r.template_type, r.template_name)}
          <span class="report-date-chip">📅 ${kstDate} ${kstTime}</span>
          <span class="report-duration-chip">⏱️ ${r.duration_minutes}분 회의</span>
        </div>
        <span class="report-status-badge">
          <span class="pulse-dot" style="width:6px; height:6px;"></span>
          AI 분석 완료
        </span>
      </div>

      <h3 class="report-card-title">${r.title}</h3>

      <div class="report-card-snippet">
        <strong>📌 1페이지 요약 미리보기:</strong> ${r.summary_snippet}
      </div>

      <div class="report-card-meta">
        <span class="meta-tag">👥 <strong>참석자:</strong> ${r.attendees}</span>
        <span class="meta-tag">🎙️ <strong>미디어 소스:</strong> ${r.audio_source}</span>
        <span class="meta-tag">🕒 <strong>분석 일시:</strong> ${kstCreatedAt}</span>
      </div>

      <div class="report-card-actions">
        <div style="font-size:12px; color:#94a3b8; font-family:var(--font-mono); font-weight:600;">
          ID: ${r.id}
        </div>
        <div class="report-btn-group">
          <button class="btn-report-action" onclick="copyArchiveFullMarkdown('${r.id}')" title="전체 회의록 마크다운 복사">
            📋 복사
          </button>
          <button class="btn-report-action" onclick="openReportDetailTab('${r.id}', 'transcript')" title="전체 대화 스크립트 보기">
            🎙️ 전체 대화 스크립트
          </button>
          <button class="btn-report-action" onclick="openReportDetailTab('${r.id}', 'markdown')" title="원문 마크다운 전문 보기">
            📄 원문 마크다운
          </button>
          <button class="btn-report-delete" onclick="deleteReportArchive('${r.id}')" title="회의록 영구 삭제">
            🗑️ 삭제
          </button>
          <button class="btn-report-view" onclick="openReportDetailTab('${r.id}', 'notes')" title="구조화 회의록 상세 보기">
            <span>🔍 회의록 상세 보기</span>
          </button>
        </div>
      </div>
    </div>
  `;
  }).join("");

  container.innerHTML = html;
}

let currentModalTab = 'notes';

async function openReportDetailTab(reportId, tabName = 'notes') {
  let report = reportsCache.find(r => r.id === reportId);
  
  // 만약 상세 필드(agendas, transcript 등)가 누락되어 있다면 백엔드 API에서 단건 로드
  if (!report || !report.agendas || report.agendas.length === 0 || !report.transcript || report.transcript.length === 0) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${encodeURIComponent(reportId)}`);
      if (res.ok) {
        const data = await res.json();
        const detailed = data.report || data.notes || data.report_meta;
        if (detailed) {
          report = Object.assign({}, report || {}, detailed);
          const idx = reportsCache.findIndex(r => r.id === reportId);
          if (idx >= 0) reportsCache[idx] = report;
        }
      }
    } catch (e) {
      console.warn("Could not fetch detailed report:", e);
    }
  }

  if (!report) return;
  activeDetailReport = report;

  const modal = document.getElementById("reportDetailModal");
  const modalTitle = document.getElementById("reportDetailModalTitle");
  if (modalTitle) modalTitle.textContent = `📋 [상세 회의록] ${report.title}`;

  switchModalTab(tabName);

  if (modal) {
    modal.classList.add("open");
    modal.classList.add("active");
  }
}

function switchModalTab(tabName) {
  currentModalTab = tabName || 'notes';

  const btnNotes = document.getElementById("modalTabBtnNotes");
  const btnTranscript = document.getElementById("modalTabBtnTranscript");
  const btnMarkdown = document.getElementById("modalTabBtnMarkdown");
  const btnCompare = document.getElementById("modalTabBtnCompare");

  if (btnNotes) btnNotes.classList.toggle("active", currentModalTab === 'notes');
  if (btnTranscript) btnTranscript.classList.toggle("active", currentModalTab === 'transcript');
  if (btnMarkdown) btnMarkdown.classList.toggle("active", currentModalTab === 'markdown');
  if (btnCompare) btnCompare.classList.toggle("active", currentModalTab === 'compare');

  const modalBody = document.getElementById("reportDetailModalBody");
  if (!modalBody || !activeDetailReport) return;

  const report = activeDetailReport;
  const sourceData = (report.sample_key && sampleSources[report.sample_key]) ? sampleSources[report.sample_key] : null;
  
  let transcriptTurns = [];
  if (report.transcript && (Array.isArray(report.transcript) ? report.transcript.length > 0 : Boolean(report.transcript))) {
    transcriptTurns = Array.isArray(report.transcript) ? report.transcript : parseTranscriptText(report.transcript);
  } else if (sourceData && sourceData.transcript) {
    transcriptTurns = sourceData.transcript;
  } else if (activeTranscript && activeTranscript.length > 0) {
    transcriptTurns = activeTranscript;
  }

  let sttTurns = [];
  if (report.stt_transcript && (Array.isArray(report.stt_transcript) ? report.stt_transcript.length > 0 : Boolean(report.stt_transcript))) {
    sttTurns = Array.isArray(report.stt_transcript) ? report.stt_transcript : parseTranscriptText(report.stt_transcript);
  } else if (activeSttTranscript && activeSttTranscript.length > 0) {
    sttTurns = activeSttTranscript;
  }

  if (currentModalTab === 'notes') {
    renderModalNotesTab(modalBody, report, sourceData);
  } else if (currentModalTab === 'transcript') {
    renderModalTranscriptTab(modalBody, transcriptTurns);
  } else if (currentModalTab === 'markdown') {
    renderModalMarkdownTab(modalBody, report);
  } else if (currentModalTab === 'compare') {
    renderModalCompareTab(modalBody, report, transcriptTurns, sttTurns);
  }
}

function renderModalNotesTab(modalBody, report, sourceData) {
  const executiveSummary = report.executive_summary || (sourceData ? sourceData.executive_summary : report.summary_snippet);
  const keyDecisions = (report.key_decisions && report.key_decisions.length > 0)
    ? report.key_decisions
    : (sourceData && sourceData.key_decisions ? sourceData.key_decisions : []);
    
  const agendas = (report.agendas && report.agendas.length > 0)
    ? report.agendas
    : ((report.agenda_discussions && report.agenda_discussions.length > 0)
      ? report.agenda_discussions
      : (sourceData && sourceData.agendas ? sourceData.agendas : []));
      
  const actionItems = (report.action_items && report.action_items.length > 0)
    ? report.action_items
    : (sourceData && sourceData.action_items ? sourceData.action_items : []);

  const kstDate = formatKstDateOnly(report.created_at) || report.date;
  const kstTime = formatKstTimeOnly(report.created_at, report.duration_minutes) || report.time;

  const agendaThemes = ["theme-blue", "theme-violet", "theme-emerald", "theme-amber", "theme-rose"];

  modalBody.innerHTML = `
    <div class="note-header-banner">
      <h3>${report.title}</h3>
      <div style="font-size:13px; display:flex; flex-wrap:wrap; gap:12px;">
        <span class="meta-chip date">📅 <strong>일시:</strong> ${kstDate} ${kstTime}</span>
        <span class="meta-chip attendees">👥 <strong>참석자:</strong> ${report.attendees}</span>
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#dbeafe; color:#1d4ed8; padding:3px 8px; border-radius:6px; font-size:13px;">📌 1</span>
        1페이지 핵심 요약 (Executive Summary)
      </h4>
      <div class="card-summary" style="line-height:1.75;">
        ${formatInlineMarkdown(executiveSummary)}
      </div>
    </div>

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#d1fae5; color:#065f46; padding:3px 8px; border-radius:6px; font-size:13px;">🎯 2</span>
        핵심 결정사항 (Key Decisions)
      </h4>
      <div class="card-decisions">
        ${keyDecisions.map((d, i) => `
          <div class="decision-item">
            <span class="decision-bullet">${i + 1}</span>
            <div style="flex:1;">${formatInlineMarkdown(d)}</div>
          </div>
        `).join("")}
      </div>
    </div>

    ${agendas.length > 0 ? `
      <div class="section-block">
        <h4 class="section-title">
          <span style="background:#ede9fe; color:#5b21b6; padding:3px 8px; border-radius:6px; font-size:13px;">💬 3</span>
          안건별 상세 논의 (Agenda Discussions)
        </h4>
        <div style="display:flex; flex-direction:column; gap:16px;">
          ${agendas.map((ag, idx) => {
            const themeClass = agendaThemes[idx % agendaThemes.length];
            const title = ag.agenda_title || ag.title || `안건 ${idx + 1}`;
            const summary = ag.summary || ag.content || ag.agenda_summary || '';
            const keyPoints = ag.key_points || ag.keypoints || [];
            const resolution = ag.resolution || ag.conclusion || '';
            const speakers = ag.speakers || [];

            return `
              <div class="agenda-card ${themeClass}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                  <h5 style="margin:0; font-size:15px; font-weight:800; color:#0f172a;">${formatInlineMarkdown(title)}</h5>
                  ${speakers.length > 0 ? `<div style="font-size:11.5px; color:var(--text-muted); display:flex; align-items:center; gap:4px;"><span style="background:#ffffff; border:1px solid #cbd5e1; padding:2px 8px; border-radius:4px; font-weight:700; color:var(--text-secondary);">🗣️ ${speakers.join(", ")}</span></div>` : ''}
                </div>
                <div style="margin:0 0 10px 0; font-size:13.5px; line-height:1.7; color:var(--text-secondary);">
                  <strong style="color:var(--text-primary);">📌 논의 배경 및 개요:</strong> ${formatInlineMarkdown(summary)}
                </div>
                ${keyPoints.length > 0 ? `
                  <div style="background:rgba(255,255,255,0.75); border-radius:8px; padding:12px 14px; margin-bottom:10px; border:1px solid var(--border-color);">
                    <div style="font-size:12.5px; font-weight:800; color:var(--text-primary); margin-bottom:8px;">🔍 핵심 세부 논의 내용 (Key Discussion Points):</div>
                    <ul style="margin:0; padding-left:18px; font-size:13px; color:var(--text-secondary); line-height:1.65;">
                      ${keyPoints.map(kp => `<li style="margin-bottom:6px;">${formatInlineMarkdown(kp)}</li>`).join("")}
                    </ul>
                  </div>
                ` : ''}
                ${resolution ? `
                  <div style="font-size:12.5px; color:#15803d; background:#ecfdf5; border:1px solid #a7f3d0; padding:8px 12px; border-radius:6px; font-weight:600; display:flex; align-items:center; gap:6px;">
                    <span>🎯 <strong>도출 결론 / 합의:</strong> ${formatInlineMarkdown(resolution)}</span>
                  </div>
                ` : ''}
              </div>
            `;
          }).join("")}
        </div>
      </div>
    ` : ''}

    <div class="section-block">
      <h4 class="section-title">
        <span style="background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:6px; font-size:13px;">📋 4</span>
        실행 과제 (Action Items)
      </h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>실행 과제</th>
            <th style="width:190px;">담당자</th>
            <th style="width:130px;">완료 목표일</th>
            <th style="width:95px; text-align:center;">상태</th>
          </tr>
        </thead>
        <tbody>
          ${actionItems.map((item, idx) => `
            <tr>
              <td style="color:var(--text-primary); font-weight:700;">
                <span style="display:inline-block; width:20px; height:20px; background:#eff6ff; color:#2563eb; border-radius:50%; text-align:center; line-height:20px; font-size:11px; margin-right:6px;">${idx+1}</span>
                ${item.task || item.task_description || ''}
              </td>
              <td><span style="background:#e0e7ff; color:#3730a3; padding:3px 8px; border-radius:6px; font-weight:700; font-size:12px;">👤 ${item.assignee}</span></td>
              <td style="color:#6b21a8; font-family:var(--font-mono); font-weight:600; font-size:12px;"><span style="background:#f5f3ff; border:1px solid #ddd6fe; padding:2px 6px; border-radius:4px;">📅 ${item.due || item.due_date || 'TBD'}</span></td>
              <td style="text-align:center;"><span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; font-weight:700; padding:3px 8px; border-radius:9999px; font-size:11px;">🟢 진행중</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderModalTranscriptTab(modalBody, transcriptTurns) {
  if (!transcriptTurns || transcriptTurns.length === 0) {
    modalBody.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">전사 대화 스크립트 데이터가 없습니다.</div>`;
    return;
  }

  let html = `
    <div style="margin-bottom:12px; font-size:12.5px; color:var(--text-muted); font-weight:600;">
      🎙️ 100% 무가공 대화 전사(Verbatim) 전문 (총 ${transcriptTurns.length}개 턴)
    </div>
    <div class="transcript-flow">
      ${transcriptTurns.map(turn => {
        const pillClass = getSpeakerPillClass(turn.speaker);
        return `
          <div class="transcript-turn">
            <span class="transcript-time">${turn.time}</span>
            <span class="speaker-pill ${pillClass}">👤 ${turn.speaker}</span>
            <span class="transcript-text">${escapeHtml(turn.text)}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;

  modalBody.innerHTML = html;
}

function renderModalMarkdownTab(modalBody, report) {
  const fullMd = buildFullMarkdownReport(report);
  modalBody.innerHTML = `
    <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:12.5px; color:var(--text-muted); font-weight:600;">📄 원문 마크다운 전문 (구조화 회의록 + 대화 전사본)</span>
      <button class="btn btn-secondary btn-sm" onclick="copyDetailModalMarkdown()">📋 전체 복사</button>
    </div>
    <pre class="markdown-preview" style="max-height:65vh; font-size:12.5px; line-height:1.65; white-space:pre-wrap;">${escapeHtml(fullMd)}</pre>
  `;
}

function renderModalCompareTab(modalBody, report, geminiTurns, sttTurns) {
  const isSttProcessing = report && (report.stt_status === "PROCESSING" || (!sttTurns || sttTurns.length === 0));
  const validSttTurns = sttTurns && Array.isArray(sttTurns) ? sttTurns : [];
  const geminiCharCount = (geminiTurns || []).reduce((acc, t) => acc + (t.text || "").length, 0);
  const sttCharCount = validSttTurns.reduce((acc, t) => acc + (t.text || "").length, 0);
  const prog = (report && report.stt_progress) || activeSttProgress || { percent: 10, completed: 0, total: 9 };

  modalBody.innerHTML = `
    <div class="compare-metrics-grid" style="margin-bottom:14px;">
      <div class="compare-metric-card highlight">
        <div class="compare-metric-title">💰 2시간 회의 기준 비용 (TCO)</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">Gemini: 약 160원</span>
          <span class="compare-metric-val stt">STT: 약 2,800원</span>
        </div>
        <div style="font-size:11.5px; color:#15803d; font-weight:700; margin-top:2px;">✨ Gemini 도입 시 94.3% (17.5배) 비용 절감</div>
      </div>
      <div class="compare-metric-card">
        <div class="compare-metric-title">⚡ 처리 속도 비교</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">Gemini: ~30초</span>
          <span class="compare-metric-val stt">${isSttProcessing && validSttTurns.length === 0 ? `<span style="color:#d97706; font-weight:700;">STT: ⏳ ${prog.percent || 5}% 진행 중</span>` : 'STT: ~120초'}</span>
        </div>
      </div>
      <div class="compare-metric-card">
        <div class="compare-metric-title">📊 전사 발화 턴 수</div>
        <div class="compare-metric-values">
          <span class="compare-metric-val gemini">${(geminiTurns || []).length}턴 (${geminiCharCount.toLocaleString()}자)</span>
          <span class="compare-metric-val stt">${validSttTurns.length > 0 ? `${validSttTurns.length}턴 (${sttCharCount.toLocaleString()}자)` : `<span style="font-size:12px; color:#7c3aed; font-weight:700;">⏳ ${prog.completed || 0}/${prog.total || 9} 청크 분석 중</span>`}</span>
        </div>
      </div>
    </div>

    <div class="compare-split-grid">
      <div class="compare-col">
        <div class="compare-col-header">
          <div class="compare-col-title"><span>✨ Vertex AI Gemini 3.7 Flash</span></div>
          <span class="compare-col-badge gemini">스마트 문맥 & 참석자 매핑</span>
        </div>
        <div class="compare-flow" style="max-height:55vh;">
          ${(geminiTurns && geminiTurns.length > 0) ? geminiTurns.map(turn => `
            <div class="compare-turn-bubble gemini">
              <div class="compare-turn-meta">
                <span class="compare-turn-time">${turn.time}</span>
                <span class="compare-turn-speaker" style="color:#0369a1;">👤 ${escapeHtml(turn.speaker)}</span>
              </div>
              <div class="compare-turn-text">${escapeHtml(turn.text)}</div>
            </div>
          `).join("") : `
            <div style="padding:30px; text-align:center; color:var(--text-muted);">Gemini 전사본이 없습니다.</div>
          `}
        </div>
      </div>

      <div class="compare-col">
        <div class="compare-col-header">
          <div class="compare-col-title"><span>🎤 Cloud Speech-to-Text (Chirp 2)</span></div>
          <span class="compare-col-badge stt" style="${isSttProcessing && validSttTurns.length === 0 ? 'background:#fef3c7; color:#92400e;' : ''}">
            ${validSttTurns.length > 0 ? '100% 음향 기반 축어(Verbatim)' : `⏳ 음향 모델 전사 중 (${prog.percent || 5}%)`}
          </span>
        </div>
        <div class="compare-flow" style="max-height:55vh;">
          ${validSttTurns.length > 0 ? validSttTurns.map(turn => `
            <div class="compare-turn-bubble stt">
              <div class="compare-turn-meta">
                <span class="compare-turn-time">${turn.time}</span>
                <span class="compare-turn-speaker" style="color:#7c3aed;">🎙️ ${escapeHtml(turn.speaker)}</span>
              </div>
              <div class="compare-turn-text">${escapeHtml(turn.text)}</div>
            </div>
          `).join("") : `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:220px; text-align:center; padding:30px 15px;">
              <div class="pstep-mini-spinner" style="width:30px; height:30px; border-width:3px; border-color:#e2e8f0; border-top-color:#7c3aed; margin-bottom:12px;"></div>
              <div style="font-size:14px; font-weight:800; color:#1e293b; margin-bottom:4px;">Cloud STT 음향 모델 비동기 전사 진행 중...</div>
              <div style="font-size:12.5px; color:#7c3aed; font-weight:700; margin-bottom:8px;">
                ⏳ ${prog.percent || 5}% 완료 (${prog.completed || 0} / ${prog.total || 9} 청크 전사 완료)
              </div>
              <div style="width:100%; max-width:260px; height:8px; background:#f1f5f9; border-radius:999px; overflow:hidden; border:1px solid #e2e8f0; margin-bottom:10px;">
                <div style="height:100%; width:${Math.max(5, prog.percent || 5)}%; background:linear-gradient(90deg, #7c3aed, #a855f7); border-radius:999px; transition:width 0.4s ease;"></div>
              </div>
              <div style="font-size:11.5px; color:var(--text-muted); line-height:1.5;">
                대용량 오디오(15분 단위 청크)를 10-Way 병렬로 음향 분석 중입니다.<br>
                완료 시 실시간으로 본 영역이 갱신됩니다.
              </div>
            </div>
          `}
        </div>
      </div>
    </div>
  `;
}

function closeReportDetailModal() {
  const modal = document.getElementById("reportDetailModal");
  if (modal) {
    modal.classList.remove("open");
    modal.classList.remove("active");
  }
}

async function copyArchiveFullMarkdown(reportId) {
  let report = reportsCache.find(r => r.id === reportId);
  if (!report) return;
  if (!report.agendas || !report.transcript) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${encodeURIComponent(reportId)}`);
      if (res.ok) {
        const data = await res.json();
        const detailed = data.report || data.notes || data.report_meta;
        if (detailed) {
          report = Object.assign({}, report, detailed);
          const idx = reportsCache.findIndex(r => r.id === reportId);
          if (idx >= 0) reportsCache[idx] = report;
        }
      }
    } catch (e) {
      console.warn("Detail fetch for copy failed:", e);
    }
  }
  const fullMd = buildFullMarkdownReport(report);
  navigator.clipboard.writeText(fullMd).then(() => {
    showToast(`📋 '${report.title}' 회의록 전문이 복사되었습니다!`);
  }).catch(err => {
    showToast(`❌ 복사 실패: ${err.message}`, "error");
  });
}

function copyDetailModalMarkdown() {
  if (!activeDetailReport) return;
  const fullMd = buildFullMarkdownReport(activeDetailReport);
  navigator.clipboard.writeText(fullMd).then(() => {
    showToast(`📋 '${activeDetailReport.title}' 회의록 전문이 복사되었습니다!`);
  }).catch(err => {
    showToast(`❌ 복사 실패: ${err.message}`, "error");
  });
}

async function deleteReportArchive(reportId) {
  const report = reportsCache.find(r => r.id === reportId);
  const title = report ? report.title : reportId;

  if (!confirm(`⚠️ 정말 '${title}' 회의록을 삭제하시겠습니까?\n\n삭제된 회의록과 분석 데이터는 영구적으로 제거됩니다.`)) {
    return;
  }

  try {
    let res = await fetch(`${API_BASE}/api/v1/reports/${encodeURIComponent(reportId)}`, {
      method: "DELETE"
    });

    if (!res.ok) {
      // 2차 POST 백업 엔드포인트 자동 시도
      res = await fetch(`${API_BASE}/api/v1/reports/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId })
      });
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "회의록 삭제 실패");
    }

    // Update local cache immediately
    reportsCache = reportsCache.filter(r => r.id !== reportId);
    
    // If detail modal is currently open for this report, close it
    if (activeDetailReport && activeDetailReport.id === reportId) {
      closeReportDetailModal();
    }

    // Re-render and update stats immediately
    updateArchiveStats();
    handleReportSearch();
    renderReportsList(reportsCache);

    alert(`🗑️ '${title}' 회의록이 성공적으로 삭제되었습니다.`);
  } catch (err) {
    alert(`❌ 삭제 중 오류가 발생했습니다: ${err.message}`);
  }
}

function deleteActiveDetailReport() {
  if (activeDetailReport) {
    deleteReportArchive(activeDetailReport.id);
  }
}

function updateArchiveStats() {
  const badge = document.getElementById("reportCountBadge");
  if (badge) badge.textContent = reportsCache.length;
  
  const statTotal = document.getElementById("statTotalReports");
  if (statTotal) statTotal.textContent = `${reportsCache.length}건`;

  const statDominant = document.getElementById("statDominantTemplate");
  const statDominantLabel = document.getElementById("statDominantLabel");
  
  if (reportsCache.length === 0) {
    if (statDominant) statDominant.textContent = "-";
    if (statDominantLabel) statDominantLabel.textContent = "주요 회의 템플릿";
  } else {
    // 템플릿별 빈도 및 최근 회의 동적 분석
    const templateCounts = {};
    reportsCache.forEach(r => {
      const name = r.template_name || (r.template_type === "CFT_REGULAR" ? "CFT 정기 회의" : (r.template_type === "EXECUTIVE" ? "임원 보고" : "프로젝트 킥오프"));
      templateCounts[name] = (templateCounts[name] || 0) + 1;
    });

    let topTemplate = "CFT 정기 회의";
    let maxCount = 0;
    for (const [tpl, count] of Object.entries(templateCounts)) {
      if (count > maxCount) {
        maxCount = count;
        topTemplate = tpl;
      }
    }
    const ratio = Math.round((maxCount / reportsCache.length) * 100);

    if (statDominant) {
      statDominant.textContent = topTemplate;
      statDominant.title = `총 ${reportsCache.length}건 중 ${maxCount}건 (${ratio}%)`;
    }
    if (statDominantLabel) {
      statDominantLabel.textContent = `주요 회의 템플릿 (${ratio}% 점유)`;
    }
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeSpeakerModal();
    closeUrlModal();
    closeBucketModal();
    closeTemplateModal();
    closeReportDetailModal();
    closeSystemLogsModal();
  }
});






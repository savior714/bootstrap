# 🗺️ Project Blueprint: AI_GUIDELINES.md 고도화 및 강화

> 생성 일시: 2026-03-17 17:39 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **AI_GUIDELINES.md**를 시니어 아키텍트 관점의 'Deep-Dive Version'으로 전면 개정하여 에이전트의 안정성, 정합성, 그리고 장애 대응 능력을 극대화함.
- **핵심 가치**: Stale(구형 데이터) 버그 차단, 터미널 환경 격리강화, 그리고 `docs/CRITICAL_LOGIC.md`와의 SSOT 동기화 프로세스 정립.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: AI_GUIDELINES.md 백업 및 초기 분석**
  - **Tool**: `run_command`
  - **CommandLine**: `Copy-Item -Path 'c:\develop\bootstrap\AI_GUIDELINES.md' -Destination 'c:\develop\bootstrap\AI_GUIDELINES.md.bak'`
  - **Goal**: 원본 파일 보존 및 구조적 변경점 최종 확정.
  - **Dependency**: None

- [x] **Task 2: AI_GUIDELINES.md 내용 전면 개정**
  - **Tool**: `write_to_file`
  - **TargetFile**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 사용자 제공 'Deep-Dive Version'의 모든 섹션을 반영하여 파일 갱신.
  - **Pseudocode**:
    ```markdown
    # 🤖 AI Behavioral Guidelines (Senior Architect’s Deep-Dive Version)
    ... (사용자 제공 섹션 0~5 및 Handoff 반영) ...
    ```
  - **Dependency**: Task 1

- [x] **Task 3: 개정된 가이드라인 무결성 검증**
  - **Tool**: `run_command`
  - **CommandLine**: `powershell.exe -NoProfile -Command "Get-Content 'c:\develop\bootstrap\AI_GUIDELINES.md' | Select-Object -First 10"`
  - **Goal**: 파일 인코딩(UTF-8 no BOM) 및 첫 섹션 정상 기록 여부 확인.
  - **Dependency**: Task 2

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: UTF-8 no BOM (PowerShell에서는 UTF-8로 처리).
- **SSOT Alignment**: `docs/CRITICAL_LOGIC.md`가 존재하지 않을 경우, 향후 생성 제안을 포함함.
- **Microtask**: 각 태스크는 독립적으로 실행하며 사용자 승인을 득함.

## ✅ Definition of Done

1. [ ] `AI_GUIDELINES.md`가 새로운 'Deep-Dive Version'으로 완전히 교체됨.
2. [ ] 새로운 규칙에 따라 `node_modules`, `.git` 등 격리 경로가 명시됨.
3. [ ] `memory.md`에 가이드라인 업데이트 사실이 기록됨.

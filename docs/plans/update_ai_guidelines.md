# 🗺️ Project Blueprint: AI 행동 지침 심화 버전 반영 (`AI_GUIDELINES.md`)

> 생성 일시: 2026-03-17 14:32 | 상태: 완료

## 🎯 Architectural Goal

- `AI_GUIDELINES.md`를 시니어 아키텍트의 심화 버전으로 전면 개정하여 에이전트의 기술적 판단 기준을 고도화합니다.
- **SSOT**: 본 문서는 모든 행동 규칙의 근간이며, `docs/memory.md`와 상호 보완적으로 작동해야 합니다.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: AI_GUIDELINES.md 읽기 — 현재 가이드라인 분석**
  - **Tool**: `Read`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 기존 지침 중 유지해야 할 맥락과 심화 버전과의 차이점 식별 (완료)

- [x] **Task 2: AI_GUIDELINES.md 전면 개정**
  - **Tool**: `Write` (Overwrite)
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 요청받은 심화 버전의 기술 지침을 적용하여 문서를 최신화함.
  - **Instruction**: 제공된 마크다운 텍스트를 `UTF-8 no BOM` 인코딩으로 저장.

- [x] **Task 3: .antigravityrules 정렬 및 검증**
  - **Tool**: `Read` & `Edit`
  - **Target**: `c:\develop\bootstrap\.antigravityrules`
  - **Goal**: 가이드라인 개정에 따라 런타임 제약 설정이 필요한 부분이 있는지 검토하고 업데이트함.

- [x] **Task 4: SSOT 동기화 (memory.md)**
  - **Tool**: `Edit`
  *   **Target**: `c:\develop\bootstrap\docs\memory.md`
  - **Goal**: 가이드라인 대개정 사실을 기록하고 다음 세션으로 기술 부채가 전이되지 않도록 요약함.

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: `UTF-8 no BOM`을 반드시 준수합니다.
- **Consistency**: 수정 후 반드시 `scripts/check-env.ps1` (존재 시)을 실행하여 시스템 일관성을 확인합니다.

## ✅ Definition of Done

1. [x] `AI_GUIDELINES.md`가 요청된 'Deep-Dive Version'으로 완벽하게 교체됨.
2. [x] 관련 런타임 규칙 파일(`.antigravityrules`)과의 충돌 없음.
3. [x] `memory.md`에 변경 사항 및 결정 근거가 기록됨.

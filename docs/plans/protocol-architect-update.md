# 🗺️ Project Blueprint: Protocol-Architect-Update

> 생성 일시: 2026-03-15 07:55 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- 사용자로부터 제공받은 **Antigravity IDE Agent Terminal Protocol (Architect Version)**의 핵심 내용을 기존 **AI_GUIDELINES.md** 및 **CRITICAL_LOGIC.md**에 정밀하게 통합합니다.
- 단순한 복사-붙여넣기가 아닌, 기존 규칙과의 충돌을 방지하고 상호 보완적인 구조로 재배치하여 **에이전트의 동작 안정성**과 **코드 무결성**을 극대화합니다.
- **SSOT 정렬**: `AI_GUIDELINES.md` (동작 지침), `CRITICAL_LOGIC.md` (기술 사양), `memory.md` (진행 상태) 간의 일관성을 확보합니다.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: AI_GUIDELINES.md 고도화 — Protocol 통합**
  - **Tool**: `Replace`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 제공된 8가지 섹션의 세부 수칙(Import 보존, AST 파싱, 캐싱 전략 등)을 기존 섹션에 녹여내거나 신규 섹션으로 추가함.
  - **Dependency**: None

- [x] **Task 2: docs/CRITICAL_LOGIC.md 업데이트 — 기술 사양 정밀화**
  - **Tool**: `Replace`
  - **Target**: `c:\develop\bootstrap\docs\CRITICAL_LOGIC.md`
  - **Goal**: Section 8(Terminal Protocol) 및 Section 10(Encoding)에 신규 프로토콜의 기술적 디테일(AST 파싱 코드, NoProfile 강조 등)을 반영함.
  - **Dependency**: Task 1

- [x] **Task 3: templates/AI_GUIDELINES.md 동기화**
  - **Tool**: `Write`
  - **Target**: `c:\develop\bootstrap\templates\AI_GUIDELINES.md`
  - **Goal**: 마스터 지침의 변경 사항을 배포용 템플릿에도 동일하게 적용하여 타 프로젝트 전파 준비를 완료함.
  - **Dependency**: Task 1

- [x] **Task 4: scripts/init-terminal.ps1 검토 및 보완 (선택적)**
  - **Tool**: `Read` 후 `Edit`
  - **Target**: `c:\develop\bootstrap\scripts\init-terminal.ps1`
  - **Goal**: 신규 프로토콜에서 강조된 세션 초기화 로직($env:TERM='dumb' 등)이 누락되어 있다면 보완함.
  - **Dependency**: Task 2

- [x] **Task 5: docs/memory.md 및 최종 보고**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\docs\memory.md`
  - **Goal**: 프로토콜 고도화 완료 사항을 기록하고 최종 결과 요약.
  - **Dependency**: Task 3

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Surgical Changes**: 기존 섹션 구조를 최대한 유지하면서 내용을 풍성하게 만듭니다.
- **PowerShell AST**: 단순 `[scriptblock]::Create()` 대신 `[System.Management.Automation.Language.Parser]::ParseInput()` 사용을 권장합니다.
- **Encoding**: 모든 소스 파일은 **UTF-8 no BOM**을 고수합니다.

## ✅ Definition of Done

1. [x] `AI_GUIDELINES.md` 섹션들이 Architect Version의 모든 핵심 가치를 포함함.
2. [x] `CRITICAL_LOGIC.md`와 `templates/` 파일들이 마스터 지침과 100% 동기화됨.
3. [x] 모든 수정 사항에 대해 구문 에러가 없음을 확인함.
4. [x] `memory.md`에 작업 로그가 최신화됨.

---
[BLUEPRINT CHECKLIST]
- [x] Task 1 진행 요청
- [x] 전체 계획 수정 요청

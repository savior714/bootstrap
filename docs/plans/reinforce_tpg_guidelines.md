# 🗺️ Project Blueprint: Terminal Parsing Guard (TPG) Reinforcement
 
> 생성 일시: 2026-03-16 17:56 | 상태: 설계 승인 대기
 
## 🎯 Architectural Goal
 
- **설계 목적**: Windows 11 환경 전용 **Terminal Parsing Guard (TPG)** 지침을 `AI_GUIDELINES.md`에 이식하여 터미널 구문 오해석, 네이티브 CLI 간섭, 그리고 경로 식별 실패로 인한 에이전트 불안정성을 원천 차단함.
- **SSOT 정렬**: `docs/CRITICAL_LOGIC.md`의 파싱 프로토콜과 정렬하며, `AI_GUIDELINES.md`를 터미널 상호작용의 최상위 기술 규범으로 확립함.
 
## 🛠️ Step-by-Step Execution Plan
 
### 📦 Task List
 
- [x] **Task 1: AI_GUIDELINES.md 정밀 분석**
  - **Tool**: `view_file`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: TPG 지침이 삽입될 최적의 위치(Section 2, 5, 8 등)를 라인 단위로 식별.
  - **Dependency**: None
 
- [x] **Task 2: Section 2 (Terminal & Runtime) 강화 - 구문 해석 보호**
  - **Tool**: `replace_file_content`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: **Shell Syntax Guard** (특수문자 따옴표 강제) 및 **PowerShell Session Hygiene** 강화.
  - **Pseudocode**:
    ```markdown
    - **Shell Syntax Guard**: 경로에 `()`, `[]`, `$`, `&` 포함 시 반드시 따옴표(`' '`) 사용.
    - **Isolation**: `powershell.exe -NoProfile` 사용 강제.
    - **Buffer**: 명령어 전 `Clear-Host` 필수 호출.
    ```
  - **Dependency**: Task 1
 
- [x] **Task 3: Section 5 (Clean Code) 강화 - 코드 무결성 및 워크플로우**
  - **Tool**: `replace_file_content`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: **Import Preservation**, **Pseudocode First**, **State Waiting** 원칙 명문화.
  - **Pseudocode**:
    ```markdown
    - **Import Preservation**: 핵심 의존성 자의적 삭제 금지.
    - **Pseudocode**: 수정 전 구조 강제 (의사코드 승인 절차).
    - **Hierarchy**: DDD 및 명확한 계층 구조 유지.
    ```
  - **Dependency**: Task 2
 
- [x] **Task 4: Section 9 (Git & Native Guard) 신규 생성 및 Section 8 보강**
  - **Tool**: `multi_replace_file_content`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: **Git & Native Command Guard** 신규 섹션 추가 및 **Path Resilience** (자가 치유) 로직 이식.
  - **Pseudocode**:
    ```markdown
    - **Native Command Guard**: `$LASTEXITCODE` 신뢰 및 NativeCommandError 무시.
    - **Path Resilience**: Test-Path 실패 시 `Get-ChildItem -Recurse` 자동 전환.
    - **Atomic Provisioning**: New-Item 시 `-Force` 필수.
    ```
  - **Dependency**: Task 3
 
- [x] **Task 5: 최종 무결성 검증 및 Memory Sync**
  - **Tool**: `run_command`
  - **Command**: `scripts/check-env.ps1`
  - **Goal**: 변경된 가이드라인이 시스템 환경과 충돌하지 않는지 검증하고 `memory.md` 최신화.
  - **Dependency**: Task 4
 
## ⚠️ 기술적 제약 및 규칙 (SSOT)
 
- **Encoding**: `UTF-8 no BOM` 고정하여 파싱 에러 방지.
- **Surgical Edits**: 기존 루프 방지 지침(Section 1)과 충돌하지 않도록 정밀하게 삽입.
- **Micro-Task**: 1 응답 1 툴 콜 원칙을 고수하여 터미널 버퍼 오버플로우 방지.
 
## ✅ Definition of Done
 
1. [x] `AI_GUIDELINES.md`에 TPG 6대 지침(Session, Integrity, Resilience, Protocol, Git Guard, Workflow)이 모두 통합됨.
2. [x] `powershell -NoProfile` 하에서 구문 오류 없이 호출 가능함.
3. [x] `docs/memory.md`에 TPG 강화 완료 사항이 기록됨.
 
---
 
### [BLUEPRINT CHECKLIST]
- [x] Task 1 (분석)
- [x] Task 2 (터미널 가드)
- [x] Task 3 (코드 무결성)
- [x] Task 4 (네이티브 가드/회복)
- [x] Task 5 (검증/동기화)

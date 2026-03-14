# 🗺️ Project Blueprint: Terminal Interaction Protocol Refinement

> 생성 일시: 2026-03-14 16:40 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **터미널 파싱 에러 제로화**: 에이전트와 터미널 간의 통신 안정성을 극대화하기 위해 인코딩, 환경 설정, 실행 전 검증 규칙을 구체화함.
- **SSOT 정렬**: `docs/CRITICAL_LOGIC.md`의 Section 8(Terminal Interaction Protocol) 및 $PROFILE 주입 로직과의 기술적 일관성 유지.
- **AI 행동 지침 강화**: `AI_GUIDELINES.md`에 파싱 에러 대응 SOP 및 컨텍스트 캐싱 원칙을 명문화하여 불필요한 I/O와 토큰 낭비 방지.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: scripts/init-terminal.ps1 고도화**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\scripts\init-terminal.ps1`
  - **Goal**: 사용자 요청에 따른 더욱 정밀한 PowerShell 세션 인코딩 및 환경 설정 반영.
  - **Pseudocode**: 
    ```powershell
    $OutputEncoding = [System.Text.Encoding]::UTF8;
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
    $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8';
    $env:TERM = 'dumb'; $env:NO_COLOR = '1';
    ```
  - **Dependency**: None

- [x] **Task 2: AI_GUIDELINES.md 행동 지침 업데이트**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 실행 전 검증(Pre-flight), 컨텍스트 캐싱, 파싱 에러 SOP 항목 추가.
  - **Pseudocode**:
    - Section 3에 `Safe Execution` 및 `Pre-flight Check` 관련 항목 추가.
    - Section 5(작업 기록) 전후에 `Terminal Error SOP` 및 `Context Caching` 원칙 추가.
  - **Dependency**: Task 1

- [x] **Task 3: docs/CRITICAL_LOGIC.md SSOT 반영**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\docs\CRITICAL_LOGIC.md`
  - **Goal**: Section 8의 프로토콜 항목을 고도화된 내용으로 동기화.
  - **Dependency**: Task 2

- [x] **Task 4: scripts/check-env.ps1 검증 로직 강화**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\scripts\check-env.ps1`
  - **Goal**: .bat 파일의 ANSI 인코딩 여부 및 소스 코드의 UTF-8 no BOM 검사 규칙 정밀화.
  - **Dependency**: Task 3

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: `.bat` 파일은 반드시 ANSI(CP949) 유지, 그 외는 UTF-8 no BOM.
- **Path**: Slash(/) 사용 권장 또는 `Join-Path` 사용.
- **Idempotency**: `init-terminal.ps1`은 여러 번 호출되어도 부작용이 없어야 함.

## ✅ Definition of Done

1. [x] `init-terminal.ps1`이 사용자 제시 사양을 완벽히 포함함.
2. [x] `AI_GUIDELINES.md`에 새로운 행동 지침(Pre-flight, Caching, SOP)이 명문화됨.
3. [x] `check-env.ps1`이 강화된 인코딩 규칙을 성공적으로 검증함.
4. [x] `memory.md`에 최종 작업 내용이 기록됨.

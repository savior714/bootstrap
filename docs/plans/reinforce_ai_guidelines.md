# 🗺️ Project Blueprint: AI_GUIDELINES.md 강화 및 보완 (TPG 통합)

> 생성 일시: 2024-03-21 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **TPG(Terminal Parsing Guard)** 가이드를 `AI_GUIDELINES.md`에 통합하여 터미널 상호작용의 안정성 극대화.
- **SQL 멱등성(Idempotency)** 및 마이그레이션 가드를 추가하여 데이터베이스 안전성 확보.
- 기존 섹션들을 최신 시니어 아키텍트 지침에 맞춰 보완 및 강화.
- **SSOT**: `AI_GUIDELINES.md` (글로벌 룰의 원천)

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: AI_GUIDELINES.md 섹션 2(터미널) 및 8(복구) 강화**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 세션 정제(Hygiene) 지침 강화 및 Path Resilience(자가 치유) 로직 구체화.
  - **Pseudocode**: 
    ```markdown
    - Isolation: powershell.exe -NoProfile 강제
    - Path Resilience: Test-Path 실패 시 Get-ChildItem -Recurse 자가 치유 시도
    ```
  - **Dependency**: None

- [x] **Task 2: 섹션 5(클린 코드) 및 섹션 9(Git) 보완**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 코드 무결성(TS Hygiene, Self-Verification) 및 Git Exit Code 검증 강화.
  - **Pseudocode**:
    ```markdown
    - TS Hygiene: Catch 블록 미사용 변수 제거 준수
    - Multi-Pathspec Validation: git add 전 경로 존재 확인
    ```
  - **Dependency**: Task 1

- [x] **Task 3: 섹션 10(Idempotent SQL) 및 섹션 11(Error Response) 신설**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: SQL 멱등성 가드(DO 블록, IF NOT EXISTS) 및 에러 대응 프로토콜 명시.
  - **Pseudocode**:
    ```markdown
    ## 10. SQL 멱등성 가드 (Idempotent SQL)
    - DO $$BEGIN ... END$$; 블록 활용
    ## 11. 에러 대응 프로토콜
    - Root Cause Analysis 수행 및 검증 커맨드 포함
    ```
  - **Dependency**: Task 2

- [x] **Task 4: 최종 검토 및 memory.md 동기화**
  - **Tool**: `Edit`
  - **Target**: `docs/memory.md`
  - **Goal**: 변경 사항 기록 및 세션 이관 준비.
  - **Dependency**: Task 3

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: UTF-8 no BOM 고정.
- **Bold Keywords**: 모든 핵심 키워드는 **굵게** 표시.
- **Korean Language**: 모든 설명은 한국어 사용.

## ✅ Definition of Done

1. [x] TPG 가이드의 모든 항목이 `AI_GUIDELINES.md`에 유기적으로 통합됨.
2. [x] SQL 멱등성 가드 섹션이 추가되어 DB 작업의 안전성 보장.
3. [x] `AI_GUIDELINES.md` 파일이 300라인을 초과하지 않음 (현재 196라인).
4. [x] `memory.md`에 활동 내역이 요약 기록됨.

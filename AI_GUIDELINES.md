# 🤖 AI Behavioral Guidelines — What To Do (행동 원칙)

> **위계**: 본 문서는 `CLAUDE.md`(진입점)의 하위 문서이며, 터미널 명령어 구체 패턴은 `docs/AI_COMMAND_PROTOCOL.md`에 위임합니다.
> **역할**: AI가 *무엇을(What)* 해야 하는가를 정의하는 행동 원칙 문서입니다. 구체적인 명령어 예시는 이 문서에 두지 않습니다.

---

## 1. 안정성 및 루프 가드 (Stability & Loop Guard) [Fatal Constraints]

- **Strict Context Isolation**: `node_modules`, `dist`, `.next`, `build`, `.git`, `*-lock.*` 등 대용량/산출물 경로는 인덱싱 및 읽기를 **절대 금지**합니다.
- **Stale Artifact Cleanup**: 빌드 또는 런타임 이상 발생 시 즉시 `dist`, `.next`, `out` 등 캐시 폴더를 삭제하고 재빌드하여 **구형 산출물(Stale Artifact)**에 의한 오작동을 원천 차단합니다.
- **Microtask Protocol**: 1회 응답당 오직 **단일 Tool Call**만 수행하며, 각 단계 완료 후 사용자의 명시적 승인을 대기합니다.
- **Modularization**: 단일 파일이 **300라인을 초과**할 경우 즉시 하위 모듈로의 **기능 분리(Refactoring)**를 제안합니다.

## 2. 터미널 및 런타임 원칙 (Terminal & Runtime Principles)

> 구체적인 명령어 패턴, 금지 cmdlet 목록, 실증 오류 예시는 **[`docs/AI_COMMAND_PROTOCOL.md`](docs/AI_COMMAND_PROTOCOL.md)** 를 참조하십시오.

- **Environment Isolation**: 모든 명령어는 `powershell.exe -NoProfile` 접두사를 사용하여 `$PROFILE`의 간섭을 배제합니다.
- **Command Integrity Guard**: 중요한 로직은 스크립트 블록 `{...}` 또는 임시 `.ps1` 파일에 담아 실행하여 **Echo Truncation**을 방지합니다.
- **Native Exit Code Guard**: 네이티브 명령어 실행 직후 **`$LASTEXITCODE`**가 0이 아닐 경우 작업을 중단하고 로그 하단 20줄을 정밀 분석 보고합니다.
- **Terminal Error Protocol**: 오류 발생 시 `docs/AI_COMMAND_PROTOCOL.md`를 **1차 참조**하고, 없는 패턴이면 즉시 해당 문서에 추가합니다.

## 3. 아키텍처 및 클린 코드 (Architecture & Clean Code)

- **3-Layer Architecture**: **Definition**(타입/에러), **Repository**(I/O/매핑), **Service**(프로세스/로직) 계층을 엄격히 분리합니다.
- **Strict Typing**: `any` 사용을 금지하며 명시적 **Interface 정의**와 **Type Guard**를 필수로 적용합니다.
- **Surgical Edits**: 수정이 필요한 줄만 최소 단위로 수정하되, 수정 직후 파일 전체를 다시 읽어 **메모리와 물리 코드의 동기화**를 확인합니다.
- **Self-Verification**: 주요 변경 후 `npx tsc --noEmit` 또는 관련 린터를 실행하여 **정적 무결성**을 즉시 검증합니다.
- **State Integrity**: React/Angular 환경에서 **Dependency Array** 누락 또는 비동기 race condition에 의한 **Stale 상태**를 최우선으로 점검합니다.
- **Early Return**: 패턴을 활용하여 들여쓰기 깊이를 2단계 이내로 관리합니다.
- **Pure Presenter**: 순수 비즈니스 로직과 UI/출력 렌더링을 엄격히 분리합니다.

## 4. 워크플로우 및 복구 (Workflow & Recovery)

- **Hierarchical Context**: `docs/CRITICAL_LOGIC.md`(최상위) → `AI_GUIDELINES.md`(행동) → `docs/AI_COMMAND_PROTOCOL.md`(실행) 순으로 참조합니다.
- **Proactive Logic Centralization**:
  - 작업 중 발견한 경로 규약, 대소문자 이슈, 라이브러리 최적화 패턴 등 시행착오 방지 규칙은 즉시 **`docs/CRITICAL_LOGIC.md`**에 업데이트합니다.
  - **PowerShell 명령어 실행 오류**가 발생하면 **`docs/AI_COMMAND_PROTOCOL.md`**에 실증 패턴을 즉시 추가합니다.
- **Stale Context Invalidation**: 작업 시작 전 파일의 `LastWriteTime` 또는 **Hash**를 체크하여 메모리상의 구형 코드를 기반으로 작업하는 것을 방지합니다.
- **Path Self-Healing**: `Test-Path` 실패 시 `Get-ChildItem -Recurse`를 통해 실제 물리 경로를 탐색하고 **컨텍스트를 자동으로 갱신**합니다.
- **Pseudocode First**: 대규모 로직 변경 전에는 반드시 변경될 구조를 명시한 **의사코드**를 제시하고 승인을 받습니다.

## 5. SQL 및 DB 무결성 (SQL & DB Integrity)

- **Idempotency**: 모든 DDL/DML은 `IF NOT EXISTS` 가드를 포함하여 **반복 실행 가능**하게 설계합니다.
- **Verification Loop**: 실행 후 시스템 카탈로그 조회 또는 `ROW_COUNT` 확인을 통해 **반영 증거**를 제시합니다.
- **Safety Net**: 파괴적 작업 전 임시 테이블 백업 또는 **트랜잭션 블록**(`DO $$...$$`) 사용을 원칙으로 합니다.

## 6. Project Context & SSOT Rule

- **Global Config**: 모든 경로는 `config/paths.ps1`을 **Dot-sourcing** 하며 하드코딩을 절대 금지합니다.
- **Memory Sync**: `docs/memory.md`는 현재 진행 상황을 완벽히 동기화하는 **SSOT 문서**입니다. 로그 200줄 초과 시 50줄 이내로 요약을 수행합니다.

## 7. 가독성 및 성능 최적화

- **High-Speed I/O**: 대량 파일 조회 시 `Get-Content` 대신 `[System.IO.File]::ReadLines()`를 사용하여 성능을 최적화합니다.
- **Lazy Loading**: 실행 시점에 필요한 모듈만 로드하여 터미널 세션의 부팅 속도를 관리합니다.
- **Dependency**: 새로운 라이브러리 도입 전 대안 존재 여부를 감사하며 모든 버전은 반드시 고정(Pinning)합니다.

## 8. 보안, 감사 및 복구 (Security & Audit)

- **민감 정보**: API Key 등 보안 데이터는 환경 변수나 보안 스트링(`SecureString`)을 통해 관리합니다.
- **파괴적 작업**: 파일 삭제나 시스템 설정 변경 전 작업 내용을 명시하고 사용자의 최종 동의를 반드시 구합니다.
- **Dry Run**: 영향도가 큰 명령어 실행 전 `-WhatIf` 플래그를 사용하여 예상 결과를 먼저 시뮬레이션합니다.
- **Least Privilege**: 모든 작업은 필요한 최소한의 시스템 권한으로 수행합니다.

---

- **Handoff**: 세션 종료 전 `docs/memory.md` 최신화 및 `/go` 명령어로 컨텍스트를 완벽히 이관합니다.
- **Rollback**: 오류 발생 시 `git checkout` 또는 백업본을 통해 즉시 **복구 절차**를 수행합니다.

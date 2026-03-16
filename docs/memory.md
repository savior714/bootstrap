# memory.md — Bootstrap DevEnv 작업 로그

---

## [누적 요약] 2026-03-10 ~ 2026-03-15

| 날짜 | 주요 작업 |
| --- | --- |
| 2026-03-10 | PS5 BOM 파싱 오류 해결, 창 종료 원인 README 명시 |
| 2026-03-11 | 그룹 번호 재정렬(1~8), `Add-ToUserPath` 추가, Java/Android PATH 자동 등록 |
| 2026-03-14 | `check-env.ps1` 8단계 Integrity Engine 구축, `OrderedDictionary` 버그 수정 |
| 2026-03-14 | Config 외부화: `config/paths.ps1`, `config/packages.json`, `.env.example` 신규 생성 |
| 2026-03-14 | `AI_GUIDELINES.md` 마스터 가이드라인 승격, CLAUDE.md 상속 구조 도입 |
| 2026-03-14 | Supabase CLI 자동 설치 제거 → npm 수동 설치 가이드로 대체 |
| 2026-03-14 | `Bootstrap-DevEnv.ps1` Git Identity 대화형 설정 로직 추가 |
| 2026-03-15 | Terminal Protocol 정밀화: NoProfile, 체이닝 금지, TERMINAL_RECOVERY_MARKER, Self-Verification |
| 2026-03-15 | Safe Raw IO 수칙 추가(`Test-Path` + Null 인덱싱 방지), PS Boolean 오용 사례 명문화 |
| 2026-03-15 | `CRITICAL_LOGIC.md` Terminal Protocol 및 Coding Rules SSOT 반영 후 Git Push |

**안정 상태**: `AI_GUIDELINES.md` 82줄 / `CRITICAL_LOGIC.md` 최신화 / `Bootstrap-DevEnv.ps1` ~350줄

---

## [2026-03-16] AI_GUIDELINES.md — Terminal Protocol Architect Version 통합 (강화) 및 무결성 검증

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | "Architect Version" 프로토콜의 Echo Truncation 대응, Batch ANSI 규정, Rollback First 원칙 반영 (123줄) |
| `docs/plans/reinforce_ai_guidelines.md` | 블루프린트 생성 및 Task 1~4 전체 실행 완료 |
| `templates/AI_GUIDELINES.md` | 루트의 강화된 가이드라인과 동기화 (Hash Sync PASS) |
| `scripts/lib/env-core.ps1` | `Test-GitConfigSetting` 함수에서 `ExpectedValue` 누락 시 오탐(False Positive) 발생하는 버그 수정 |

### 주요 강화 항목

- **Section 2**: `-NoProfile` 강제화, $env:TERM='dumb', $env:NO_COLOR='1', Echo Truncation 대응(Clear-Host), 명령어 체이닝 금지 가이드 강화.
- **Section 3**: Batch 파일(.bat, .cmd) **ANSI(CP949)** 인코딩 규정 명시.
- **Section 5**: Catch Block Hygiene(TS6133 방지), 자가 검증 Workflow(`tsc --noEmit`), **Rollback First** 전략 명문화.
- **Section 8**: 터미널 스트림 파싱 에러 긴급 복구 SOP (4단계) 및 Pre-flight Validation 고도화.
- **Integrity**: `check-env.ps1` 실행을 통해 전역 환경 무결성 최종 검증 완료 (100% Pass).

### 진행 상황

- [x] Task 1~4: AI_GUIDELINES.md 신규 프로토콜 규칙 완전 통합 (Type Guarding, Pure Presenter, PS Professional Scripting)
- [x] 가이드라인 템플릿 동기화 및 Hash 무결성 검증 완료
- [x] `scripts/check-env.ps1` 실행 결과 모든 항목 통과 (Git Config, Encoding, Guidelines 등)
- [x] 최종 검증 완료 (약 150 lines)

---

## [2026-03-16] Antigravity 확장 프로그램 루프 방지 지침(Loop Prevention) 통합

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | **Antigravity Loop Prevention** 섹션 추가 및 `Reload Window` 지침 확인 완료 |
| `.antigravityrules` | `node_modules`, `.git` 등 대용량 경로 제외 설정 보완 완료 |
| `docs/plans/enhance_ai_guidelines.md` | Task 2, Task 3 실행 및 체크 완료 |

### 주요 반영 사항

- **Section 1. Stability & Reliability**: 
  - 확장 프로그램의 **PERMISSIONS** 카운트 급증 및 팝업 깜빡임 현상(Loop) 식별 가이드 추가.
  - `.antigravityrules`를 통한 물리적 스캔 범위 제한 수립.
  - 루프 발생 시 **`Reload Window`**를 통한 세션 초기화 대응 절차 명문화.

### 진행 상황

- [x] Task 1: `AI_GUIDELINES.md` 내 루프 방지 수칙 통합 완료.
- [x] Task 2: `.antigravityrules` 보완 및 설정 완료.
- [x] Task 3: 환경 검증 및 세션 초기화 지침 확인 완료.
- [x] Definition of Done: 모든 항목 충족 확인.
75: - [x] Definition of Done: 모든 항목 충족 확인.
76: 
77: ---
78: 
79: ## [2026-03-16] Antigravity Rules 최적화 및 SSOT(AI_GUIDELINES.md) 정합성 확보
80: 
81: ### 작업 내용
82: 
83: | 파일 | 변경 내용 |
84: | --- | --- |
85: | `.antigravityrules` | 중복된 설명을 제거하고 런타임 제약과 물리적 차단 경로만 남김. 상세 규칙은 `AI_GUIDELINES.md`를 참조하도록 포인터 방식 도입. |
86: | `docs/plans/optimize_antigravity_rules.md` | Task 1 실행 및 체크 완료 |
87: 
88: ### 주요 반영 사항
89: 
90: - **DRY Principle**: `.antigravityrules` 내 행동 지침을 제거하여 `AI_GUIDELINES.md`와의 중복 관리 비용 최소화.
91: - **물리적 차단**: `node_modules`, `.git`, `dist` 등 Silent Loop의 핵심 원인인 경로들에 대한 물리적 차단은 유지.
92: - **포인터 방식**: 에이전트가 상세 규칙 확인을 위해 `AI_GUIDELINES.md`를 주 문서로 인식하도록 유도.
93: 
94: ### 진행 상황
95: 
96: - [x] Task 1: .antigravityrules 재작성 (Optimization) 완료.
97: - [x] Task 2: AI_GUIDELINES.md 내 .antigravityrules 역할 명시 완료.
98: - [x] Task 3: 변경 사항 검증 및 memory.md 동기화 완료.
99: - [x] SSOT Alignment: CRITICAL_LOGIC.md 내 .antigravityrules 위계 명시 완료.

---

## [2026-03-16] Terminal Parsing Guard (TPG) Reinforcement — 전역 통합 및 최종 무결성 검증 완료

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | **TPG Protocol** 강화, **코드 무결성 워크플로우** 보강 및 **Git & Native Command Guard** 신규 섹션(Section 9) 추가 완료. |
| `templates/AI_GUIDELINES.md` | 강화된 `AI_GUIDELINES.md`와 템플릿 동기화 완료 (Hash Sync PASS). |
| `docs/plans/reinforce_tpg_guidelines.md` | Task 1~5 전체 태스크 성공적으로 완료 및 종료. |

### 주요 반영 사항

- **TPG Protocol & Shell Syntax Guard**: `powershell.exe -NoProfile` 강제, 명시적 `Clear-Host` 호출, 특수 문자 작음따옴표(`' '`) 가두기 원칙 수립.
- **Workflow & Integrity**:
  - **Pseudocode First**: 로직 수정 전 설계 승인 단계 강제.
  - **State Waiting**: 파괴적 작업 전 사용자의 명시적 승인 대기.
  - **Path Resilience**: `Test-Path` 실패 시 `Get-ChildItem -Recurse` 자동 전환 및 `-LiteralPath` 사용 강조.
- **Native Command Guard**: `$LASTEXITCODE` 기반의 실행 결과 신뢰 및 `NativeCommandError` 예외 처리 로직 명문화.
- **Integrity Verification**: `scripts/check-env.ps1` 실행을 통해 전역 환경 무결성 최종 검증 완료 (Guidelines Hash Sync 포함하여 100% Pass).

### 진행 상황

- [x] Task 1: AI_GUIDELINES.md 삽입 위치 정밀 분석 완료.
- [x] Task 2: Section 2 터미널 가드 규칙 강화 완료.
- [x] Task 3: Section 5 코드 무결성 및 워크플로우 보강 완료.
- [x] Task 4: Section 9 Git & Native Command Guard 섹션 신설 및 Path Resilience 로직 이식 완료.
- [x] Task 5: 전체 시스템 무결성 검증 및 `memory.md` 최종 동기화 완료.
- [x] **Definition of Done**: TPG 6대 핵심 지침 통합 및 환경 검증 통과 완료.

---

## [2026-03-16] AI_GUIDELINES.md 가이드라인 최종 강화 및 TPG 통합 완료

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | TPG 프로토콜 고도화, SQL 멱등성 가드 및 에러 대응 프로토콜 통합 (196줄) |
| `docs/plans/reinforce_ai_guidelines.md` | Task 1~4 전체 태스크 성공적으로 완료 및 종료. |
| `docs/memory.md` | 작업 로그 정밀화 및 세션 이관 준비 완료 |

### 주요 반영 사항

- **TPG & Terminal Hygiene**: `powershell.exe -NoProfile` 강제화 및 `Clear-Host`를 통한 Echo Truncation 방지, 터미널 노이즈 대응 SOP 정밀화.
- **Path Resilience (자가 치유)**: `Test-Path` 실패 시 `Get-ChildItem -Recurse`를 통한 물리적 경로 자동 재탐색 로직 명문화.
- **Code & Git Integrity**: Catch Block Hygiene(TS6133 방지), `git add` 전 `Multi-Pathspec Validation`, `$LASTEXITCODE` 기반 네이티브 명령 판단.
- **DB & Error Guard**: SQL 멱등성(`DO` 블록, `IF NOT EXISTS`), Standardized RCA (현상-원인-해결), 에러 응답 표준 스키마 정의 및 검증 커맨드 의무화.

### 진행 상황

- [x] Task 1: 섹션 2(터미널) 및 8(복구) 강화 완료.
- [x] Task 2: 섹션 5(클린 코드) 및 섹션 9(Git) 보완 완료.
- [x] Task 3: 섹션 10(SQL) 및 섹션 11(에러 대응) 신설 완료.
- [x] Task 4: 최종 검토 및 `memory.md` 동기화 완료.
- [x] **Definition of Done**: 전역 가이드라인 강화 및 무결성 확보 PASS.


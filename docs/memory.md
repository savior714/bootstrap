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
